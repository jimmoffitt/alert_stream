# JSON objects

Here are the types of objects this project works with. These are grounded on the fundamentals of posting weather alerts for a location. 

### Rain intensity report

```json
{   "key":"",
    "received_time": "",
    "created_at": "",
    "rain": {
        "m15": 0,
        "m30": 0,
        "h1": 0,
        "h3": 0,
        "h6": 0,
        "h12": 0,
        "h24": 0,
        "d3": 0.08,
        "d7": 0.08,
        "d14": 0.16,
        "d30": 0.31
    }
}
```

### Location metadata
```json
{
	"key": "",
	"properties": {
		"name": "Red Rocks amphitheater",
		"lat": 0,
		"long": 0,
		"state": "CO",
		"timezone": "US-Mountain",
		"utc_offset_std": -7,
		"host": "",
		"site_id": 2850,
		"shef": "BYOC2",
		"last_report": "2025-01-28T11:00:00",
		"created_at": "2025-01-20T05:34:13",
		"data_start": ""
	}
}
```

# POCs

## Basestation to Bluesky

### Goal
A simple command-line Python script that takes a message and posts its contents to Bluesky. 

```python
post_to_bluesky.py -message "example_msg.yaml" -settings "settings.yaml"
```
*Example message*:

A simple YAML file path is passed into the script and that YAML object includes a `message` attribute that is passed to the Bluesky API. Everything in this Bluesky should be treated as public data. 

```yaml
message: "Red Rocks Park 30-day rain total: 0.71 inches #RainData #30Day #COWx #MHFD"
created_by: "Base station"
created_at: "2024-07-05T17:30:07+07:00" 
sent_at: "2024-07-05T17:30:38+07:00"  
host: "local_flood_monitoring_district"
host_site_id: 2500
target_channel: "bluesky"
```
It can handle multiple files and can be set up to monitor a folder and trigger a post for each. 

## Check for Bluesky Alerts

### Goal

A simple command-line Python script that continuously monitors a folder for new files, and when one is found, it is posted to Bluesky.


## Notes:


### Configuration 

Still working out the details, splitting settings into three types:
* Environment variables: Private (not shared) credentials, keys, secrets, etc.

Currently, the BlueskyPoster class assumes there is a local .env.local with these settings:
```bash
    BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
    BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")
    BLUESKY_PDS_URL = os.getenv("BLUESKY_PDS_URL")
```



* Shared app configurations: Things like the check interval, paths, etc.
* Things that users may want to change on the fly for testing and now convinience. There may be a `verbose` flag for debugging purposes.
