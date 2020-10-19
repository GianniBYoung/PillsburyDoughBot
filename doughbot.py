from pathlib import Path
import keyboard
import schedule
import time
import datetime
import praw
import subprocess
import sys
import os
import requests
import configparser


def reddit_authentication(config, projectPath):
    auth = projectPath + '/auth.ini'
    config.read ('credentials')
    redditClientId = config.get('credentials', 'reddit_Client_Id')
    redditClientSecret = config.get('credentials', 'reddit_Client_Secret')
    redditUsername = config.get('credentials', 'reddit_Username')
    redditPassword = config.get('credentials', 'reddit_Password')
    return praw.Reddit(client_id = redditClientId,
		         client_secret = redditClientSecret,
		         username = redditUsername,
		         password = redditPassword,
		         user_agent = 'PillsburyDoughBot')




def upload_media(title, imagePath, projectPath):
    auth = projectPath + '/auth.ini'
    config = configparser.ConfigParser()
    config.read(auth)
    cookie = config.get('credentials', 'imgur_cookie')
    fileExtension = imagePath[-3:]

    if fileExtension == 'mp4':
        fileType = 'video'
    else:
        fileType = 'image'

    url = "https://api.imgur.com/3/upload"
    payload = {'title': title}
    files = [
      (fileType, open(imagePath,'rb')),
      ('type', open(imagePath,'rb'))
    ]
    headers = {
      'Cookie': cookie 
    }

    response = requests.request("POST", url, headers=headers, data = payload, files = files)
    return response




def cross_post(imageTitle, crossSubreddit, post):

    crossPostable = True
#searches for artists that are meant to be excluded
    refrainList = open('refrainlist.txt', 'r')
    while True:
        line = refrainList.readline().strip()
        if not line:
            break
        elif imageTitle[0].strip() == line:
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
            post.crosspost(subreddit=crossSubreddit, title=imageTitle,nsfw=True)
        except:
            print("Error cross posting. make sure you are subscribed to the subreddit and that crossposting is allowed.")
            with open('noCrossPost.txt', 'w') as file:
                file.write(crossSubreddit)
    else:
        print("r/" + crossSubreddit + " cannot be posted to or is on the refrain list.")
        return
    print(crossSubreddit)




def doughbot():
    if len(sys.argv) < 2 :
        print("Usage: python3 doughbot.py <subreddit> [Directory of images] \n Directory of images must be provided on first run.")
        exit()

    projectPath = os.path.dirname(os.path.realpath(__file__)) 
    authFile = projectPath + "/auth.ini"
    config = configparser.ConfigParser()
    config.read(authFile)
    redditClient = reddit_authentication(config, projectPath)
    subreddit = redditClient.subreddit(str(sys.argv[1]))


    #keeps track of what image should be posted
    imageLogPath = Path(projectPath + '/imageLog.txt')
    if imageLogPath.is_file():
        imageLog = open(imageLogPath,'r')
        imageToPost = int(imageLog.readline()) + 1
        imageLog.close()
    else:
        imageLog = open(imageLogPath,'w')
        imageToPost = 0
        imageLog.write(imageToPost)
    
    masterList = open(projectPath + '/masterMedia.txt','r')
    with open(projectPath + '/masterMedia.txt') as f:
        imagePaths = f.read().splitlines()

    #cleans up the title and provides the path to image to be posted
    imagePath = imagePaths[imageToPost].strip()
    imageTitle = imagePaths[imageToPost].split("/")
    crossSubreddit = imageTitle[4]
    imageTitle = imageTitle[len(imageTitle) - 1]
    imageTitle = imageTitle.replace("_", " ")
    imageTitle = imageTitle.replace("-", " ")
    imageTitle = imageTitle.replace(".", " ")
    imageTitle = imageTitle.rsplit(' ', 2)[0]
    
    masterList.close()
    imageLog.close()

    imageLog = open(imageLogPath, 'w')
    imageLog.write(str(imageToPost))
    imageLog.close()

    #json response containing image info
    imageResponse = upload_media(imageTitle, imagePath,projectPath).json()
    statusCode = imageResponse["status"]
    if statusCode != 200:
        return -1

    imageUrl = imageResponse["data"]["link"] 


    post = subreddit.submit(title = imageTitle, url = imageUrl)
    #cross_post(imageTitle, crossSubreddit, post)
    try:
        submission = redditClient.submission(id = str(post.id))
        submission.reply("This image was originally obtained from [" + crossSubreddit + "](" + "https://www.reddit.com/r/" + crossSubreddit + ")")
    except:
        return -1
    now = datetime.datetime.now()
    print(now.strftime('Posted at: %I:%M'))
    print("Image Link: " + imageUrl)
    return


if len(sys.argv) == 3 :
    print("The master record will be updated.")
    subprocess.call([os.path.dirname(os.path.realpath(__file__)) + "/directorylist.sh", str(sys.argv[2])])
doughbot()

   #For scheduling task execution
schedule.every(25).minutes.do(doughbot)
while True:
    schedule.run_pending()
    time.sleep(1)
