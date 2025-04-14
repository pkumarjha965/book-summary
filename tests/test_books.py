import pytest
from fastapi.testclient import TestClient
from main import app, create_access_token
from datetime import timedelta
from unittest.mock import patch

client = TestClient(app)


def get_mock_user(username):
    return {"name": username, "password": "$2b$12$KIXQ9z1eWz5F5F5F5F5F5u"}


@patch("service.datahandler.get_user_from_db", side_effect=get_mock_user)
def login_returns_token_for_valid_credentials(mock_get_user):
    response = client.post("/token", data={"username": "valid_user", "password": "valid_password"})
    assert response.status_code == 200
    assert "access_token" in response.json()


@patch("service.datahandler.get_user_from_db", return_value=None)
def login_returns_401_for_invalid_user(mock_get_user):
    response = client.post("/token", data={"username": "invalid_user", "password": "valid_password"})
    assert response.status_code == 401


@patch("service.datahandler.get_user_from_db", side_effect=get_mock_user)
@patch("main.pwd_context.verify", return_value=False)
def login_returns_401_for_invalid_password(mock_verify, mock_get_user):
    response = client.post("/token", data={"username": "valid_user", "password": "invalid_password"})
    assert response.status_code == 401


@patch("service.datahandler.get_user_from_db", side_effect=get_mock_user)
def get_current_user_returns_user_for_valid_token(mock_get_user):
    token = create_access_token(data={"sub": "valid_user"}, expires_delta=timedelta(minutes=30))
    response = client.get("/user/valid_user", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "valid_user"


@patch("service.datahandler.get_user_from_db", return_value=None)
def get_current_user_returns_401_for_invalid_token(mock_get_user):
    response = client.get("/user/valid_user", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


@patch("service.datahandler.getBooks", return_value=[{"id": "1", "title": "Book 1"}, {"id": "2", "title": "Book 2"}])
def get_books_returns_list_of_books(mock_get_books):
    response = client.get("/book")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["title"] == "Book 1"


@patch("service.datahandler.getBooks", side_effect=Exception("Database error"))
def get_books_returns_500_on_exception(mock_get_books):
    response = client.get("/book")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch books"


@patch("service.datahandler.getBook", return_value=("1", "Book 1", "Author 1", "Fiction", 2020, "Summary 1"))
def get_book_by_id_returns_book_details(mock_get_book):
    response = client.get("/book/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Book 1"


@patch("service.datahandler.getBook", return_value=None)
def get_book_by_id_returns_404_if_book_not_found(mock_get_book):
    response = client.get("/book/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"


@patch("service.datahandler.createBook", return_value={"id": "1"})
def create_book_returns_successful_response(mock_create_book):
    response = client.post("/book",
                           json={"title": "New Book", "author": "Author", "genre": "Fiction", "year_published": 2023,
                                 "summary": "Summary"})
    assert response.status_code == 200
    assert response.json()["id"] == "1"


@patch("service.datahandler.createBook", side_effect=Exception("Database error"))
def create_book_returns_500_on_exception(mock_create_book):
    response = client.post("/book",
                           json={"title": "New Book", "author": "Author", "genre": "Fiction", "year_published": 2023,
                                 "summary": "Summary"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Book creation failed"


