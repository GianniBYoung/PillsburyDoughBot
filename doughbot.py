#using watchdog i can now store posts in the db if i would like to instead of a text file.
import sqlite3
import subprocess
import os
import praw
import requests
from config import *

# returns a Reddit client with users details
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

# inserts a single user to the db
def insert_user(name="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Users(name, allowedToPost) \
                      VALUES (?,?)''', (name, -1))
    con.commit()


# inserts a single post to the db
def insert_post(authorKey, mediaPath, title="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Posts(title, author, mediaPath) \
           VALUES (?,?,?)''', (title, authorKey, mediaPath))
    con.commit()

# inserts a single subreddit to the db
def insert_subreddit(name):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT INTO Subreddits(name, allowsCrossPosts) \
           VALUES (?,?)''', (name, 1))
    con.commit()


# returns a dictionary containing subreddit, author, title, postid
def deconstruct_path(mediaPath):
    subreddit = mediaPath.split("/")[4]
    post = mediaPath.split("/")[5].split("_")
    author = post[0]
    postId = post[len(post) - 1].split('.')[0]
    title = post[1]
    title = ' '.join(post[1:len(post) - 2])
    submission = {
        "subreddit": subreddit,
        "author": author,
        "title": title,
        "postId": postId,
        "path": mediaPath
    }
    return submission


#TODO grab fileExtension
#can use ends with
def upload_to_imgur(detailsDict):
    if detailsDict["mediaPath"].endswith(".mp4"):
        fileType = 'video'
    else:
        fileType = 'image'

    try:
        url = "https://api.imgur.com/3/upload"
        payload = {'title': detailsDict["title"]}
        files = [(fileType, open(detailsDict["path"], 'rb')),
                 ('type', open(detailsDict["path"], 'rb'))]
        headers = {'Cookie': imgurCookie}

        response = requests.request("POST",
                                    url,
                                    headers=headers,
                                    data=payload,
                                    files=files)

        imgurUrl = response.json() 
        detailsDict["imgurLink"] = imgurUrl["data"]["link"]
        return detailsDict
    except:
        print("Unable to upload to imgur")

# uploads media to specified subreddit and returns postId
def upload_to_reddit(detailsDict, subreddit):
    redditClient = reddit_authenticate() 
    subreddit = redditClient.subreddit(subreddit)
    redditClient.validate_on_submit = True

    redditPost = subreddit.submit(title = detailsDict["title"], url = detailsDict["imgurLink"])
    return str(post.id)


def comment_on_post(postId, content):
    submission = redditClient.submission(id=str(post.id))
    submission.reply(content)

# obtains absolute paths from user specified basePath variable and
# outputs them to user specified pathToPosts variable
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

# Translates paths in posts.txt to a list
def posts_to_list():
    file = open(pathToPosts)
    lines = file.read().split('\n')
    file.close()
    return lines


# for populating, store author and the primary key in a dictionary to make creating subreddits easier
# adds multiple subreddits to db
def populate_subreddits():
    posts = posts_to_list()
    for path in posts:
        deconstruction = deconstruct_path(path)
        print(deconstruction["subreddit"])
        #insert_subreddit(deconstruction["subreddit"])

get_media_paths()
populate_subreddits()
