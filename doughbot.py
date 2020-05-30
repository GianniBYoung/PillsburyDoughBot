import praw
import requests
import configparser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from imgurpython import ImgurClient


def upload_image(client, title):
     config = {
             'title': title,
             }
     print ('uploading image')
     image = client.upload_from_path(image_path, config, anon=False)
     print("done")
     print()
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
imgur_username = config.get('credentials', 'imgur_username')
imgur_password = config.get('credentials', 'imgur_password')

imgurClient = imgurAuthentication(config)
redditClient = redditAuthentication(config)

image_path = "pixxelzombie_she's_ready_to_serve_c9l7zh.jpg"
subreddit = redditClient.subreddit('MancysMuses')

#this is for selenium (autologin)
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



image = upload_image(imgurClient, "this is the path to the image")
imageUrl = format(image['link'])
print("Image was posted!")
print("You can find the image here: {0}".format(image['link']))
subreddit.submit(title = image_path, url = imageUrl)
