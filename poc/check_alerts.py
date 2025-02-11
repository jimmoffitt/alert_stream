import os
import time
import yaml
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from BlueskyPoster import BlueskyPoster

# Load configuration from .env.local file
load_dotenv(".env.local")

config = {
    "ALERT_CHECK_INTERVAL": int(os.getenv("ALERT_CHECK_INTERVAL", 5)),  # Default to 5 seconds
    "INBOX_ROOT": os.getenv("INBOX_ROOT", "inbox")
}

# Ensure necessary subfolders exist
INBOX_PATH = Path(config["INBOX_ROOT"])
FAILED_PATH = INBOX_PATH / "failed"
SENT_PATH = INBOX_PATH / "sent"

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
        main()
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    except Exception as e:
        print(f"Fatal error in main execution: {e}")
