import argparse
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
         (userId INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL UNIQUE, allowPost INTEGER)"
                   )

    # creates Subreddits table
    cursor.execute("CREATE TABLE IF NOT EXISTS Subreddits \
         (subredditId INTEGER NOT NULL PRIMARY KEY, \
         name TEXT NOT NULL UNIQUE, allowsCrossPosts INTEGER, allowPost INTEGER);"
                   )

    # creates Posts table
    cursor.execute("CREATE TABLE IF NOT EXISTS Posts \
         (id INTEGER NOT NULL PRIMARY KEY, title TEXT NOT NULL, author INTEGER NOT NULL, mediaPath TEXT, subreddit INTEGER NOT NULL, \
          posted INTEGER, \
         FOREIGN KEY (author) REFERENCES Users(userId),\
         FOREIGN KEY (subreddit) REFERENCES Subreddits(id));")

    con.commit()


# queries the database and returns the results
def query_database(query):
    con = sqlite3.connect('main.db')
    con.execute("PRAGMA foreign_keys = on")
    cursor = con.cursor()

    cursor.execute(query)
    con.commit()
    return cursor.fetchall()


# inserts a single user to the db
def insert_user(name):
    con = sqlite3.connect('main.db')
    con.execute("PRAGMA foreign_keys = on")
    cursor = con.cursor()

    cursor.execute(
        '''INSERT OR IGNORE INTO Users(name, allowPost) \
                      VALUES (?,?)''', (name, 1))
    con.commit()


# inserts a single post to the db
def insert_post(authorKey, subredditPrimaryKey, mediaPath, title="Unknown"):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT OR IGNORE INTO Posts(title, author, mediaPath, subreddit, posted) \
           VALUES (?,?,?,?,?)''',
        (title, authorKey, mediaPath, subredditPrimaryKey, 0))
    con.commit()


# inserts a single subreddit to the db
def insert_subreddit(name):
    con = sqlite3.connect('main.db')
    cursor = con.cursor()

    cursor.execute(
        '''INSERT OR IGNORE INTO Subreddits(name, allowsCrossPosts, allowPost) \
           VALUES (?,?,?)''', (name, 1, 1))
    con.commit()


# inserts a user, subreddit, and post
def insert_full_entry(detailsDict):
    insert_user(detailsDict["author"])

    authorPrimaryKey = query_database('''SELECT userId FROM Users WHERE name = '''\
            + '"' + detailsDict["author"] + '"')[0][0]

    insert_subreddit(detailsDict["subreddit"])
    subredditPrimaryKey = query_database(
        '''SELECT subredditId FROM Subreddits WHERE\
            name = ''' + '"' + detailsDict["subreddit"] + '"')[0][0]

    insert_post(authorPrimaryKey,
                subredditPrimaryKey,
                detailsDict["path"],
                title=detailsDict["title"])


# disables posting content to specified reddits
def disable_post_to_subreddit(subreddit):
    query_database('''UPDATE subreddits SET allowPost = 0 WHERE name = "''' +
                   subreddit + '"')


# disables posting of specified users content
def disable_post_by_user(username):
    query_database('''UPDATE Users SET allowPost = 0 WHERE name = "''' +
                   username + '"')

# bulk disabling of subreddits
def disable_post_to_subreddit_from_file(pathToTextFile):
    file = open(pathToTextFile)
    lines = file.read().split('\n')
    file.close()
    del lines[-1]

    for line in lines:
        disable_post_to_subreddit(line)


# bulk disabling of posts from specified users
def disable_post_by_user_from_file(pathToTextFile):
    file = open(pathToTextFile)
    lines = file.read().split('\n')
    file.close()

    for line in lines:
        disable_post_by_user(line)


def disable_crosspost(subreddit):
    query_database(
        '''UPDATE Subreddits SET allowsCrossPosts = 0 WHERE name = "''' +
        subreddit + '"')


# returns a dictionary containing subreddit, author, title, postid
def deconstruct_path(mediaPath):
    subreddit = mediaPath.split("/")[4]
    post = mediaPath.split("/")[5].split("_")
    author = post[0]
    postId = post[len(post) - 1].split('.')[0]
    title = post[1]
    #grabs title exluding subreddit and postId
    title = ' '.join(post[1:len(post) - 1]) + " | obtained from user: " + author
    submission = {
        "subreddit": subreddit.lower(),
        "author": author,
        "title": title,
        "postId": postId,
        "path": mediaPath
    }
    return submission

# uploads media and returns an updated dictionary with link
def upload_to_imgur(detailsDict):
    allowPostUser = query_database(
        '''SELECT allowPost FROM Users WHERE name = "''' +
        detailsDict["author"] + '"')[0][0]

    allowPostSubreddit = query_database(
        '''SELECT allowPost FROM Subreddits WHERE name = "''' +
        detailsDict["subreddit"] + '"')[0][0]

    if (allowPostUser and allowPostSubreddit):

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
            print("uploaded to imgur")
            print(detailsDict["imgurLink"])
            return detailsDict
        except:
            print("Unable to upload to imgur")
        else:
            print("error, post or subreddit is not supposed to be posted to")


# uploads media to specified subreddit and returns a praw post
def upload_to_reddit(detailsDict, subreddit):
    try:
        redditClient = reddit_authentication()
        subreddit = redditClient.subreddit(subreddit)
        redditClient.validate_on_submit = True


        redditPost = subreddit.submit(title=detailsDict["title"],
                                      url=detailsDict["imgurLink"])
        return redditPost
    except:
        print("Error while posting to reddit. Did you specify the subreddit?")

# leaves a comment on specified reddit post
def comment_on_post(post, content):
    redditClient = reddit_authentication()
    submission = redditClient.submission(id=str(post.id))
    submission.reply(content)


def crosspost(detailsDict):
    redditClient = reddit_authentication()
    redditPost = redditClient.submission(id=detailsDict["postId"])
    crossPost = redditPost.crosspost(subreddit=detailsDict["subreddit"],
                                     title=detailsDict["title"],
                                     nsfw=True)
    return crossPost


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
    del lines[-1]
    return lines


# adds multiple subreddits to db
def populate_subreddits():
    posts = posts_to_list()
    del posts[-1]
    for path in posts:
        deconstruction = deconstruct_path(path)
        insert_subreddit(deconstruction["subreddit"])
    return posts

# obtains a paths from get_media_paths and Translates info into the database
def populate_database():
    get_media_paths()
    posts = populate_subreddits()
    for line in posts:
        insert_full_entry(deconstruct_path(line))


# takes an unposted entry from the db, uploads to imgur and reddit
# and returns dictionary with postId added
def post_from_database(subreddit):
    try:
        unposted = query_database(
            '''SELECT mediaPath FROM Posts WHERE posted = 0 ''')
        detailsDict = deconstruct_path(unposted[0][0])
        detailsDict = upload_to_imgur(detailsDict)
        postId = upload_to_reddit(detailsDict, subreddit).id
        query_database('''UPDATE Posts SET posted = 1 WHERE mediaPath = ''' +
                       '"' + detailsDict["path"] + '"')
        print("Image has been posted to reddit.")
        detailsDict["postId"] = postId
        return detailsDict
    except:
        print("Error encountered while posting from database.")

# personal comment for my own usecase detailed in readme
def personal_comment(detailsDict):
    redditClient = reddit_authentication()
    submission = redditClient.submission(id=detailsDict["postId"])
    submission.reply("This image was originally posted by [" +
                     detailsDict["author"] + "](" +
                     "https://www.reddit.com/u/" + detailsDict["author"] +
                     ") obtained from [" + detailsDict["subreddit"] + "](" +
                     "https://www.reddit.com/r/" + detailsDict["subreddit"] +
                     ").")

    submission.reply(
        "Note, if the link to the user's page does not work it is likely because their username\
         contains underscores. The original posters handle is the first sequence in the following: " + 
         detailsDict["path"].split("/")[5] + " and the part before the extension is the og post id " +
         "You can try to find them by using a link formed like: http://www.reddit.com/u/red_sonja"
    )





def main():
    parser = argparse.ArgumentParser(
        description="Upload Media to Specified Subreddit")
    parser.add_argument("-s",
                        "--subreddit",
                        help="Specify Subreddit",
                        required=False)
    parser.add_argument("-c",
                        "--crosspost",
                        help="Enable Cross Posting",
                        required=False,
                        action="store_true")
    parser.add_argument("-p",
                        "--populate-from-file",
                        help="populate database with pre existing data",
                        required=False,
                        action="store_true")
    parser.add_argument("--disable-user",
                        help="restrict posting specified users",
                        required=False)
    parser.add_argument("--disable-subreddit",
                        help="restrict posting specified subreddits",
                        required=False)
    args = parser.parse_args()

    create_database()

    if args.populate_from_file:
        populate_database()

    if args.disable_user is not None:
        disable_post_by_user_from_file(args.disable_user)

    if args.disable_subreddit is not None:
        disable_post_to_subreddit_from_file(args.disable_subreddit)

    detailsDict = post_from_database(args.subreddit)
    personal_comment(detailsDict)

    if args.crosspost:
        try:
            crosspost(detailsDict)
        except:
            disable_crosspost(detailsDict["subreddit"])

    print("Execution completed.")



if __name__ == "__main__":
    main()
