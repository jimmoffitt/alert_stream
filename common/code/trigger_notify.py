import time
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
import json

from dotenv import load_dotenv

import asyncio

# Now you can import the BlueskyPoster class
from bluesky_poster import BlueskyPoster

# Get the directory of the current script
script_dir = Path(__file__).parent 
# Construct the path to .env.local within the script's directory
env_path = script_dir / '.env.local'
load_dotenv(dotenv_path=env_path)

# Assume you have some configuration data
class ClientConfig:
    def __init__(self):
        # Add your configuration parameters here
        self.message = ''
        self.host = ''
        self.site_lat = 0.0
        self.site_long = 0.0
        self.target_channels = ''
        self.alert_source = ''
        self.tags = []
        self.uuid = 0
        self.host_site_id = 0
        self.host_sensor_id = 0
        self.created_by = ''
        self.created_at = datetime(year=0, month=1, day=1, hour=0, minute=0, second=0)

class Alert:
    """
    Base class for handling alerts. Subclasses will implement specific
    methods for checking and processing alerts from different sources.
    """

    def __init__(self):
        self.message = ''
        self.host = ''
        self.site_lat = 0.0
        self.site_long = 0.0
        self.target_channels = ''
        self.tags = []
        self.uuid = 0
        self.host_site_id = 0
        self.host_sensor_id = 0
        self.created_by = ''
        self.trigger_type = ''
        self.alert_source = ''
        self.created_at = datetime(year=0, month=1, day=1, hour=0, minute=0, second=0)

    def check_for_alerts(self):
        raise NotImplementedError("Subclasses must implement check_for_alerts")

    def process_alert(self, message):
        raise NotImplementedError("Subclasses must implement process_alert")


    def yaml_to_json(yaml_data):
       
        try:
            if yaml_data is not None:
                json_data = json.dumps(yaml_data)
                return json_data

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
class DatabaseAlert(Alert):

    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    
    def __init__(self, alert_source):
        self.trigger_type = 'database'

        self.host = ''
        self.alert_table = ''

        pass

    def check_for_alerts(self):
        print(f"Checking for new database alerts.")

    def process_alert(self, filepath, message):
        print(f"Processing new database alerts.")

class FileAlert(Alert):
    """
    Handles alerts that are triggered by the presence of files in a directory.
    """

    # Define the alert folder relative to the script's location
    # TODO: This 'inbox' needs to be configurable.
    ALERT_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'inbox')
    FAILED_FOLDER = os.path.join(ALERT_FOLDER, 'failed')
    SENT_FOLDER = os.path.join(ALERT_FOLDER, 'sent')

    def __init__(self):

        self.trigger_type = 'file'
        self.alert_source = self.ALERT_FOLDER
        self.created_at = datetime.now(timezone.utc)  # Set created_at to UTC now


        self._ensure_folders_exist()

    def _ensure_folders_exist(self):
        if not os.path.exists(self.alert_source):
            os.makedirs(self.alert_source)
            print(f"Created alert folder: {self.alert_source}")
        if not os.path.exists(self.FAILED_FOLDER):
            os.makedirs(self.FAILED_FOLDER)
            print(f"Created failed alert folder: {self.FAILED_FOLDER}")
        if not os.path.exists(self.SENT_FOLDER):
            os.makedirs(self.SENT_FOLDER)
            print(f"Created sent alert folder: {self.SENT_FOLDER}")

    def check_for_alerts(self):
        try:
            
            # How do we identify Alert files? 
            # TODO: Should be configurable. 
            # startswith(alert_)
            # endswith(_alert)
            # file extension = yaml
            
            alert_files = [f for f in os.listdir(self.alert_source) if f.startswith('alert_')]

            for filename in alert_files:
                print(f"File alert detected in {self.alert_source})")
                yaml_file_path = os.path.join(self.alert_source, filename)
                try:
                    with open(yaml_file_path, 'r') as yaml_file:
                        yaml_data = yaml.safe_load(yaml_file)

                        if yaml_data is not None:
                            alert_json = yaml_data
                            print(alert_json)

                            self.process_alert(alert_json, filename)

                except FileNotFoundError:
                    print(f"Error: File not found at '{yaml_file_path}'.")
                    return None
                except yaml.YAMLError as e:
                    print(f"Error parsing YAML in '{yaml_file_path}': {e}")
                    return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def process_alert(self, alert_json, filename):
        """Passes the alert message to the configured notification system."""
        
        try:
            message = self.notification_system.build_message(alert_json)

            # TODO: remove
            message = message + "\n\n (File-based triggers is working...)"
            
            # TODO: uncomment
            self.notification_system.send_notification(message)

            # Construct the full source path
            source_path = os.path.join(self.alert_source, filename)
            destination_path = os.path.join(self.SENT_FOLDER, filename)
            self._move_file(source_path, destination_path)
                            
        except Exception as e:
            print(f"Error sending notification for '{filename}': {e}")
            self._move_file(filename, self.FAILED_FOLDER)

    def _move_file(self, source, destination):
        """Moves a file from the source to the destination."""
        try:
            os.rename(source, destination)
            print(f"Moved '{os.path.basename(source)}' to '{os.path.basename(destination)}'")
        except Exception as e:
            print(f"Error moving '{os.path.basename(source)}' to '{os.path.basename(destination)}': {e}")

class Notification:
    """
    Base class for sending notifications. Subclasses will implement specific
    methods for sending notifications through different channels.
    """
    def send_notification(self, message):
        raise NotImplementedError("Subclasses must implement send_notification")
    
    def build_message(self):
        raise NotImplementedError("Subclasses must implement build_message")

class SMSNotification(Notification):
    def send_notification(self, message):
        pass

class EMailNotification(Notification):
    def send_notification(self, message):
        pass

class BlueskyNotification(Notification):
    """
    Sends notifications via Bluesky using the BlueskyPoster.
    """
    # Load from .env file.
    BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
    BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")
    BLUESKY_PDS_URL = os.getenv("BLUESKY_PDS_URL")

    def __init__(self, pds_url=BLUESKY_PDS_URL, handle=BLUESKY_HANDLE, password=BLUESKY_PASSWORD):
        if not all([pds_url, handle, password]):
            raise ValueError("Bluesky PDS URL, handle, and password must be set in the .env file.")
        self.poster = BlueskyPoster(pds_url, handle, password)

    def build_message(self, alert_json):
        """
        Creates a Bluesky message string from the attributes in the JSON data.

        Args:
            json_data (dict): The dictionary representing the loaded JSON data.

        Returns:
            str: The formatted Bluesky message.
        """

        message = ''

        # TODO: this code is a train wreck. 
        # TODO: sort out timezones, and go with UTC. 
        # Try to parse the created_at timestamp and format it

        message_content = alert_json.get('message', 'No message content available.')
        created_at = alert_json.get('created_at', 'Timestamp not available.')

        if created_at == 'now' or created_at == 'YYYY-MM-DD HH:mm:ss' or created_at == '' or created_at == 0:
            now_utc = datetime.now(timezone.utc)
            created_at = now_utc.strftime('%Y-%m-%dT%H:%M:%S+00:00')

        formatted_time = created_at

        host = alert_json.get('host', 'Unknown host')
        site_id = alert_json.get('host_site_id', 'N/A')
        sensor_id = alert_json.get('host_sensor_id', 'N/A')
        tags = alert_json.get('tags', [])
        tags_string = ' '.join(['#' + tag for tag in tags]) if tags else ''

        # Initial message with site and sensor IDs
        message = (
            f"{message_content}\n\n"
            f"Generated by: {host} at {formatted_time} UTC\n"
            f"(Site ID: {site_id}, Sensor ID: {sensor_id})\n"
            f"{tags_string}"
        ).strip()

        if len(message) <= 300:
            return message
        else:
            # Truncate by removing site and sensor IDs
            truncated_message = (
                f"{message_content}\n\n"
                f"Generated by: {host} at {formatted_time}\n"
                f"{tags_string}"
            ).strip()

        if len(truncated_message) <= 300:
            return truncated_message
        else:
            # If still too long, further truncate the original message content
            remaining_length = 300 - (len(f"\n\nGenerated by: {host} at {formatted_time}\n{tags_string}") + 3) # +3 for ellipsis
            truncated_content = message_content[:max(0, remaining_length)] + "..."
            final_truncated_message = (
                f"{truncated_content}\n\n"
                f"Generated by: {host} at {formatted_time}\n"
                f"{tags_string}"
            ).strip()
            return final_truncated_message

    def send_notification(self, message):
        try:

            config = {}
            config['handle'] = self.BLUESKY_HANDLE
            config['password'] = self.BLUESKY_PASSWORD
            config['pds_url'] = self.BLUESKY_PDS_URL
            config['media_folder'] = ''
        
            if not (config['handle'] and config['password']):
                print("both handle and password are required", file=sys.stderr)
                sys.exit(-1)

            # Run the asynchronous create_post method using asyncio.run
            asyncio.run(self.poster.create_post(config, message))
            print(f"Bluesky notification sent: {message}")
        except Exception as e:
            raise Exception(f"Error sending Bluesky notification: {e}")

def main_loop(alert_system, interval=1):
    """Main loop to periodically check for and process alerts."""
    print("Alert monitoring started...")
    while True:
        alert_system.check_for_alerts()
        print(f"Checked for alerts, sleeping for {interval} seconds.")
        time.sleep(interval)

if __name__ == "__main__":
    # Instantiate the specific alert and notification systems
    try:
        bluesky_notifier = BlueskyNotification()
        file_alerter = FileAlert()

        # Inject the notification system into the alert system
        file_alerter.notification_system = bluesky_notifier

        # Start the main loop with the configured alert system
        main_loop(file_alerter)

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")