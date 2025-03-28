import os
import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BEETS_CONFIG = "/config/config.yaml"
UNSORTED_DIR = "/music_unsorted"

class FolderHandler(FileSystemEventHandler):
    """
    Watches for both directory and file additions.
    If a new directory is detected, import that folder.
    If a new file is detected, import just that file
    (or the entire unsorted folder—your choice).
    """

    def on_created(self, event):
        # Wait briefly in case the file/folder is still being copied
        time.sleep(2)

        if event.is_directory:
            folder_path = event.src_path
            print(f"[Watcher] New folder detected: {folder_path}")
            self.import_path(folder_path)
        else:
            file_path = event.src_path
            print(f"[Watcher] New file detected: {file_path}")
            # Option A: Import just the single file
            # self.import_path(file_path)

            # Option B: Import the entire unsorted directory each time a file is added
            self.import_path(UNSORTED_DIR)

    def import_path(self, path):
        print(f"[Watcher] Running beets import on {path}")
        command = ["beet", "-vvvvv", "-c", BEETS_CONFIG, "import", "--from-scratch", "-s", "--set", "genraae='Alternative Rock'", path]
        print(f"[Watcher] Running command: {' '.join(command)}")
        subprocess.run(command, check=True, stdout=sys.stdout, stderr=sys.stderr)

def main():
    event_handler = FolderHandler()
    observer = Observer()
    # Watch the unsorted directory recursively (so subfolders are also tracked)
    observer.schedule(event_handler, UNSORTED_DIR, recursive=True)
    observer.start()
    print(f"[Watcher] Listening for new items in: {UNSORTED_DIR} ...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
