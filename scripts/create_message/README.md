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
## **Alert** message object

Here is an example of a `message` object and its attributes. Some of these are parsed and arranged for public messages. When these are written to a database, by default, they are written to a `message` table with these same attributes as fields. 

```yaml
message: 'Building an example for the repo's README. '
created_by: someone writing code
created_at: 2025-05-30 04:18:54.396106+00:00
site_uuid: 1
host: Test
host_site_id: 100
host_sensor_id: 100
trigger_type: file
target_channels: bluesky
site_lat: 142795
site_long: -378738
tags:
- development
- testing
- API
```

Here is the SQL command for creating the corresponding database table: 

```sql
create table message (
  id serial primary key,
  message text not null,
  created_by text not null,
  created_at timestamp not null,
  site_uuid integer,
  host text,
  host_site_id integer,
  host_sensor_id integer,
  trigger_type text,
  target_channels text,
  site_lat double precision,
  site_long double precision,
  tags text[]
);

```

```
