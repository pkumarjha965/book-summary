import uuid
from typing import Optional

from pydantic import BaseModel
from pydantic.v1 import Field


class UserResponse(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    name: str = Field(..., example="John Doe")


class responseModel(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
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
    review: str = Field(..., example="This book is amazing")
    rating: float = Field(..., example=4.5)


class User(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    name: str = Field(..., example="John Doe")
    password: str = Field(..., example="secret")
