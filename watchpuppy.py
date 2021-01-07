#derived from watchpuppy by Davide Mastromatteo
#http://thepythoncorner.com/dev/how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/
import time
from config import basePath, pathToPosts
from watchdog.observers import Observer,polling
from watchdog.events import PatternMatchingEventHandler

PATHTOBEOBSERVED = basePath

def on_created(event):
    postsTxt = open(pathToPosts, 'a')
    filePath = event.src_path
    if str(filePath).endswith(('.png','jpg','pdf','gif','wav','mkv','mp4')):
        postsTxt.write(str(filePath) + '\n')
        print(f"{event.src_path} has been added!")

    postsTxt.close()


if __name__ == "__main__":

    patterns = "*" 
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns,
                                                   ignore_directories,
                                                   case_sensitive)

    my_event_handler.on_created = on_created

    path = PATHTOBEOBSERVED
    go_recursively = True

    #my_observer = Observer()
    my_observer = polling.PollingObserver()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    my_observer.start()
    try:
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        my_observer.stop()
    my_observer.join()
