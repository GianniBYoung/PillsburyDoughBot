#using watchdog i can now store posts in the db if i would like to instead of a text file.
import sqlite3
import subprocess
import os
import praw
import requests
from config import *

# /media/unit/ripme/AbsoluteUnits
# /media/unit/ripme/AbsoluteUnits/FimonFogus_Hope_this_hasn_t_been_posted_before__cigdl2.jpg


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

    cursor.execute("CREATE TABLE IF NOT EXISTS Users \
         (userId INTEGER PRIMARY KEY, name TEXT, allowedToPost INTEGER)")

    cursor.execute("CREATE TABLE IF NOT EXISTS Posts \
         (id INTEGER NOT NULL PRIMARY KEY, title text, author TEXT, mediaPath TEXT, \
         FOREIGN KEY (author) REFERENCES Users(userId));")

    cursor.execute("CREATE TABLE IF NOT EXISTS Subreddits \
         (id INTEGER NOT NULL PRIMARY KEY, name TEXT, allowsCrossPosts INTEGER);"
                   )
    con.commit()


def insert_user(name="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Users(name, allowedToPost) \
                      VALUES (?,?)''', (name, -1))
    con.commit()


def insert_post(authorKey, mediaPath, title="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Posts(title, author, mediaPath) \
           VALUES (?,?,?)''', (title, authorKey, mediaPath))
    con.commit()


def insert_subreddit(name):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Subreddits(name, allowsCrossPosts) \
           VALUES (?,?)''', (name, 1))
    con.commit()


# /media/unit/ripme/AbsoluteUnits/FimonFogus_Hope_this_hasn_t_been_posted_before__cigdl2.jpg
# returns a dictionary containing subreddit, author, title, postid
def deconstruct_path(mediaPath):
    subreddit = mediaPath.split("/")[4]
    
    post = mediaPath.split("/")[5].split("_")

    author = post[0]

    postId = post[len(post)-1].split('.')[0]

    title = post[1]
    title = ' '.join(post[1:len(post)-2])
    
    submission = {"subreddit":subreddit, "author":author, "title":title, "postId": postId}
    return submission 


#TODO grab fileExtension
#can use ends with
def upload_to_imgur(title, imagePath):
    fileExtension = "the file ext"
    if fileExtension == 'mp4':
        fileType = 'video'
    else:
        fileType = 'image'

    try:
        url = "https://api.imgur.com/3/upload"
        payload = {'title': title}
        files = [(fileType, open(imagePath, 'rb')),
                 ('type', open(imagePath, 'rb'))]
        headers = {'Cookie': imgurCookie}

        response = requests.request("POST",
                                    url,
                                    headers=headers,
                                    data=payload,
                                    files=files)
        return response
    except:
        print("Unable to upload to imgur")


def get_media_paths():
    postsTxt = open(pathToPosts, 'w')
    for subdir, dirs, files in os.walk(basePath):
        for filename in files:
            filepath = subdir + os.sep + filename

            if filepath.endswith(".jpg") or filepath.endswith(
                    ".png") or filepath.endswith(".gif") or filepath.endswith(
                        ".mp4"):
                postsTxt.write(filepath + '\n')

    postsTxt.close()



#create_database()
#insert_user("Gianni")
#insert_post(1, "ths/is/a/path")
#insert_subredditt("AbsoluteUnits")
get_media_paths()
