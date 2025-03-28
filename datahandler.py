import json
import os
import uuid
from minio import Minio
import dotenv
import pandas as pd
from pandas import DataFrame as df
from dotenv import dotenv_values
from psycopg2 import connect

# create connections to database

# create cursor
# create table schema
# execute the connections in db
dotenv.load_dotenv()
db_config = {
    "dbname": "bms",
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres123"
}


def init_db():
    # create table if not exist

    book_table = "create table book(id UUID PRIMARY KEY,title varchar(50),author varchar(50),genre varchar(30), year_published int,summary varchar(5000))"
    user_table = "create table users(id UUID primary key, name varchar(50))"
    review_table = "create table reviews(id UUID PRIMARY KEY, book_id UUID, user_id UUID, review text, rating decimal, constraint fk_user FOREIGN KEY(user_id) references users(id) on delete cascade, constraint fk_book FOREIGN KEY(book_id) references book(id) on delete cascade )"

    conn = connect(**db_config)
    conn.cursor.execute(book_table)
    conn.cursor.execute(user_table)
    conn.cursor().execute(review_table)
    conn.commit()


def createUser(user):
    try:
        if user.id is None:
            user.id = uuid.uuid4()

        user_dict = user.dict()
        print(user_dict)
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("insert into users(id,name) values(%s,%s)", (str (user_dict["id"]), user_dict["name"]))
        conn.commit()
        return user_dict

    except Exception as e:
        print(e)
        return None


def getUser(user_id:uuid.UUID):
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select * from users where id = %s", (str(user_id),))
    user = cursor.fetchone()
    return user



def createBook(book):
    try:
        if book.id is None:
            book.id = uuid.uuid4()

        book_dict = book.dict()
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("insert into book(id,title,author,genre,year_published,summary) values(%s,%s,%s,%s,%s,%s)", (str(book_dict["id"]), book_dict["title"], book_dict["author"], book_dict["genre"], book_dict["year_published"], ""))
        updateSummary(book_dict["name"])
        conn.commit()
        return book_dict

    except Exception as e:
        print(e)
        return None
async def updateSummary(book_dict):
    # call LLM to generate summary
    book_name = book_dict['name']
    genre = book_dict['genre']
    base_url = os.getenv("storage_url")
    file_name = base_url + "/books/"+ genre+"/"+ book_name + ".pdf"
    minio_client = Minio(os.getenv("minio_url"), access_key=os.getenv("minio_access_key"), secret_key=os.getenv("minio_secret_key"), secure=False)
    file = minio_client.get_object("books/"+genre, file_name)
    content = file.read().decode('utf-8')
    return "summary of the book"
def getBook(book_id:uuid.UUID):
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select * from book where id = %s", (str(book_id),))
    book = cursor.fetchone()
    return book

def getBook():
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select * from book")
    books = cursor.fetchall()
    return books

def createReview(review):
    try:
        if review.id is None:
            review.id = uuid.uuid4()

        review_dict = review.dict()
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("insert into reviews(id,book_id,user_id,review,rating) values(%s,%s,%s,%s,%s)", (str(review_dict["id"]), str(review_dict["book_id"]), str(review_dict["user_id"]), review_dict["review"], review_dict["rating"]))
        conn.commit()
        return review_dict

    except Exception as e:
        print(e)
        return None

def getReviews(book_id:uuid.UUID):
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select review,rating from reviews where book_id = %s", (str(book_id),))
    reviews = cursor.fetchall()
    summary = summarizeReviews(reviews)
    return summary

def summarizeReviews(reviews):
    summary ={}
    df_reviews = df(reviews, columns=["review","rating"])
    reviews_list = df_reviews.get("review")
    summarized_reviews = summarize(reviews_list)
    summary['summary']= summarized_reviews

    rating_avg = df_reviews.get("rating").avg()
    summary['rating'] = rating_avg
    # summary = df_reviews.describe()
    return summary

def summarize(reviews):
    # call LLM to summarize the reviews
    return " ".join(reviews)