from io import BytesIO
import json
import os

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, Depends, File, Query 
from fastapi.responses import JSONResponse

from database.database import get_session
from errors import EntityNotFoundError, ValidityError
from api.handlers import *
from models import *
from responses import Response
from utils import logger, get_barcode_quantity_datagram_from_bytes

router = APIRouter()

def post_handler(request, http_status_code, message, handler_func, database_session):
    request_data = None
    try:
        result = handler_func(database_session, request)
        if isinstance(request, (pd.core.frame.DataFrame)):
            request_data = request.to_json(orient="records")
        else:
            request_data = json.dumps(request.model_dump())
        logger.info(f"/{request.__class__.__name__.lower()} request: {request_data}")
        logger.info(f"/{request.__class__.__name__.lower()} result: {result}")
        return JSONResponse(content=Response(result, message), status_code=http_status_code)
    except ValidityError as v_error:
        raise v_error
    except Exception as e:
        logger.exception(f"Error executing handler, {e}")
        raise e


@router.get("/ping")
async def root():
    return Response("ping", "ping")


@router.post("/author")
async def add_author(request: Author, database_session: Session=Depends(get_session)):
    try:
        request.check_request_validity()
        return post_handler(request, 201, "Author created successfully", add_author_handler, database_session)
    except ValidityError as v_error:
        raise HTTPException(status_code=422, detail=str(v_error))
    except Exception as e:
        logger.exception(f"Error adding author, {e}")
        raise HTTPException(status_code=500, detail=f"Error adding author, {e}")


@router.get("/author/{author_id}")
async def get_author_by_id(author_id: str, database_session: Session=Depends(get_session)):
    try:
        result = get_author_by_id_handler(database_session, int(author_id))
        logger.info(f"author_id: {author_id}, /author result: {result}")
        return Response(result, "Author loaded successfully")
    except EntityNotFoundError as ne:
        raise HTTPException(status_code=404, detail=f"No author with {author_id}, {ne}")
    except Exception as e:
        logger.exception(f"Error fetching author with ID {author_id}, {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching author with ID {author_id}, {e}")


@router.post("/book")
async def add_book(request: Book, database_session: Session=Depends(get_session)):
    try:
        request.check_request_validity()
        return post_handler(request, 201, "Book created successfully", add_book_handler, database_session)
    except ValidityError as v_error:
        raise HTTPException(status_code=422, detail=str(v_error))
    except Exception as e:
        logger.exception(f"Error adding book, {e}")
        raise HTTPException(status_code=500, detail=f"Error adding book, {e}")


@router.get("/book/{book_id}")
async def get_book_by_id(book_id: str, database_session: Session=Depends(get_session)):
    try:
        result = get_book_by_id_handler(database_session, int(book_id))
        logger.info(f"book_id: {book_id}, /book result: {result}")
        return Response(result, "Book loaded successfully")
    except EntityNotFoundError as ne:
        raise HTTPException(status_code=404, detail=f"No book with {book_id}, {ne}")
    except Exception as e:
        logger.exception(f"Error fetching book with ID {book_id}, {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching book with ID {book_id}, {e}")


@router.get("/book")
async def get_book_by_barcode(barcode: str, database_session: Session=Depends(get_session)):
    try:
        result = get_book_by_barcode_handler(database_session, barcode)
        logger.info(f"barcode: {barcode}, /book result: {result}")
        return Response(result, "Book loaded successfully")
    except Exception as e:
        logger.exception(f"Error fetching book with barcode {barcode}, {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching book with barcode {barcode}, {e}")


@router.post("/leftover/add")
async def add_inventory(request: InventoryRequest, database_session: Session=Depends(get_session)):
    try:
        request.check_request_validity()
        return post_handler(request, 201, "Inventory created successfully", add_inventory_handler, database_session)
    except ValidityError as v_error:
        raise HTTPException(status_code=422, detail=str(v_error))
    except Exception as e:
        logger.exception(f"Error adding inventory, {e}")
        raise HTTPException(status_code=500, detail=f"Error adding inventory, {e}")


@router.post("/leftover/remove")
async def remove_inventory(request: InventoryRequest, database_session: Session=Depends(get_session)):
    try:
        request.check_request_validity()
        request.quantity = -1 * request.quantity
        return post_handler(request, 201, "Inventory created successfully", add_inventory_handler, database_session)
    except ValidityError as v_error:
        raise HTTPException(status_code=422, detail=str(v_error))
    except Exception as e:
        logger.exception(f"Error adding inventory, {e}")
        raise HTTPException(status_code=500, detail=f"Error adding inventory, {e}")


@router.post("/leftover/bulk")
async def add_inventory_bulk(file: UploadFile=File(...), database_session: Session=Depends(get_session)):
    """
    Update inventory in bulk based on the provided file.

    Args:
        file (UploadFile): The file containing inventory data.

    Returns:
        JSONResponse: A JSON response indicating the status of the inventory update.
    """
    try:
        _, file_extension = os.path.splitext(file.filename)
        contents = await file.read()
        if file_extension == ".txt":
            dataframe = get_barcode_quantity_datagram_from_bytes(contents)
        elif file_extension == ".xlsx":
            dataframe = pd.read_excel(BytesIO(contents), header=None)
        return post_handler(dataframe, 201, "Inventory created successfully", add_inventory_bulk_handler, database_session)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except EntityNotFoundError as ne:
        raise HTTPException(status_code=404, detail=f"Data conversion with missing part error, {ne}")
    except ValidityError as ve:
        # task requirement 400
        raise HTTPException(status_code=400, detail=f"Data conversion error, {ve}")
    except Exception as e:
        logger.exception(f"Error adding inventory, {e}")
        raise HTTPException(status_code=500, detail=f"Error adding inventory, {e}")


@router.get("/history")
async def get_history(start: Optional[str]=Query(None, pattern=r"\d{4}-\d{2}-\d{2}"),
                      end: Optional[str]=Query(None, pattern=r"\d{4}-\d{2}-\d{2}"),
                      book: Optional[str]=None, database_session: Session=Depends(get_session)):
    """
    Get the inventory history based on the provided start and end dates and book ID.

    Args:
        start (Optional[str]): The start date in YYYY-MM-DD format (optional).
        end (Optional[str]): The end date in YYYY-MM-DD format (optional).
        book (Optional[str]): The book ID (optional).

    Returns:
        Response: A response containing the inventory history.
    """
    try:
        if start is None:
            start = datetime.now().strftime("%Y-%m-%d")
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        request = InventoryHistoryRequest(start=start, end=end, book=book)
        request.check_request_validity()
        result = get_book_history_handler(database_session, request)
        logger.info(f"/history result: {result}")
        return Response(result, "Book inventory history loaded successfully")
    except EntityNotFoundError as ne:
        raise HTTPException(status_code=404, detail=f"No book history, {ne}")
    except ValidityError as v_error:
        raise HTTPException(status_code=422, detail=str(v_error))
    except Exception as e:
        logger.exception(f"Error fetching book inventory history, {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching book inventory history, {e}")
