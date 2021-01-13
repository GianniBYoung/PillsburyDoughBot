This program takes a directory of images/mp4s/gifs and uploads them to a user specified subreddit. It is intended to be used alongside Bulk Downloader for Reddit by aliparlakci(https://github.com/aliparlakci/bulk-downloader-for-reddit) with the default file path settings. If you have not used his program before I would reccomend creating an empty directory that will store the images to be downloaded and specifying the absolute path in the 'basePath' variable in config.py. Once the required information is entered in config.py you can either create a service for watchpuppy.py or run it on its own. watchpuppy will watch the given directory for new files and add them to the database. 

If however, you have already used Bulk downloader for reddit and have a pre-existing media directory you can call the function get_media_paths() and it will recurse through the basePath writing the path to a text file whose location is specified in config.py. You can then call populate_database() to translate the paths into the database.

Once the database has been populated regular usage is as follows: 
python3 doughbot.py --subreddit <subreddit>
