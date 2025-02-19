import sys
import os
from pathlib import Path

# Get the directory of the current script
script_dir = Path(__file__).parent.resolve()

# Construct the path to the 'common/code' directory
common_code_dir = script_dir.parent / "common" / "code"

# Add the 'common/code' directory to the Python path
sys.path.append(str(common_code_dir))

# Now you can import the BlueskyPoster class
from bluesky_poster import BlueskyPoster

import time
import yaml
from dotenv import load_dotenv
import argparse
from pathlib import Path
from datetime import datetime

# Load configuration from .env.local file
load_dotenv(".env.local")

# --- Argument parsing ---
parser = argparse.ArgumentParser(description="Process messages and post them to Bluesky")
parser.add_argument("--inbox", help="Path to the inbox folder")
parser.add_argument("--interval", type=int, help="Alert check interval in seconds")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()
# --- End argument parsing ---

# Configuration from environment variables and command-line arguments
# Example of pulling setting from env vars:
#ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", 5))

# Example of pulling settings from command line arguments:
#ALERT_CHECK_INTERVAL = args.alert_check_interval

# Example of reading from a local settings.yaml file: 
settings_path = script_dir / 'settings.yaml'
with open(settings_path, 'r') as f:
    config = yaml.safe_load(f)
    print(config)
    print(config['ALERT_CHECK_INTERVAL'])



# --- Override settings with command-line arguments ---
if args.inbox:
    config["INBOX_ROOT"] = args.inbox
if args.interval:
    config["ALERT_CHECK_INTERVAL"] = args.interval
if args.verbose:
    config["VERBOSE"] = args.verbose

# --- Set defaults if not provided ---
if "INBOX_ROOT" not in config:
    config["INBOX_ROOT"] = "./inbox"
if "ALERT_CHECK_INTERVAL" not in config:
    config["ALERT_CHECK_INTERVAL"] = 5
if "VERBOSE" not in config:
    config["VERBOSE"] = False

ALERT_CHECK_INTERVAL = int(config['ALERT_CHECK_INTERVAL'])

# Ensure necessary subfolders exist
INBOX_PATH = Path(config["INBOX_ROOT"])
FAILED_PATH = INBOX_PATH / "failed"
SENT_PATH = INBOX_PATH / "sent"

# Create folders if they don't exist
for path in [INBOX_PATH, FAILED_PATH, SENT_PATH]:
    path.mkdir(parents=True, exist_ok=True)

def process_message_file(file_path):
    """Processes a single YAML message file."""
    try:
        # Parse the YAML file
        with open(file_path, 'r') as f:
            message_data = yaml.safe_load(f)

        # Validate required fields
        if not isinstance(message_data, dict):
            raise ValueError("Invalid YAML format: expected a dictionary")
        if "timestamp" not in message_data or "message" not in message_data:
            raise ValueError("Missing required fields: 'timestamp' and 'message'")

        # Append alert processing timestamp
        message_data["processed_timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Post the message using BlueskyPoster
        # TODO: create once and reuse: def process_message_file(poster, file_path):
        poster = BlueskyPoster()
      
        poster.create_post(message_data, config)  # Pass message data and config

        # Move the file to the "sent" folder on success
        new_path = SENT_PATH / file_path.name
        file_path.rename(new_path)
        print(f"Message posted successfully and moved to 'sent': {file_path}")

    except (yaml.YAMLError, ValueError) as e:
        print(f"YAML parsing or validation error for {file_path}: {e}")
        new_path = FAILED_PATH / file_path.name
        file_path.rename(new_path)
    except Exception as e:
        print(f"Unexpected error processing {file_path}: {e}")
        new_path = FAILED_PATH / file_path.name
        file_path.rename(new_path)

def main():
    """Main function to monitor the inbox folder and process messages."""
    print("Starting message processor...")
    while True:
        try:
            # Check for YAML files in the inbox
            for file_path in INBOX_PATH.glob("*.yaml"):
                try:
                    process_message_file(file_path)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
        except Exception as e:
            print(f"Critical error during processing loop: {e}")
        
        # Wait before checking again
        try:
            time.sleep(config["ALERT_CHECK_INTERVAL"])
        except Exception as e:
            print(f"Error during sleep interval: {e}")

if __name__ == "__main__":
    try:
        if args.verbose:
            print("Verbose output enabled")
        main()
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    except Exception as e:
        print(f"Fatal error in main execution: {e}")
