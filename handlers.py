from typing import Optional
from sqlmodel import Session, select, func
from sqlalchemy import text
import pandas as pd
import numpy
from models import *
from utils import logger
from errors import ValidityError, EntityNotFoundError, DatabaseOperationError


def add_item_to_database(session: Session, item) -> dict:
    try:
        """Add an item to the database"""
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    except Exception as e:
        session.rollback()
        logger.exception(f"Error adding item {item} in DB, {e}")
        raise DatabaseOperationError(f"Error adding item {item} in DB, {e}")
    finally:
        session.close()


def add_author_handler(session: Session, request: Author) -> dict:
    """Add an author to the database"""
    try:
        item = add_item_to_database(session, request)
        return {"id": item.id}
    except Exception as e:
        raise e
    finally:
        session.close()


def get_author_by_id_handler(session: Session, author_id: int) -> Optional[Author]:
    """Retrieve an author from the database by their ID."""
    try:
        result = session.exec(select(Author).where(Author.id == author_id)).first()
        if result is None:
            raise EntityNotFoundError(f"No author with ID {author_id} in DB")
        return result
    except EntityNotFoundError as ene:
        raise ene
    except Exception as e:
        logger.exception(f"Error fetching author with ID {author_id} in DB, {e}")
        raise DatabaseOperationError(f"Error fetching author with ID {author_id} in DB, {e}")
    finally:
        session.close()


def add_book_handler(session: Session, request: Book) -> dict:
    """Add a book to the database"""
    try:
        item = add_item_to_database(session, request)
        return {"id": item.id}
    except Exception as e:
        raise e
    finally:
        session.close()


def get_book_by_id_handler(session: Session, book_id: int) -> Optional[dict]:
    """Retrieve book details along with its inventory quantity by book ID."""
    try:
        statement = (
            select(
                Book.id,
                Book.title,
                Book.publish_year,
                Book.author,
                Book.barcode,
                func.sum(Inventory.quantity).label("quantity")
            )
            .join(Inventory, Book.id == Inventory.book_id, isouter=True)
            .where(Book.id == book_id)
            .group_by(Book.id)
        )
        result = session.exec(statement).first()
        if result is None:
            raise EntityNotFoundError(f"No book with ID {book_id} in DB")
        data = {
                "id": result.id,
                "title": result.title,
                "barcode": result.barcode,
                "author": result.author,
                "publish_year": result.publish_year,
                "quantity": 0
        }
        if result.quantity is not None:
            data["quantity"] = result.quantity
        return data
    except EntityNotFoundError as ene:
        raise ene
    except Exception as e:
        logger.exception(f"Error fetching book with ID {book_id} in DB, {e}")
        raise DatabaseOperationError(f"Error fetching book with ID {book_id} in DB, {e}")
    finally:
        session.close()


def get_book_by_barcode_handler(session: Session, barcode: str) -> Optional[Book]:
    """Retrieve book details based on the provided barcode."""
    try:
        statement = (
            select(
                Book.id,
                Book.title,
                Book.publish_year,
                Author.name,
                Author.birth_date,
                Book.barcode,
                func.sum(Inventory.quantity).label("quantity")
            )
            .join(Author, Book.author == Author.id)
            .join(Inventory, Book.id == Inventory.book_id, isouter=True)
            .where(Book.barcode.like(f"{barcode}%"))
            .group_by(
                Book.id,
                Book.title,
                Book.publish_year,
                Author.name,
                Author.birth_date,
                Book.barcode
            )
            .order_by(Book.barcode.asc())
        )
        results = session.exec(statement)
        data_list = []
        for result in results.all():
            data = {
                "id": result.id,
                "title": result.title,
                "barcode": result.barcode,
                "author": {
                    "name": result.name,
                    "birth_date": result.birth_date
                },
                "publish_year": result.publish_year,
                "quantity": 0
            }
            if result.quantity is not None:
                data["quantity"] = result.quantity
            data_list.append(data)
        return {
            "found": len(data_list),
            "items": data_list
        }
    except Exception as e:
        logger.exception(f"Error fetching book with bracode {barcode} in DB, {e}")
        raise DatabaseOperationError(f"Error fetching book with bracode {barcode} in DB, {e}")
    finally:
        session.close()


def add_inventory_handler(session: Session, request: InventoryRequest) -> dict:
    """Add an inventory to the database"""
    try:
        book = session.exec(select(Book).where(Book.barcode == request.barcode)).first()
        book_quantity_data = get_book_by_id_handler(session, book.id)
        if book_quantity_data["quantity"] + request.quantity < 0:
            logger.exception(f"No enough book barcode {request.barcode} inventory in DB")
            raise ValueError(f"No enough book barcode {request.barcode} inventory in DB")
        if book:
            inventory = add_item_to_database(session,
                                             Inventory(book_id=book.id,
                                                       quantity=request.quantity,
                                                       date=datetime.now().strftime("%Y-%m-%d")))
            return {"barcode": request.barcode, "quantity": inventory.quantity}
        else:
            logger.exception(f"Empty book found with {request.barcode} in DB")
            raise ValueError(f"Empty book found with {request.barcode} in DB")
    except Exception as e:
            logger.exception(f"Error adding an inventory, {e}")
            raise e
    finally:
        session.close()


def add_inventory_bulk_handler(session: Session, request: pd.core.frame.DataFrame) -> list:
    """Add inventory items in bulk based on the provided request."""
    updated_items = []
    try:
        for index, row in request.iterrows():
            barcode = row.iloc[0]
            quantity = row.iloc[1]
            if pd.isna(barcode):
                logger.info(f"Empty barcode found in row {index} for DB, skipping...")
                continue
            elif pd.isna(quantity):
                logger.exception(f"barcode {str(int(barcode))} has no quantity for DB, stopping...")
                raise EntityNotFoundError(f"barcode {str(int(barcode))} has no quantity for DB")
            elif not isinstance(quantity, (numpy.int64, numpy.float64, int)):
                logger.exception(f"barcode {str(int(barcode))} quantity is not a number {quantity} in row {index} for DB stopping...")
                raise ValidityError(f"barcode {str(int(barcode))} quantity is not a number {quantity} in row {index} for DB")
            try:
                book = session.exec(select(Book).where(Book.barcode == str(int(barcode)))).first()
                if book:
                    inventory = Inventory(book_id=book.id, quantity=int(quantity), date=datetime.now().strftime("%Y-%m-%d"))
                    session.add(inventory)
                    session.commit()
                    session.refresh(inventory)
                    updated_items.append({
                        "inventory_id": inventory.id,
                        "book_id": inventory.book_id,
                        "quantity": inventory.quantity,
                        "date": inventory.date
                    })
                else:
                    session.rollback()
                    updated_items = []
                    logger.exception(f"Empty book found with {str(int(barcode))} in DB")
                    raise ValueError(f"Empty book found with {str(int(barcode))} in DB")
            except Exception as e:
                session.rollback()
                updated_items = []
                logger.exception(f"Error adding bulk of inventory in DB, {e}")
                raise DatabaseOperationError(f"Error adding bulk of inventory in DB, {e}")
        session.commit()
    finally:
        session.close()
    return updated_items


def get_book_history_handler(session: Session, request: InventoryHistoryRequest) -> list:
    """
    Retrieves the inventory history of books based on the provided request parameters.

    Args:
    - request (InventoryHistoryRequest): An instance of InventoryHistoryRequest containing the request parameters.

    Returns:
    - list: A list of dictionaries representing the inventory history of books.

    Description:
    This function queries the database to retrieve the inventory history of books based on the provided request parameters.
    It constructs a SQL query to fetch relevant data and aggregates the results into a list of dictionaries representing the inventory history.
    The returned list contains information such as book key, title, barcode, start balance, end balance, and historical data.
    """
    query = """
    SELECT
        b.id AS book_key,
        b.title AS book_title,
        b.barcode AS book_barcode,
        COALESCE(start_balance, 0) AS start_balance,
        COALESCE(end_balance, 0) AS end_balance,
        CASE
            WHEN COUNT(i.date) = 0 THEN '[]'
            ELSE
                JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'date', i.date,
                        'quantity',
                        CASE
                            WHEN i.quantity > 0 THEN CONCAT('+', CAST(i.quantity AS text))
                            ELSE CAST(i.quantity AS text)
                        END
                    ) ORDER BY i.date DESC
                )
        END AS history
    FROM
        book b
    LEFT JOIN (
        SELECT
            book_id,
            SUM(CASE WHEN date < :start_date THEN quantity ELSE 0 END) AS start_balance,
            SUM(CASE WHEN date <= :end_date THEN quantity ELSE 0 END) AS end_balance
        FROM
            inventory
        WHERE
            date BETWEEN :start_date AND :end_date
        GROUP BY
            book_id
    ) balances ON b.id = balances.book_id
    LEFT JOIN
        inventory i ON b.id = i.book_id AND i.date BETWEEN :start_date AND :end_date
    WHERE
        (:book_id IS NULL OR b.id = :book_id)
    GROUP BY
        b.id, b.title, b.barcode, start_balance, end_balance;
                """
    books = []
    inventory_history = []
    try:
        if request.book is None:
            books = session.exec(select(Book)).all()
        else:
            book = session.exec(select(Book).where(Book.id == request.book)).first()
            if book is None:
                raise EntityNotFoundError(f"No book with ID {request.book} in DB")
            books.append(book)
        for book in books:
            parameters = {
                "start_date": request.start,
                "end_date": request.end,
                "book_id": book.id
            }
            with session.connection().engine.connect() as connection:
                result = connection.execute(text(query), parameters)
                for result in result.fetchall():
                    data = {
                        "book": {
                            "key": result.book_key,
                            "title": result.book_title,
                            "barcode": result.book_barcode
                        },
                        "start_balance": result.start_balance,
                        "end_balance": result.end_balance,
                        "history": result.history
                    }
                    inventory_history.append(data)
        return inventory_history
    except EntityNotFoundError as ene:
        raise ene
    except Exception as e:
            logger.exception(f"Error getting inventory history in DB, {e}")
            raise DatabaseOperationError(f"Error getting inventory history in DB, {e}")
    finally:
        session.close()
