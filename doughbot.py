import praw
import sqlite3
from config import *

# to obtain correct fields flip the string first duhhh
def reddit_authentication():
    return praw.Reddit(client_id=redditClientid,
                       client_secret=redditClientsecret,
                       username=redditUsername,
                       password=redditPassword,
                       user_agent='PillsburyDoughBot')


def create_database():
    con = sqlite3.connect('main.db')
    con.execute("PRAGMA foreign_keys = on")
    cursor = con.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Users(userId INTEGER PRIMARY KEY, name TEXT, allowedToPost INTEGER)"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Posts(id integer NOT NULL PRIMARY KEY, title text, author text, mediaPath text, FOREIGN KEY (author) REFERENCES Users(userId));"
    )

    con.commit()


def insert_user(name="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute('''INSERT INTO Users(name, allowedToPost) VALUES (?,?)''',
                   (name, -1))
    con.commit()


def insert_post(authorKey, mediaPath, title="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Posts(title, author, mediaPath) VALUES (?,?,?)''',
        (title, authorKey, mediaPath))
    con.commit()


create_database()
insert_user("Gianni")
insert_post(1, "ths/is/a/path")
