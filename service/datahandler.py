import os
import uuid

from minio import Minio
import dotenv
from pandas import DataFrame as df
from psycopg2 import connect
from AIUtil import summarize_reviews, generateSummary
from contextlib import contextmanager

# create connections to database

# create cursor
# create table schema
# execute the connections in db
dotenv.load_dotenv()

db_config = {
    "dbname": os.getenv("database_name"),
    "host": os.getenv("database_host"),
    "port": os.getenv("database_port"),
    "user": os.getenv("database_user"),
    "password": os.getenv("database_password")
}


@contextmanager
def db_connection():
    conn = connect(**db_config)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    # create table if not exist
    # create table schema if not exit

    book_table = "create table if not exists book(id UUID PRIMARY KEY,title varchar(50),author varchar(50),genre varchar(30), year_published int,summary varchar(5000))"
    user_table = "create table if not exists users(id UUID primary key, name varchar(50) UNIQUE, password varchar(100))"
    review_table = "create table if not exists reviews(id UUID PRIMARY KEY, book_id UUID, user_id UUID, review text, rating decimal, constraint fk_user FOREIGN KEY(user_id) references users(id) on delete cascade, constraint fk_book FOREIGN KEY(book_id) references book(id) on delete cascade )"
    conn = connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(book_table)
    cursor.execute(user_table)
    cursor.execute(review_table)
    conn.commit()
    conn.close()
    print("db initialized")


def createUser(user):

    if user.id is None:
        user.id = uuid.uuid4()

    user_dict = user.dict()
    print(user_dict)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("insert into users(id,name,password) values(%s,%s,%s)",
                       (str(user_dict["id"]), user_dict["name"], user_dict["password"]))
        conn.commit()
        return user_dict


def getUser(user_id: uuid.UUID):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("select * from users where id = %s", (str(user_id),))
        user = cursor.fetchone()
        return user


def getBooks():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("select * from book")
        books = cursor.fetchall()
        conn.close()

        # convert to dictionary
        books_list = []
        for book in books:
            book_dict = {
                'id': book[0],
                'title': book[1],
                'author': book[2],
                'genre': book[3],
                'year_published': book[4],
                'summary': book[5]
            }
            books_list.append(book_dict)
        return books_list


def createBook(book):

    with db_connection() as conn:
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

#
# def getBook(book_id: uuid.UUID):
#     with db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute("select * from book where id = %s", (str(book_id),))
#         book = cursor.fetchone()
#         return book


def getBook():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("select * from book")
        books = cursor.fetchall()
        return books


def getBook(book_id: uuid.UUID):
    with db_connection() as conn:
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
        conn.close()
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
        conn.close()
        return None


def createReview(book_id, review, user_id):
    try:
        if review.id is None:
            review.id = uuid.uuid4()

        review_dict = review.dict()
        review_dict["book_id"] = book_id
        review_dict["user_id"] = user_id
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("insert into reviews(id,book_id,user_id,review,rating) values(%s,%s,%s,%s,%s)", (
            str(review_dict["id"]), str(book_id), str(review_dict["user_id"]), review_dict["review"],
            review_dict["rating"]))
        conn.commit()
        return review_dict

    except Exception as e:
        print(e)
        conn.close()
        return None


def getReviews(book_id: uuid.UUID):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("select * from reviews where book_id = %s", (str(book_id),))
        reviews = cursor.fetchall()
        # summary = summarizeReviews(reviews)
        # convert revies to dictionary
        reviews_list = []

        return reviews


def summarizeReviews(reviews):
    summary = {}
    df_reviews = df(reviews, columns=['id', 'book_id', 'user_id', 'review', 'rating'])
    reviews_list = df_reviews.get("review")
    summarized_reviews = summarize_reviews(reviews_list)
    summary['summary'] = summarized_reviews

    rating_avg = df_reviews.get("rating")
    rating_avg = rating_avg.mean()
    summary['rating'] = rating_avg
    # summary = df_reviews.describe()
    return summary


def getBookSummary(book_id: uuid.UUID):

    try:
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("select summary from book where id = %s", (str(book_id),))
        book_details = cursor.fetchone()
        if book_details is None:
            return None
        summary = book_details[5]
        if summary is None:
            content = book_details[4]
            summary = generateSummary(content)
    except Exception as e:
        print(e)
        return None
    finally:
        conn.close()
    return summary


def get_user_from_db(user_name: str):
    try:
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("select * from users where name = %s", (user_name,))
        user = cursor.fetchone()
        if user is None:
            return None
        # create dictionary from user
        user_dict = {'id': user[0], 'name': user[1], 'password': user[2]}
    except Exception as e:
        print(e)
        return None
    finally:
        conn.close()

    return user_dict