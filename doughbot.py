from pathlib import Path
import keyboard
import schedule
import time
import praw
import subprocess
import sys
import os
import requests
import configparser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from imgurpython import ImgurClient

#this is for selenium (autologin)
def imgurLogin(imgur, config):
    imgur_username = config.get('credentials', 'imgur_username')
    imgur_password = config.get('credentials', 'imgur_password')
    authorization_url = imgur.get_auth_url('pin')
    driver = webdriver.Firefox()
    driver.get(authorization_url)

    username = driver.find_element_by_xpath('//*[@id="username"]')
    password = driver.find_element_by_xpath('//*[@id="password"]')
    username.clear()
    username.send_keys(imgur_username)
    password.send_keys(imgur_password)
    driver.find_element_by_name("allow").click()


    timeout = 5
    try:
        element_present = EC.presence_of_element_located((By.ID, 'pin'))
        WebDriverWait(driver, timeout).until(element_present)
        pin_element = driver.find_element_by_id('pin')
        pin = pin_element.get_attribute("value")
    except TimeoutException:
        print("Timed out waiting for page to load")
    driver.close()
    credentials = imgur.authorize(pin,'pin')
    imgur.set_user_auth(credentials['access_token'], credentials['refresh_token'])



#uploads an image or a gif to imgur
def upload_image(client, title, image_path):
     config = {
             'title': title,
             }
     print ('uploading image')
     try:
         image = client.upload_from_path(image_path, config, anon=False)
         return image
     except:
         print("File type cannot be uploaded to Imgur. We'll get em next time.")
         return -1



def cross_post(image_title, cross_subreddit, post):

    crossPostable = True
#searches for artists that are meant to be excluded
    refrainList = open('refrainlist.txt', 'r')
    while True:
        line = refrainList.readline().strip()
        if not line:
            break
        elif image_title[0].strip() == line:
            return -1

    refrainList.close()

#checks if the given subreddit allows crossposts
    noCrossPost = open('noCrossPost.txt', 'r')
    while True:
        line = noCrossPost.readline().strip()
        if not line:
            break
        elif cross_subreddit == line:
           crossPostable = False 

    noCrossPost.close()

#attempts to crosspost and if the request is blocked noCrossPost.txt is updated
    if crossPostable:
        try:
            post.crosspost(subreddit=cross_subreddit, title=image_title,nsfw=True)
        except:
            print("Error Cross Posting. Make Sure You Are Subscribed To The Subredditand that crossposting is allowed.")
            with open('noCrossPost.txt', 'w') as file:
                file.write(cross_subreddit)
    else:
        print("r/" + cross_subreddit + " cannot be posted to")
        return
    print(cross_subreddit)



def redditAuthentication(config):
    config.read('auth.ini')
    reddit_client_Id = config.get('credentials', 'reddit_client_id')
    reddit_client_secret = config.get('credentials', 'reddit_client_secret')
    reddit_username = config.get('credentials', 'reddit_username')
    reddit_password = config.get('credentials', 'reddit_password')
    return praw.Reddit(client_id = reddit_client_Id,
		         client_secret = reddit_client_secret,
		         username = reddit_username,
		         password = reddit_password,
		         user_agent = 'PillsburyDoughBot')




def imgurAuthentication(config):
    config.read('auth.ini')
    imgur_client_Id = config.get('credentials', 'imgur_client_id')
    imgur_client_secret = config.get('credentials', 'imgur_client_secret')
    imgur_username = config.get('credentials', 'imgur_username')
    imgur_password = config.get('credentials', 'imgur_password')
    return ImgurClient(client_id = imgur_client_Id,client_secret = imgur_client_secret)




def doughbot():
    if len(sys.argv) < 2 :
        print("Usage: python3 doughbot.py <subreddit> [Directory of images] \n Directory of images must be provided on first run.")
        exit()

    projectPath = os.path.dirname(os.path.realpath(__file__)) 
    authfile = projectPath + "/auth.ini"
    config = configparser.ConfigParser()
    config.read(authfile)
    imgurClient = imgurAuthentication(config)
    redditClient = redditAuthentication(config)
    subreddit = redditClient.subreddit(str(sys.argv[1]))

    if len(sys.argv) == 2 :
        subreddit = redditClient.subreddit(str(sys.argv[1]))

    #keeps track of what image should be posted
    imagelogPath=Path(projectPath + '/imageLog.txt')
    if imagelogPath.is_file():
        imagelog = open(imagelogPath,'r')
        imageToPost = int(imagelog.readline())+1
        imagelog.close()
    else:
        imagelog = open(imagelogPath,'w')
        imageToPost = 0
        imagelog.write(imageToPost)
    
    masterList = open(projectPath + '/masterMedia.txt','r')
    with open(projectPath + '/masterMedia.txt') as f:
        imagePaths = f.read().splitlines()

    #cleans up the title and provides the path to image to be posted
    image_path = imagePaths[imageToPost].strip()
    image_title = imagePaths[imageToPost].split("/")
    cross_subreddit = image_title[4]
    image_title = image_title[len(image_title)-1]
    image_title = image_title.replace("_"," ")
    image_title = image_title.replace("-"," ")
    image_title = image_title.replace("."," ")
    image_title = image_title.rsplit(' ', 2)[0]
    
    masterList.close()
    imagelog.close()
    imgurLogin(imgurClient, config)
    image = upload_image(imgurClient, image_title, image_path)

    if image==-1:
        return

    imageUrl = format(image['link'])
    print("You can find the image here: {0}".format(image['link']))
    post = subreddit.submit(title = image_title, url = imageUrl)
    cross_post(image_title, cross_subreddit, post)
    imagelog = open(imagelogPath,'w')
    imagelog.write(str(imageToPost))
    imagelog.close()
    return


if len(sys.argv) == 3 :
    print("The master record will be updated")
    subprocess.call([os.path.dirname(os.path.realpath(__file__)) + "/directorylist.sh", str(sys.argv[2])])
doughbot()
   #For scheduling task execution
schedule.every(1).hours.do(doughbot)
while True:
    schedule.run_pending()
    time.sleep(1)
