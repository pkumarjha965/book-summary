import uuid

from psycopg2 import connect

# create connections to database

# create cursor
# create table schema
# execute the connections in db

db_config = {
    "dbname": "bms",
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres123"
}


def init_db():
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


