#using watchdog i can now store posts in the db if i would like to instead of a text file.
import sqlite3
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

    # creates Users table
    cursor.execute("CREATE TABLE IF NOT EXISTS Users \
         (userId INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL UNIQUE, allowedToPost INTEGER)"
                   )

    # creates Posts table
    cursor.execute("CREATE TABLE IF NOT EXISTS Posts \
         (id INTEGER NOT NULL PRIMARY KEY, title text NOT NULL, author, mediaPath TEXT, \
         FOREIGN KEY (author) REFERENCES Users(userId));")

    # creates Subreddits table
    cursor.execute("CREATE TABLE IF NOT EXISTS Subreddits \
         (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL UNIQUE, allowsCrossPosts INTEGER);"
                   )
    con.commit()


# inserts a single user to the db
def insert_user(name):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT OR IGNORE INTO Users(name, allowedToPost) \
                      VALUES (?,?)''', (name, -1))
    con.commit()


# inserts a single post to the db
def insert_post(authorKey, mediaPath, title="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT OR IGNORE INTO Posts(title, author, mediaPath) \
           VALUES (?,?,?)''', (title, authorKey, mediaPath))
    con.commit()


# inserts a single subreddit to the db
def insert_subreddit(name):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT OR IGNORE INTO Subreddits(name, allowsCrossPosts) \
           VALUES (?,?)''', (name, 1))
    con.commit()


# returns a dictionary containing subreddit, author, title, postid
def deconstruct_path(mediaPath):
    subreddit = mediaPath.split("/")[4]
    post = mediaPath.split("/")[5].split("_")
    author = post[0]
    postId = post[len(post) - 1].split('.')[0]
    title = post[1]
    #grabs title exluding subreddit and postId
    title = title + ' '.join(post[1:len(post) - 2])
    submission = {
        "subreddit": subreddit,
        "author": author,
        "title": title,
        "postId": postId,
        "path": mediaPath
    }
    print(submission["title"])
    return submission


#TODO grab fileExtension
def upload_to_imgur(detailsDict):
    if detailsDict["path"].endswith(".mp4"):
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
        print(detailsDict["imgurLink"])
        return detailsDict
    except:
        print("Unable to upload to imgur")


# uploads media to specified subreddit and returns postId
def upload_to_reddit(detailsDict, subreddit):
    redditClient = reddit_authentication()
    subreddit = redditClient.subreddit(subreddit)
    redditClient.validate_on_submit = True

    redditPost = subreddit.submit(title=detailsDict["title"],
                                  url=detailsDict["imgurLink"])
    return str(redditPost.id)


def comment_on_post(postId, content):
    redditClient = reddit_authentication()
    submission = redditClient.submission(id=str(postId))
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


# adds multiple subreddits to db
def populate_subreddits():
    posts = posts_to_list()
    #removes the empty line at the end of a file
    del posts[-1]
    for path in posts:
        deconstruction = deconstruct_path(path)
        insert_subreddit(deconstruction["subreddit"])


