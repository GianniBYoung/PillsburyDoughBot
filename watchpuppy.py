#derived from watchpuppy by Davide Mastromatteo
#http://thepythoncorner.com/dev/how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/
import time
from config import basePath, pathToPosts
from doughbot import deconstruct_path, insert_full_entry, query_database
import sqlite3
from watchdog.observers import Observer,polling
from watchdog.events import PatternMatchingEventHandler

PATHTOBEOBSERVED = basePath

def on_created(event):
    postsTxt = open(pathToPosts, 'a')
    filePath = event.src_path

    if filePath.endswith(('.png','jpg','pdf','gif','wav','mkv','mp4')):

        postsTxt.write(filePath + '\n')
        print(f"{event.src_path} has been added!")
        detailsDict = deconstruct_path(filePath)
        insert_full_entry(detailsDict)

    postsTxt.close()


def on_deletion(event):
    try:

        query_database('''DELETE FROM Posts WHERE media Path = "''' + event.src_path + '"')[0][0]
        print(f"{event.src_path} has been removed from the database")

    except:

        print("Could not be removed from the databse. Was it in there to begin with?")


if __name__ == "__main__":

    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns,
                                                   ignore_directories,
                                                   case_sensitive)

    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deletion

    path = PATHTOBEOBSERVED
    go_recursively = True

    my_observer = polling.PollingObserver()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    my_observer.start()
    try:
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        my_observer.stop()
    my_observer.join()
