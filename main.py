import uuid
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic.v1 import Field

import datahandler

app = FastAPI()


class User(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    name: str = Field(..., example="John Doe")


class responseModel(BaseModel):
    id: uuid.UUID = uuid.uuid4()
    message: str = Field(..., example="User created successfully")
    status: bool = Field(..., example=True)


class Book(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    title: str = Field(..., example="The Alchemist")
    author: str = Field(..., example="Paulo Coelho")
    genre: str = Field(..., example="Adventure")
    year_published: int = Field(..., example=1988)
    summary: Optional[str] = Field(default="", example="summary of the book")


class Review(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    book_id: uuid.UUID
    user_id: uuid.UUID
    review: str = Field(..., example="This book is amazing")
    rating: float = Field(..., example=4.5)


@app.get("/user/{user_id}")
def getUser(user_id: uuid.UUID):
    user = datahandler.getUser(user_id)
    return user


@app.post("/user")
def createUser(user: User):
    userRes = datahandler.createUser(user)
    return userRes


@app.on_event("startup")
def init_db():
    print("init db")
    # datahandler.init_db()


@app.post("/book")
def createBook(book: Book):
    bookRes = datahandler.createBook(book)
    return bookRes


@app.put("/book")
def updateBook(book: Book):
    bookRes = datahandler.updateBook(book)
    return bookRes


@app.delete("/book/{book_id}")
def deleteBook(book_id: uuid.UUID):
    book = datahandler.deleteBook(book_id)
    return responseModel(book.id, "Book deleted successfully", True)


@app.get("/book/{book_id}", response_model=Book, tags=["book"])
def getBook(book_id: uuid.UUID):
    book = datahandler.getBook(book_id)
    # convert to Book model
    book = Book(id=book[0], title=book[1], author=book[2], genre=book[3], year_published=book[4], summary=book[5])
    return book

@app.get("/book/{book_id}/review")
def getReview(book_id: uuid.UUID):
    reviews = datahandler.getReviews(book_id)
    # convert to Review model
    reviewModels = []
    review = reviews[0]
    review_model = Review(id=review[0], book_id=review[1], user_id=review[2], review=review[3], rating=review[4])
    for review in reviews:
        reviewModels.append(
            Review(id=review[0], book_id=review[1], user_id=review[2], review=review[3], rating=review[4]))
    print(reviewModels)
    return reviewModels

@app.post("/book/{id}/review")
def createReview(id:uuid.UUID, review: Review):
    reviewRes = datahandler.createReview(review)
    return responseModel(reviewRes.id, "Review created successfully", True)


@app.get("/book/{book_id}/summary")
def getBookSummary(book_id: uuid.UUID):
    summary = datahandler.getBookSummary(book_id)
    return summary