import os
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BEETS_CONFIG = "/config/config.yaml"
UNSORTED_DIR = "/music_unsorted"

class MusicHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Wait briefly to ensure the file finishes copying
        time.sleep(2)

        # Option A: Import the single new file/folder
        # subprocess.run(["beet", "-c", BEETS_CONFIG, "import", event.src_path])

        # Option B: Import the entire unsorted folder each time
        subprocess.run(["beet", "-c", BEETS_CONFIG, "import", UNSORTED_DIR])

def main():
    event_handler = MusicHandler()
    observer = Observer()
    observer.schedule(event_handler, UNSORTED_DIR, recursive=True)
    observer.start()
    print("Watching for new music in:", UNSORTED_DIR)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
