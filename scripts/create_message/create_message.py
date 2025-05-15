import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
import shutil
import logging
import hashlib
import psycopg

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env.local'
load_dotenv(dotenv_path=env_path)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Database connection configuration
DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DATABASE_NAME"),
    'user': os.getenv("POSTGRES_DATABASE_USER"),
    'password': os.getenv("POSTGRES_DATABASE_PASSWORD"),
    'host': os.getenv("POSTGRES_DATABASE_HOST"),
    'port': os.getenv("POSTGRES_DATABASE_PORT")
}

# Folder paths
OUTBOX_FOLDER = script_dir.parent.parent / 'inbox'  # configurable outbox
ARCHIVE_FOLDER = script_dir / 'archive'      # now local to the script folder
NEW_MESSAGE_FILE = script_dir / 'new_message.yaml'

def get_timestamp_slug():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

def load_new_message():
    if not NEW_MESSAGE_FILE.exists():
        raise FileNotFoundError(f"{NEW_MESSAGE_FILE} does not exist.")
    with open(NEW_MESSAGE_FILE, 'r') as f:
        data = yaml.safe_load(f)
    return data

# Implementing a way to prevent the same exact message being sent twice. Ignores cre
def get_message_hash(message_data):
    """Create a hash of the message data (excluding created_at)."""
    data_to_hash = {k: v for k, v in message_data.items() if k != 'created_at'}
    return hashlib.sha256(yaml.dump(data_to_hash, sort_keys=True).encode()).hexdigest()


def is_duplicate_message(message_data):
    """Check if a similar message already exists in the archive."""
    current_hash = get_message_hash(message_data)
    if not ARCHIVE_FOLDER.exists():
        return False

    for file in ARCHIVE_FOLDER.glob('*.yaml'):
        try:
            with open(file, 'r') as f:
                archived_data = yaml.safe_load(f)
            if get_message_hash(archived_data) == current_hash:
                logging.info(f"Duplicate message found in archive: {file.name}")
                return True
        except Exception as e:
            logging.warning(f"Could not read {file.name}: {e}")
            continue
    return False

def insert_message(conn, data):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO message (
                message, created_by, created_at, site_uuid, host,
                host_site_id, host_sensor_id, trigger_type,
                target_channels, site_lat, site_long, tags
            ) VALUES (
                %(message)s, %(created_by)s, %(created_at)s, %(site_uuid)s, %(host)s,
                %(host_site_id)s, %(host_sensor_id)s, %(trigger_type)s,
                %(target_channels)s, %(site_lat)s, %(site_long)s, %(tags)s
            )
        """, data)
        conn.commit()

def write_yaml_file(data, directory=OUTBOX_FOLDER, archive=True):
    os.makedirs(directory, exist_ok=True)
    # Local?
    # timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    # UTC 
    timestamp = datetime.now(timezone.utc).isoformat()
    filename = f"alert_{get_timestamp_slug()}.yaml"
    file_path = directory / filename

    with open(file_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)
    logging.info(f"YAML alert written to outbox: {file_path}")

    if archive:
        os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
        archived_path = ARCHIVE_FOLDER / filename
        shutil.copy2(file_path, archived_path)
        logging.info(f"Archived copy written to {archived_path}")

def main():
    try:
        message_data = load_new_message()
        message_data['created_at'] = datetime.now(timezone.utc)  # Set runtime timestamp

        if is_duplicate_message(message_data):
            logging.info("No new message written; duplicate detected in archive.")
            return

        with psycopg.connect(**DB_CONFIG) as conn:
            insert_message(conn, message_data)
            write_yaml_file(message_data)
            logging.info("Message written to database and outbox.")
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == '__main__':
    main()