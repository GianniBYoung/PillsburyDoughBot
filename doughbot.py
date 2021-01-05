import argparse
import configparser
import datetime
import os
import subprocess
import time
from pathlib import Path

import praw
import requests
import schedule


def reddit_authentication(config):

    config.read('credentials')
    redditClientId = config.get('credentials', 'reddit_Client_Id')
    redditClientSecret = config.get('credentials', 'reddit_Client_Secret')
    redditUsername = config.get('credentials', 'reddit_Username')
    redditPassword = config.get('credentials', 'reddit_Password')
    return praw.Reddit(client_id=redditClientId,
                       client_secret=redditClientSecret,
                       username=redditUsername,
                       password=redditPassword,
                       user_agent='PillsburyDoughBot')


def upload_media(title, imagePath, projectPath, originalPoster):

    refrainList = open('refrainlist.txt', 'r')

    while True:
        line = refrainList.readline().strip()
        if not line:
            break
        elif originalPoster == line:
            refrainList.close()
            print("The original poster is on the refrainList, skipping")
            return -1

    refrainList.close()

    auth = projectPath + '/auth.ini'
    config = configparser.ConfigParser()
    config.read(auth)
    cookie = config.get('credentials', 'imgur_cookie')
    fileExtension = imagePath[-3:]

    if fileExtension == 'mp4':
        fileType = 'video'
    else:
        fileType = 'image'

    try:

        url = "https://api.imgur.com/3/upload"
        payload = {'title': title}
        files = [(fileType, open(imagePath, 'rb')),
                 ('type', open(imagePath, 'rb'))]
        headers = {'Cookie': cookie}

        response = requests.request("POST",
                                    url,
                                    headers=headers,
                                    data=payload,
                                    files=files)
        return response

    except:
        print("An error occured")


def check_if_allowed_subreddit(subreddit, projectPath):

    blackListSubs = open(projectPath + '/blackListSubs.txt', 'r')

    while True:
        line = blackListSubs.readline().strip()
        if not line:
            break
        elif subreddit == line:
            blackListSubs.close()
            return False

    blackListSubs.close()
    return True


def cross_post(imageTitle, crossSubreddit, post):

    crossPostable = True
    #searches for artists that are meant to be excluded
    refrainList = open('refrainlist.txt', 'r')

    while True:
        line = refrainList.readline().strip()
        if not line:
            break
        elif imageTitle[0].strip() == line:
            refrainList.close()
            return -1

    refrainList.close()

    #checks if the given subreddit allows crossposts
    noCrossPost = open('noCrossPost.txt', 'r')

    while True:
        line = noCrossPost.readline().strip()
        if not line:
            break
        elif crossSubreddit == line:
            crossPostable = False

    noCrossPost.close()

    #attempts to crosspost and if the request is blocked noCrossPost.txt is updated
    if crossPostable:
        try:
            post.crosspost(subreddit=crossSubreddit,
                           title=imageTitle,
                           nsfw=True)
        except:

            print(
                "Error cross posting. ."
            )
            with open('noCrossPost.txt', 'w') as file:
                file.write(crossSubreddit)

    else:
        print("r/" + crossSubreddit +
              " cannot be posted to or is on the refrain list.")
        return


def update_master(path):
    print("The master record will be updated.")
    subprocess.call([
        os.path.dirname(os.path.realpath(__file__)) + "/directorylist.sh", path
    ])


def increment_image_log(imageLogPath, imageToPost):
    imageLog = open(imageLogPath, 'w')
    imageLog.write(str(imageToPost))
    imageLog.close()
    return


def update_image_log(imageLogPath):
    if imageLogPath.is_file():
        imageLog = open(imageLogPath, 'r')
        imageToPost = int(imageLog.readline()) + 1
        imageLog.close()

    else:
        imageLog = open(imageLogPath, 'w')
        imageToPost = 0
        imageLog.write(imageToPost)
        imageLog.close()

    return imageToPost


def get_image_paths(projectPath):
    masterList = open(projectPath + '/masterMedia.txt', 'r')
    with open(projectPath + '/masterMedia.txt') as f:
        imagePaths = f.read().splitlines()
    return imagePaths


def doughbot(args):

    if args.update:
        update_master(args.path)

    projectPath = os.path.dirname(os.path.realpath(__file__))
    authFile = projectPath + "/auth.ini"
    config = configparser.ConfigParser()
    config.read(authFile)
    redditClient = reddit_authentication(config)
    subreddit = redditClient.subreddit(args.subreddit)
    redditClient.validate_on_submit = True

    #keeps track of what image should be posted
    imageLogPath = Path(projectPath + '/imageLog.txt')
    imageToPost = update_image_log(imageLogPath)

    #cleans up the title and provides the path to image to be posted
    imagePath = get_image_paths(projectPath)[imageToPost].strip()
    imageTitle = imagePath.split("/")
    crossSubreddit = imageTitle[4]
    imageTitle = imageTitle[len(imageTitle) - 1]
    originalPoster = imageTitle.split("_")
    originalPoster = originalPoster[0]
    imageTitle = imageTitle.replace("_", " ")
    imageTitle = imageTitle.replace("-", " ")
    imageTitle = imageTitle.replace(".", " ")
    imageTitle = imageTitle.rsplit(' ', 2)[0]

    increment_image_log(imageLogPath, imageToPost)

    if check_if_allowed_subreddit(crossSubreddit, projectPath):
        try:

            #json response containing image info
            imageResponse = upload_media(imageTitle, imagePath, projectPath,
                                         originalPoster).json()

            imageUrl = imageResponse["data"]["link"]
            post = subreddit.submit(title=imageTitle, url=imageUrl)

        except:
            print(
                "Unable to upload. Does the file exist? Subreddit exist? Credentials correct?"
            )
            return -1

        if args.crosspost:
            try:

                cross_post(imageTitle, crossSubreddit, post)

            except:
                print("Unable to crosspost")

        try:

            submission = redditClient.submission(id=str(post.id))
            submission.reply("This image was originally posted by [" +
                             originalPoster + "](" +
                             "https://www.reddit.com/u/" + originalPoster +
                             ") obtained from [" + crossSubreddit + "](" +
                             "https://www.reddit.com/r/" + crossSubreddit +
                             ").")

            submission.reply(
                "Note, if the link to the user's page does not work it is likely because their username contains underscores. The original posters handle is the first sequence in the title. You can attempt to find them by following a link in the form of: http://www.reddit.com/u/red_sonja"
            )

        except:
            return -1

    print(datetime.datetime.now().strftime('Posted at: %I:%M\nImage Link: ' +
                                           imageUrl))

    return


parser = argparse.ArgumentParser(
    description="Upload Media to Specified Subreddit")
parser.add_argument("-s",
                    "--subreddit",
                    help="Specify Subreddit",
                    required=True)
parser.add_argument("-u",
                    "--update",
                    help="Update MasterMedia.txt",
                    required=False,
                    action="store_true")
parser.add_argument("-c",
                    "--crosspost",
                    help="Enable Cross Posting",
                    required=False,
                    action="store_true")
parser.add_argument("-t",
                    "--timer",
                    help="Set Autopost Timer",
                    required=False,
                    type=int)
parser.add_argument("-p",
                    "--path",
                    help="Set Path to Saved Images",
                    required=False)
args = parser.parse_args()

doughbot(args)

#For scheduling task execution
print("Posting new image every " + str(args.timer) + " minutes")
if args.timer > 0:
    schedule.every(args.timer).minutes.do(doughbot, args=args)
    while True:
        schedule.run_pending()
        time.sleep(1)
