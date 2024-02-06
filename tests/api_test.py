import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
import logging
import os

from database.database import get_session
from exporter import DATABASE_URL
from main import app

logger = logging.getLogger('test')


@pytest.fixture(name="session")
def session_fixture():
    test_engine = create_engine(DATABASE_URL+"test_bookshop", echo=True)
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_ping(client):
    response = client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"data": "ping", "status": True, "message": "ping"}


def test_success_cases(client):
    # POST /author
    author_data = [
        {"name": "test author", "birth_date": "1963-11-10"},
        {"name": "test author 2", "birth_date": "1973-11-10"}
    ]

    author_ids = []
    for data in author_data:
        response = client.post("/author", json=data)
        assert response.status_code == 201
        author_id = response.json()["data"]["id"]
        assert isinstance(author_id, int)
        author_ids.append(author_id)

    # GET /author/{author_id}
    get_author_response = client.get(f"/author/{author_ids[0]}")
    assert get_author_response.status_code == 200
    assert get_author_response.json()["data"] == {
        "name": "test author",
        "birth_date": "1963-11-10",
        "id": author_ids[0]
    }

    # POST /book
    book_data = [
        {"barcode": "1111238", "title": "test book", "publish_year": 1990, "author": author_ids[0]},
        {"barcode": "1111234", "title": "test book2", "publish_year": 1991, "author": author_ids[0]},
        {"barcode": "11245", "title": "test book3", "publish_year": 1992, "author": author_ids[0]},
        {"barcode": "15110", "title": "test book4", "publish_year": 1995, "author": author_ids[1]},
        {"barcode": "15002", "title": "test book5", "publish_year": 1997, "author": author_ids[1]},
        {"barcode": "14810", "title": "test book6", "publish_year": 2000, "author": author_ids[1]}
    ]

    book_ids = []
    for data in book_data:
        response = client.post("/book", json=data)
        assert response.status_code == 201
        book_id = response.json()["data"]["id"]
        assert isinstance(book_id, int)
        book_ids.append(book_id)

    # GET /book/{book_id}
    get_book_response = client.get(f"/book/{book_ids[0]}")
    assert get_book_response.status_code == 200
    assert get_book_response.json()["data"]["barcode"] == "1111238"
    assert get_book_response.json()["data"]["quantity"] == 0

    # POST /leftover/add
    add_inventory_response = client.post("/leftover/add", json={
        "barcode": "1111238",
        "quantity": 10
    })
    assert add_inventory_response.status_code == 201
    assert add_inventory_response.json()["data"]["quantity"] == 10

    # POST /leftover/remove
    remove_inventory_response = client.post("/leftover/remove", json={
        "barcode": "1111238",
        "quantity": 3
    })
    assert remove_inventory_response.status_code == 201
    assert remove_inventory_response.json()["data"]["quantity"] == -3

    # POST /leftover/bulk
    file_paths = [os.path.abspath("../bookshop/fixtures/txt_example.txt"), os.path.abspath("../bookshop/fixtures/xls_example_correct.xlsx")]
    for file_path in file_paths:
        file_data = {'file': open(file_path, 'rb')}
        bulk_response = client.post("/leftover/bulk", files=file_data)
        assert bulk_response.status_code == 201
        assert len(bulk_response.json()["data"]) == 3

    # GET /book/{book_id}
    get_book_response = client.get(f"/book/{book_ids[0]}")
    assert get_book_response.status_code == 200
    assert get_book_response.json()["data"]["quantity"] == 5

    # GET /book?barcode=?
    get_book_response2 = client.get("/book?barcode=11112")
    assert get_book_response2.status_code == 200
    assert get_book_response2.json()["data"]["found"] == 2

    # GET /history
    get_history_response = client.get(f"/history?book={book_ids[0]}")
    assert get_history_response.status_code == 200
    assert len(get_history_response.json()["data"][0]["history"]) == 3
    assert get_history_response.json()["data"][0]["end_balance"] == 5


def test_failure_cases(client):
    # Method not allowed
    response = client.get("/author")
    assert response.status_code == 405

    # Not Found(key in request)
    response = client.get("/author/1")
    assert response.status_code == 404

    # Not Found
    response = client.get("/authorbook")
    assert response.status_code == 404

    # Validation error
    response = client.post("/author", json={"name": "test author", "birth_date": "1963/11/10"})
    assert response.status_code == 422

    # Internal Error
    file_data = {'file': open(os.path.abspath("../bookshop/fixtures/xls_example_fail.xlsx"), 'rb')}
    bulk_response = client.post("/leftover/bulk", files=file_data)
    assert bulk_response.status_code == 500

    # Bad request - if quantity not a number - error 400 (task requirement)
    response = client.post("/author", json={"name": "test author", "birth_date": "1963-11-10"},)
    author_id = response.json()["data"]["id"]
    book_data = [
        {"barcode": "1111238", "title": "test book", "publish_year": 1990, "author": author_id},
        {"barcode": "1111234", "title": "test book2", "publish_year": 1991, "author": author_id},
        {"barcode": "11245", "title": "test book3", "publish_year": 1992, "author": author_id},
    ]
    for data in book_data:
        response = client.post("/book", json=data)
    file_data = {'file': open("../bookshop/fixtures/xls_example_fail.xlsx", 'rb')}
    bulk_response = client.post("/leftover/bulk", files=file_data)
    assert bulk_response.status_code == 400
