import json
import os
import uuid

from fastapi import requests
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
        cursor.execute("insert into users(id,name) values(%s,%s)", (str(user_dict["id"]), user_dict["name"]))
        conn.commit()
        return user_dict

    except Exception as e:
        print(e)
        return None


def getUser(user_id: uuid.UUID):
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
        cursor.execute("insert into book(id,title,author,genre,year_published,summary) values(%s,%s,%s,%s,%s,%s)", (
            str(book_dict["id"]), book_dict["title"], book_dict["author"], book_dict["genre"],
            book_dict["year_published"],
            ""))
        conn.commit()
        conn.close()

        updateSummary(book_dict["id"], book_dict["name"])
        return book_dict

    except Exception as e:
        print(e)
        return None


async def getBookContent(book_dict):
    # call LLM to generate summary
    book_name = book_dict['name']
    genre = book_dict['genre']
    base_url = os.getenv("storage_url")
    file_name = base_url + "/books/" + genre + "/" + book_name + ".pdf"
    minio_client = Minio(os.getenv("minio_url"), access_key=os.getenv("minio_access_key"),
                         secret_key=os.getenv("minio_secret_key"), secure=False)
    file = minio_client.get_object("books/" + genre, file_name)
    content = file.read().decode('utf-8')
    return content


async def updateSummary(id, content):
    # call LLM to generate summary

    summary = await generateSummary(content)  # call LLM to generate summary
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("update book set summary = %s where id = %s", (summary, id))
    conn.commit()
    conn.close()


async def generateSummary(content):
    # call LLM to generate summary
    url = os.getenv("llm_url")
    headers = {
        "content-type": "application/json",
        "accept": "application/json"
    }

    requestObj = {
        "model": "llama3.2",
        "message": [{"role": "system",
                     "content": "You are an assistant, who reads the content of a book and generate the summary of the book."},
                    {"role": "user", "content": content}],
        "stream": False
    }

    response = requests.post(url, headers=headers, json=requestObj)

    if (response.status_code != 200):
        print("Error in generating summary")
        return None
    response = response.json()
    summary_content = response.get("message").get("content")
    return summary_content


def getBook(book_id: uuid.UUID):
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


def getBook(book_id: uuid.UUID):
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select * from book where id = %s", (str(book_id),))
    books = cursor.fetchone()
    return books

def deleteBook(book_id: uuid.UUID):
    try:
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("delete from book where id = %s", (str(book_id),))
        conn.commit()
        return book_id

    except Exception as e:
        print(e)
        return None
def updateBook(book):
    try:
        book_dict = book.dict()
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("update book set title = %s, author = %s, genre = %s, year_published = %s where id = %s",
                       (book_dict["title"], book_dict["author"], book_dict["genre"], book_dict["year_published"],
                        str(book_dict["id"])))
        conn.commit()
        return book_dict

    except Exception as e:
        print(e)
        return None


def createReview(book_id,review):
    try:
        if review.id is None:
            review.id = uuid.uuid4()

        review_dict = review.dict()
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("insert into reviews(id,book_id,user_id,review,rating) values(%s,%s,%s,%s,%s)", (
            str(review_dict["id"]), str(book_id), str(review_dict["user_id"]), review_dict["review"],
            review_dict["rating"]))
        conn.commit()
        return review_dict

    except Exception as e:
        print(e)
        return None


def getReviews(book_id: uuid.UUID):
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select * from reviews where book_id = %s", (str(book_id),))
    reviews = cursor.fetchall()
    # summary = summarizeReviews(reviews)
    # convert revies to dictionary
    reviews_list = []

    return reviews


def summarizeReviews(reviews):
    summary = {}
    df_reviews = df(reviews, columns=["review", "rating"])
    reviews_list = df_reviews.get("review")
    summarized_reviews = summarize(reviews_list)
    summary['summary'] = summarized_reviews

    rating_avg = df_reviews.get("rating")
    rating_avg = rating_avg.mean()
    summary['rating'] = rating_avg
    # summary = df_reviews.describe()
    return summary


def summarize(reviews):
    # call LLM to summarize the reviews
    return " ".join(reviews)

def getBookSummary(book_id: uuid.UUID):
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("select summary from book where id = %s", (str(book_id),))
    book_details = cursor.fetchone()
    if(book_details is None):
        return None
    summary = book_details[5]
    if(summary is None):
        content = book_details[4]
        summary = generateSummary(content)

    return summary