import os
import re
import subprocess
import time
import logging
import yaml
import tempfile
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_config_with_env_variables(config_path):
    """
    Load a YAML configuration file, interpolate environment variables, 
    and return both the parsed config and the processed YAML text.
    """
    with open(config_path, 'r') as file:
        original_content = file.read()

    # Replace placeholders like ${VAR_NAME} with their environment variable values
    def replace_placeholder(match):
        env_var = match.group(1)
        return os.environ.get(env_var, match.group(0))  # keep placeholder if not found

    processed_content = re.sub(r'\${(\w+)}', replace_placeholder, original_content)
    parsed_config = yaml.safe_load(processed_content)
    return parsed_config, processed_content


def write_temp_config(text_content: str) -> str:
    """
    Write the processed YAML text directly to a temporary file
    and return its path.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    with open(temp_file.name, 'w') as file:
        file.write(text_content)
    return temp_file.name

def load_all_configs_with_env_variables(main_config_path):
    """
    Load the main YAML configuration file and all included configuration files,
    interpolate environment variables, and return a dictionary of all configurations.
    """
    # Load the main configuration file
    main_config, main_raw_yaml = load_config_with_env_variables(main_config_path)

    # Initialize a dictionary to store all configurations
    all_configs = {"main": main_config}

    # Process included configuration files
    included_files = main_config.get("include", [])
    for included_file in included_files:
        included_path = os.path.abspath(os.path.join(os.path.dirname(main_config_path), included_file))
        if os.path.exists(included_path):
            included_config, included_raw_yaml = load_config_with_env_variables(included_path)

            # Merge the included configuration into the main configuration
            main_config.update(included_config)

            # Add the included configuration to the dictionary
            all_configs[included_file] = included_config
        else:
            logging.warning(f"Included configuration file not found: {included_file}")

    return all_configs

# Read environment variables
BEETS_CONFIG = os.getenv("BEETS_CONFIG", "/app/config/config.yaml")
UNSORTED_DIR = os.getenv("UNSORTED_DIR", "/data/music/unsorted")
SORTED_DIR = os.getenv("SORTED_DIR", "/data/music/sorted")
LOGS_PATH = os.getenv("LOGS_PATH", "/app/logs")

# Load and process all configurations
all_configs = load_all_configs_with_env_variables(f"{BEETS_CONFIG}/config.yaml")

# Log the loaded configurations
for config_name, config_content in all_configs.items():
    logging.info(f"Loaded configuration: {config_name}")
    logging.debug(config_content)

# Write the processed configuration to a temporary file
BEETS_CONFIG_TEMP = write_temp_config(yaml.dump(all_configs["main"]))

# Log the contents of the generated temporary configuration file
with open(BEETS_CONFIG_TEMP, 'r') as temp_file:
    logging.info("Contents of the temporary configuration file:")
    logging.info(temp_file.read())

# Ensure the parent directory for the log file exists
log_dir = os.path.dirname(LOGS_PATH)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    logging.info(f"Created log directory: {log_dir}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{LOGS_PATH}/beets.log"),
        logging.StreamHandler()
    ]
)

# Ensure the UNSORTED_DIR directory exists
if not os.path.exists(UNSORTED_DIR):
    os.makedirs(UNSORTED_DIR)
    logging.info(f"Created directory: {UNSORTED_DIR}")

# Ensure the SORTED_DIR directory exists
if not os.path.exists(SORTED_DIR):
    os.makedirs(SORTED_DIR)
    logging.info(f"Created directory: {SORTED_DIR}")

class FolderHandler(FileSystemEventHandler):
    """
    Watches for newly added directories or files and triggers a beets import.
    """

    def on_created(self, event):
        time.sleep(2)  # give filesystem time to settle

        path = event.src_path
        if event.is_directory:
            logging.info(f"[Watcher] New folder detected: {path}")
        else:
            logging.info(f"[Watcher] New file detected: {path}")
        self.import_path(path)

    def import_path(self, path):
        logging.info(f"[Watcher] Running beets import on {path}")
        cmd = ["beet", "-vvvvv", "-c", BEETS_CONFIG_TEMP, "import", "--from-scratch", "-s", path]
        logging.info(f"[Watcher] Command: {' '.join(cmd)}")
        with open(f"{LOGS_PATH}/beets.log", "a") as beet_log:
            subprocess.run(cmd, check=True, stdout=beet_log, stderr=beet_log)

def run_beet_web_in_background():
    """
    Run the Beets web plugin in a separate thread to start the web interface.
    """
    def run_web():
        try:
            subprocess.run(["beet", "-vvvvv", "-c", BEETS_CONFIG_TEMP, "web"], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to start Beets web interface: {e}")

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

def main():
    handler = FolderHandler()
    observer = Observer()
    observer.schedule(handler, UNSORTED_DIR, recursive=True)
    observer.start()
    logging.info(f"[Watcher] Listening for new items in: {UNSORTED_DIR} ...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_beet_web_in_background()
    main()
