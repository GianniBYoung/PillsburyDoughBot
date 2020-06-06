from pathlib import Path
import praw
import subprocess
import sys
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
def imgurLogin(imgur, imgur_username, imgur_password):
    authorization_url = imgurClient.get_auth_url('pin')
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
    credentials = imgurClient.authorize(pin,'pin')
    imgurClient.set_user_auth(credentials['access_token'], credentials['refresh_token'])




def upload_image(client, title):
     config = {
             'title': title,
             }
     print ('uploading image')
     image = client.upload_from_path(image_path, config, anon=False)
     return image



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





config = configparser.ConfigParser()
config.read('auth.ini')
imgurClient = imgurAuthentication(config)
redditClient = redditAuthentication(config)

imgur_username = config.get('credentials', 'imgur_username')
imgur_password = config.get('credentials', 'imgur_password')

image_path = "this is a placeholder"
subreddit = redditClient.subreddit('MancysMuses')

imgurLogin(imgurClient, imgur_username, imgur_password)
imagelogPath=Path('./imageLog.txt')
if imagelogPath.is_file():
    imagelog = open(imagelogPath,'r')
    imageToPost=int(imagelog.readline())+1
    imagelog.close()
    imagelog = open(imagelogPath,'w')
    imagelog.write(str(imageToPost))
else:
    imagelog = open(imagelogPath,'w')
    imageToPost=0
    imagelog.write(imageToPost)

masterList = open('./masterMedia.txt','r')
with open('./masterMedia.txt') as f:
    imagePaths=f.read().splitlines()

image_path=imagePaths[imageToPost]    
image_title= imagePaths[imageToPost].split("/")
image_title= image_title[len(image_title)-1]
image_title= image_title.replace("_"," ")
image_title= image_title.replace("-"," ")
image_title= image_title.replace("."," ")
image_title= image_title.rsplit(' ', 2)[0]

masterList.close()
imagelog.close()
image = upload_image(imgurClient, image_path)
imageUrl = format(image['link'])
print("Image was posted!")
print("You can find the image here: {0}".format(image['link']))
subreddit.submit(title = image_title, url = imageUrl)
