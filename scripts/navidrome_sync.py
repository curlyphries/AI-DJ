import os
import json
import logging
import requests
import time
import base64
import hashlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'navidrome_sync.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NavidromeSync:
    """Class to sync data with Navidrome music server."""
    
    def __init__(self, base_url, username, password):
        """Initialize the Navidrome sync client.
        
        Args:
            base_url (str): The base URL of the Navidrome server
            username (str): Navidrome username
            password (str): Navidrome password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.salt = None
        self.token_expiry = None
        
        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('playlists', exist_ok=True)
        
        # Authenticate on initialization
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with the Navidrome server and get a token."""
        try:
            auth_url = f"{self.base_url}/rest/ping"
            
            response = requests.get(auth_url, params={
                "u": self.username,
                "p": self.password,
                "v": "1.16.1",  # Subsonic API version
                "c": "ai-dj",   # Client name
                "f": "json"     # Response format
            })
            
            if response.status_code != 200:
                logger.error(f"Authentication failed with status code {response.status_code}")
                return False
            
            data = response.json()
            if 'subsonic-response' in data and data['subsonic-response']['status'] == 'ok':
                logger.info("Successfully authenticated with Navidrome")
                
                # Get salt and token for further requests
                auth_url = f"{self.base_url}/rest/getUser"
                response = requests.get(auth_url, params={
                    "u": self.username,
                    "p": self.password,
                    "v": "1.16.1",
                    "c": "ai-dj",
                    "f": "json",
                    "username": self.username
                })
                
                if response.status_code == 200:
                    data = response.json()
                    if 'subsonic-response' in data and data['subsonic-response']['status'] == 'ok':
                        # Generate a random salt
                        self.salt = base64.b64encode(os.urandom(8)).decode('utf-8')
                        
                        # Generate token (md5 of password + salt)
                        token = hashlib.md5(f"{self.password}{self.salt}".encode()).hexdigest()
                        self.token = token
                        
                        # Set token expiry (24 hours from now)
                        self.token_expiry = datetime.now() + timedelta(hours=24)
                        
                        return True
            
            logger.error("Failed to get salt and token")
            return False
        
        except Exception as e:
            logger.error(f"Error authenticating with Navidrome: {str(e)}")
            return False
    
    def check_token(self):
        """Check if the token is valid and refresh if needed."""
        if not self.token or not self.salt or datetime.now() > self.token_expiry:
            logger.info("Token expired or not set, re-authenticating")
            return self.authenticate()
        return True
    
    def make_request(self, endpoint, params=None):
        """Make a request to the Navidrome API.
        
        Args:
            endpoint (str): API endpoint to call
            params (dict, optional): Additional parameters
            
        Returns:
            dict: Response data or None if failed
        """
        if not self.check_token():
            return None
        
        if params is None:
            params = {}
        
        # Add authentication parameters
        params.update({
            "u": self.username,
            "t": self.token,
            "s": self.salt,
            "v": "1.16.1",
            "c": "ai-dj",
            "f": "json"
        })
        
        url = f"{self.base_url}/rest/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code {response.status_code}")
                return None
            
            data = response.json()
            if 'subsonic-response' in data and data['subsonic-response']['status'] == 'ok':
                return data['subsonic-response']
            else:
                error = data.get('subsonic-response', {}).get('error', {}).get('message', 'Unknown error')
                logger.error(f"API request failed: {error}")
                return None
        
        except Exception as e:
            logger.error(f"Error making request to Navidrome: {str(e)}")
            return None
    
    def sync_playlists(self):
        """Sync playlists from Navidrome to local storage."""
        logger.info("Syncing playlists from Navidrome...")
        
        response = self.make_request("getPlaylists")
        if not response:
            return False
        
        playlists = response.get('playlists', {}).get('playlist', [])
        
        # Save playlists to local storage
        with open(os.path.join('playlists', 'navidrome_playlists.json'), 'w') as f:
            json.dump(playlists, f, indent=2)
        
        logger.info(f"Synced {len(playlists)} playlists from Navidrome")
        return True
    
    def sync_recent_plays(self, limit=50):
        """Sync recently played songs from Navidrome to local storage."""
        logger.info(f"Syncing recent plays from Navidrome (limit: {limit})...")
        
        # Get recently played albums
        response = self.make_request("getAlbumList", {
            "type": "recent",
            "size": limit
        })
        
        if not response:
            return False
        
        albums = response.get('albumList', {}).get('album', [])
        
        recent_songs = []
        
        # For each album, get the songs
        for album in albums[:10]:  # Limit to 10 albums to avoid too many requests
            album_id = album.get('id')
            if album_id:
                album_response = self.make_request("getAlbum", {"id": album_id})
                if album_response:
                    songs = album_response.get('album', {}).get('song', [])
                    recent_songs.extend(songs)
        
        # Limit to the requested number
        recent_songs = recent_songs[:limit]
        
        # Save recent plays to local storage
        with open(os.path.join('logs', 'recent_plays.json'), 'w') as f:
            json.dump(recent_songs, f, indent=2)
        
        logger.info(f"Synced {len(recent_songs)} recent plays from Navidrome")
        return True
    
    def sync_library_stats(self):
        """Sync library statistics from Navidrome to local storage."""
        logger.info("Syncing library statistics from Navidrome...")
        
        # Get library statistics
        response = self.make_request("getNowPlaying")
        if not response:
            return False
        
        now_playing = response.get('nowPlaying', {}).get('entry', [])
        
        # Save now playing to local storage
        with open(os.path.join('logs', 'now_playing.json'), 'w') as f:
            json.dump(now_playing, f, indent=2)
        
        # Get system status
        response = self.make_request("getUser", {"username": self.username})
        if not response:
            return False
        
        user = response.get('user', {})
        
        # Extract library stats
        library_stats = {
            'albumCount': user.get('albumCount', 0),
            'artistCount': user.get('artistCount', 0),
            'songCount': user.get('songCount', 0),
            'lastScan': datetime.now().isoformat()
        }
        
        # Save library stats to local storage
        with open(os.path.join('logs', 'library_stats.json'), 'w') as f:
            json.dump(library_stats, f, indent=2)
        
        logger.info("Synced library statistics from Navidrome")
        return True
    
    def run_sync(self):
        """Run a full sync of all data from Navidrome."""
        logger.info("Starting full Navidrome sync...")
        
        # Sync playlists
        self.sync_playlists()
        
        # Sync recent plays
        self.sync_recent_plays()
        
        # Sync library stats
        self.sync_library_stats()
        
        logger.info("Full Navidrome sync completed")

def main():
    """Main function to run Navidrome sync."""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get Navidrome settings from environment variables
    navidrome_url = os.getenv('NAVIDROME_URL', 'http://localhost:4533')
    navidrome_username = os.getenv('NAVIDROME_USERNAME', '')
    navidrome_password = os.getenv('NAVIDROME_PASSWORD', '')
    
    if not navidrome_username or not navidrome_password:
        logger.error("Navidrome username or password not set in environment variables")
        return
    
    # Create sync client
    sync_client = NavidromeSync(navidrome_url, navidrome_username, navidrome_password)
    
    # Run initial sync
    sync_client.run_sync()
    
    # Run sync every 15 minutes
    try:
        while True:
            time.sleep(900)  # 15 minutes
            sync_client.run_sync()
    
    except KeyboardInterrupt:
        logger.info("Navidrome sync stopped by user")

if __name__ == "__main__":
    main()
