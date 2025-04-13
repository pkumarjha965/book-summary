from fastapi import Depends, HTTPException, status
import uuid
from datetime import timedelta, datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from psycopg2 import connect
from pydantic import BaseModel
from pydantic.v1 import Field

import datahandler

app = FastAPI()

SECRET_KEY = "a6b7409de6b74a2e8127aa529d90ae8f9f2e7cfb7fc08fbc6e3c83be1d3b59a5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = datahandler.get_user_from_db(username)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user


# Create JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = datahandler.get_user_from_db(username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/token")
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["name"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Login route to get Token
@app.post("/login")
async def login(username: str, password: str):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["name"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


class User(BaseModel):
    id: Optional[uuid.UUID] = uuid.uuid4()
    name: str = Field(..., example="John Doe")
    password: str = Field(..., example="secret")


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


@app.get("/user/{user_name}", summary="Get user by name", tags=["user"])
def getUser(user_name: str):
    user = datahandler.getUser(user_name)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user[0], name=user[1])


@app.post("/user", summary="Create user", tags=["user"])
def createUser(user: User):
    try:
        existing_user = datahandler.get_user_from_db(user.name)
        if existing_user is not None:
            raise HTTPException(status_code=400, detail="User already exists")

        user.password = pwd_context.hash(user.password)
        userRes = datahandler.createUser(user)
        return responseModel(id=userRes["id"], message="User created successfully", status=True)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="User creation failed")


@app.on_event("startup")
def init_db():
    print("init db")
    datahandler.init_db()


@app.post("/book", summary="Create book", tags=["book"])
def createBook(book: Book, current_user: dict = Depends(get_current_user)):

    try:
        book_res = datahandler.createBook(book)
        print("Book added by " + str(current_user.get("name")) + " with id " + str(book_res["id"]))
        return book_res
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Book creation failed")


@app.put("/book", summary="Update book", tags=["book"])
def updateBook(book: Book):
    bookRes = datahandler.updateBook(book)
    return bookRes


@app.delete("/book/{book_id}", summary="Delete book", tags=["book"])
def deleteBook(book_id: uuid.UUID):
    id = datahandler.deleteBook(book_id)
    return responseModel(id=id, message="Book deleted successfully", status=True)


@app.get("/book/{book_id}", response_model=Book, summary="Get book by Id", tags=["book"])
def getBook(book_id: uuid.UUID):
    book = datahandler.getBook(book_id)
    # convert to Book model
    book = Book(id=book[0], title=book[1], author=book[2], genre=book[3], year_published=book[4], summary=book[5])
    return book


@app.get("/book/{book_id}/review", summary="Get review by book Id", tags=["book"])
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


@app.get("/book/{book_id}/summary", summary="Get book summary", tags=["book"])
def getBookSummary(book_id: uuid.UUID):
    summary = datahandler.getBookSummary(book_id)
    return summary


@app.post("/book/{id}/review", summary="Add review to a book", tags=["book"])
def createReview(book_id: uuid.UUID, review: Review, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    review_res = datahandler.createReview(book_id, review, user_id)
    return responseModel(id=review_res["id"], message="Review created successfully", status=True)


@app.get("/book/{book_id}/review/summary", summary="Get review  summary by book Id", tags=["book"])
def getReviewSummary(book_id: uuid.UUID):
    reviews = datahandler.getReviews(book_id)
    summary = datahandler.summarizeReviews(reviews)
    return summary
