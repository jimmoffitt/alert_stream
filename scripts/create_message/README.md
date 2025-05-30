# What is this thing? 

A helper script for generating alert messages. 

Mimics a system that writes files or makes database inserts when new data arrives.

## How does it work? 

Reads in the `new_message.yaml` as a template for an 'alert' message. 

```python
NEW_MESSAGE_FILE = script_dir / 'new_message.yaml'
```

Reads database connection details from a local `.env.local` configuration file. 


This script can:
* Write a file to a specified directory.

```python
OUTBOX_FOLDER = script_dir.parent.parent / 'inbox'  # configurable outbox
ARCHIVE_FOLDER = script_dir / 'archive'      # now local to the script folder
```

* Insert a new entry into a Postgres database. Database connection details are read fom the .env.local file. 

## Usage

```bash
>python3 create_message.py --file --db
```
