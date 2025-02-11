from .bluesky_facets import parse_facets
import os
import sys
import re
import json
from typing import Dict, List
from pathlib import Path
import asyncio
import aiohttp
from datetime import datetime, timezone
from datetime import timedelta
from dotenv import load_dotenv

class BlueskyPoster:
    """
        A class to handle posting and managing sessions with a Bluesky server.
    
        This class provides methods to authenticate, upload images, manage message lengths, and create posts on a Bluesky server.
        This version does not handle video uploads. 
    
        Attributes:
            pds_url (str): The URL of the Bluesky server.
            handle (str): The user handle for authentication.
            password (str): The password for authentication.
            access_jwt (str): The access token for the session.
            did (str): The decentralized identifier for the session.
            session_lock (asyncio.Lock): A lock to manage session creation.
            session (dict): The current session information.
            session_expiry (datetime): The expiry time of the current session.
        """
    def __init__(self, pds_url, handle, password):
        """
        Initializes the instance with server URL, user handle, and password, and sets up session management attributes.
        """
        self.pds_url = pds_url
        self.handle = handle
        self.password = password
        self.access_jwt = None
        self.did = None
        self.session_lock = asyncio.Lock()
        self.session = None
        self.session_expiry = None
    
    async def bsky_login_session(self, pds_url: str, handle: str, password: str) -> Dict:
        """
            Initiates an asynchronous login session with a Bluesky server.
        
            Args:
                pds_url: The URL of the Bluesky server.
                handle: The user handle for login.
                password: The password for login.
        
            Returns:
                A dictionary containing the session data if successful, or None if an error occurs.
            """  # Make bsky_login_session async

        headers = {'Content-Type': 'application/json'}

        try:
            async with aiohttp.ClientSession() as session:  # Use aiohttp for async requests
                resp = await session.post(  # Use await for the async post request
                    pds_url + "/xrpc/com.atproto.server.createSession",
                    json={"identifier": handle, "password": password},
                    headers=headers
                )
                resp.raise_for_status()  # This will raise an exception for 4xx and 5xx status codes
                return await resp.json()  # Use await for async json response
        except aiohttp.ClientError as e:  # Catch aiohttp exceptions
            print(f"An error occurred during the request: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    async def get_or_create_session(self):
        """
        Manages the session lifecycle, creating a new session if none exists or if the current session has expired.
        """  # No config argument needed here
        async with self.session_lock:
            if self.session is None or (self.session_expiry and datetime.now(timezone.utc) > self.session_expiry):
                self.session = await self.bsky_login_session(self.pds_url, self.handle, self.password)  # Use instance attributes
                if self.session is None:
                    print("Authentication failed")
                    return None

                # Assuming the session response includes `accessJwt` and a token expiry time in seconds (if available)
                self.access_jwt = self.session.get("accessJwt")
                self.did = self.session.get("did")
                
                # Set session expiry if token has an expiration field (adjust based on actual API response)
                expiry_seconds = self.session.get("expires_in", 3600)  # Default to 1 hour if unspecified
                self.session_expiry = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)


            return self.session

    async def upload_video(self, config, media_filename):
        """
        Uploads a video to a Bluesky server using com.atproto.repo.uploadBlob.

        Args:
        config: Configuration dictionary containing server details.
        media_path: Path to the video file to be uploaded.

        Returns:
        The blob identifier if the upload is successful, or None if an error occurs.
        """
        media_path = f"{config['media_folder']}/{media_filename}"

        if not os.path.exists(media_path):
            print(f"File does not exist: {media_path}")
            return None
        
        

    async def upload_image(self, config, media_filename):
        """
        Uploads an image to a Bluesky server using com.atproto.repo.uploadBlob.
        
        Args:
        config: Configuration dictionary containing server details.
        media_path: Path to the image file to be uploaded.
        
        Returns:
        The blob identifier if the upload is successful, or None if an error occurs.
        """

        media_path = f"{config['media_folder']}/{media_filename}"

        if not os.path.exists(media_path):
            print(f"File does not exist: {media_path}")
            return None

        try:
            with open(media_path, "rb") as media_file:
                media_bytes = media_file.read()

            if len(media_bytes) > 1000000:
                raise Exception(
                    f"Image file size too large. 1000000 bytes maximum, got: {len(media_bytes)}"
                )

            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    # TODO: what is the recipe for uploading videos to Bluesky?
                    config['pds_url'] + "/xrpc/com.atproto.repo.uploadBlob",
                    headers={
                        "Content-Type": "video/mp4",  # TODO: if similar enough, combine with upload_image method. 
                        "Authorization": "Bearer " + self.access_jwt
                    },
                    data=media_bytes,
                )
                resp.raise_for_status()
                blob = (await resp.json())["blob"] 

            return blob

        except aiohttp.ClientError as e:  # Catch aiohttp exceptions
            print(f"Error uploading image: {e}")
            return None

    def manage_bluesky_message_length(self, message):
        """
        Manages the length of a Bluesky message to keep it under 300 characters.

        Args:
            message: A dictionary representing a message, containing a 'text' key.

        Returns:
            A string with the processed message and addendum, is ready for Bluesky.
        """

        # Create the long and short versions of the addendum
        #long_addendum = f"\n\nPosted at {message['timestamp']} UTC"
        long_addendum = f"\n\nPosted at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
        short_addendum = f"\n\nPosted at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S').split()[0]}"

        #TODO: these are domain-specific and need to be moved upstream

        #mentions? 
        #mention0 = "snowbot"
        #mentions = f"@{mention0}"   
        #message = message + "\n" + mentions

        # TODO: tack on some configured tags
        tag0 = "RainData"
        tag1 = "30Day" 
        tag2 = "COWx"
        tag3 = "Host"
        tags = f"#{tag0} #{tag1} #{tag2} #{tag3}"        
        
        message = message + "\n" + tags

        # Check if the long addendum fits within the character limit
        if len(message + long_addendum) <= 300:
            return message + long_addendum
        else:
            return message + short_addendum

    async def create_post(self, config, message):
        """
        Creates a new post on the Bluesky platform using the provided message metadata and configuration.
        
            Args:
            config: Configuration dictionary containing necessary session and API details.
            message: A dictionary representing the message to be posted.
        
            Returns:
            None
        """
        bsky_session = await self.get_or_create_session()
        if bsky_session is None:
            return

        #config['accessJwt'] = bsky_session["accessJwt"]
        #config['did'] = bsky_session["did"]

        message= self.manage_bluesky_message_length(message)

        # trailing "Z" is preferred over "+00:00"
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Use the parse_facets function to generate facets
        #facets = parse_facets(message['text'] + addendum, self.pds_url)
        facets = parse_facets(message, self.pds_url)

        # these are the required fields which every post must include
        post = {
            # TODO: make general with pds_url
            "$type": "app.bsky.feed.post",
            "text": message,
            "createdAt": now,
            "facets": facets,
        }

        print("post:")
        print(json.dumps(post, indent=2), file=sys.stderr)

        async with aiohttp.ClientSession() as session:  # Create aiohttp ClientSession here
            resp = await session.post(  # Use await for async post
                config['pds_url'] + "/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": "Bearer " + self.access_jwt},
                json={
                    "repo": self.did,
                    "collection": "app.bsky.feed.post",
                    "record": post,
                },
            )
            print("createRecord response:", file=sys.stderr)
            print(json.dumps(await resp.json(), indent=2))  # Use await for async json response
            resp.raise_for_status()
        
async def main():
    """
    Asynchronously loads environment variables, initializes configurations, and posts using BlueskyPoster.
    """

    # Get the directory of the current script
    script_dir = Path(__file__).parent 
    # Construct the path to .env.local within the script's directory
    env_path = script_dir / '.env.local'
    load_dotenv(dotenv_path=env_path)

    # Load from .env file.
    BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE")
    BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD")
    BLUESKY_PDS_URL = os.getenv("BLUESKY_PDS_URL")

    config = {}
    #TODO: figure out .env and overrides.
    config['handle'] = BLUESKY_HANDLE
    config['password'] = BLUESKY_PASSWORD
    config['pds_url'] = BLUESKY_PDS_URL
    config['media_folder'] = ''
        
    if not (config['handle'] and config['password']):
        print("both handle and password are required", file=sys.stderr)
        sys.exit(-1)
    """ if args.image and len(args.image) > 4:
        print("at most 4 images per post", file=sys.stderr)
        sys.exit(-1) """
        
    # Create an instance of BlueskyPoster
    bluesky_poster = BlueskyPoster(config['pds_url'], config['handle'], config['password'])  # Assuming the constructor takes these arguments
    

    async with aiohttp.ClientSession() as session:
        tasks = []
        for item in data:
            # ... (prepare config and message metadata)
            if item['id'] == id:
                message = item
                break

        task = asyncio.create_task(
            #poster.create_post_async(config, message, httpsession)  # Pass the session
            bluesky_poster.create_post(config, message)  # Pass the session
        )
        tasks.append(task)
        await asyncio.sleep(3.6)  # Adjust delay as needed

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
