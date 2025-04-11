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

class Book(BaseModel):
    id : Optional[uuid.UUID] = uuid.uuid4()
    title: str = Field(..., example="The Alchemist")
    author: str = Field(..., example="Paulo Coelho")
    genre: str = Field(..., example="Adventure")
    year_published: int = Field(..., example=1988)
    summary: Optional[str] = Field(default="",example="summary of the book")

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
