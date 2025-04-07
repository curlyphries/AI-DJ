import requests
import base64
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NavidromeClient:
    """Client for interacting with the Navidrome API."""
    
    def __init__(self, base_url, username, password):
        """Initialize the Navidrome client.
        
        Args:
            base_url (str): The base URL of the Navidrome server
            username (str): Navidrome username
            password (str): Navidrome password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = None
        
        # Authenticate on initialization
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with the Navidrome server and get a token."""
        try:
            auth_url = f"{self.base_url}/rest/auth.createToken"
            auth_data = {
                "u": self.username,
                "p": self.password,
                "v": "1.16.1",  # Subsonic API version
                "c": "ai-dj",   # Client name
                "f": "json"     # Response format
            }
            
            response = requests.get(auth_url, params=auth_data)
            response.raise_for_status()
            
            data = response.json()
            if 'subsonic-response' in data and data['subsonic-response']['status'] == 'ok':
                self.token = data['subsonic-response']['token']
                salt = data['subsonic-response']['salt']
                
                # Store token and set expiry (24 hours from now)
                self.token = self.token
                self.token_expiry = datetime.now().timestamp() + 86400  # 24 hours
                
                logger.info("Successfully authenticated with Navidrome")
                return True
            else:
                error = data.get('subsonic-response', {}).get('error', {}).get('message', 'Unknown error')
                logger.error(f"Authentication failed: {error}")
                raise Exception(f"Authentication failed: {error}")
        
        except Exception as e:
            logger.error(f"Error authenticating with Navidrome: {str(e)}")
            raise
    
    def _check_token(self):
        """Check if the token is valid and refresh if needed."""
        if not self.token or datetime.now().timestamp() > self.token_expiry:
            logger.info("Token expired or not set, re-authenticating")
            self._authenticate()
    
    def _make_request(self, endpoint, params=None, method='GET'):
        """Make a request to the Navidrome API.
        
        Args:
            endpoint (str): API endpoint to call
            params (dict, optional): Query parameters
            method (str, optional): HTTP method (GET, POST, etc.)
            
        Returns:
            dict: Response data
        """
        self._check_token()
        
        if params is None:
            params = {}
        
        # Add authentication parameters
        params.update({
            "u": self.username,
            "t": self.token,
            "s": "ai-dj",  # Salt
            "v": "1.16.1",  # Subsonic API version
            "c": "ai-dj",   # Client name
            "f": "json"     # Response format
        })
        
        url = f"{self.base_url}/rest/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, data=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            if 'subsonic-response' in data and data['subsonic-response']['status'] == 'ok':
                return data['subsonic-response']
            else:
                error = data.get('subsonic-response', {}).get('error', {}).get('message', 'Unknown error')
                logger.error(f"API request failed: {error}")
                raise Exception(f"API request failed: {error}")
        
        except Exception as e:
            logger.error(f"Error making request to Navidrome: {str(e)}")
            raise
    
    def get_playlists(self):
        """Get all playlists from Navidrome.
        
        Returns:
            list: List of playlist objects
        """
        try:
            response = self._make_request("getPlaylists")
            playlists = response.get('playlists', {}).get('playlist', [])
            return playlists
        except Exception as e:
            logger.error(f"Error getting playlists: {str(e)}")
            raise
    
    def get_playlist(self, playlist_id):
        """Get a specific playlist by ID.
        
        Args:
            playlist_id (str): ID of the playlist
            
        Returns:
            dict: Playlist object with songs
        """
        try:
            response = self._make_request("getPlaylist", {"id": playlist_id})
            playlist = response.get('playlist', {})
            return playlist
        except Exception as e:
            logger.error(f"Error getting playlist {playlist_id}: {str(e)}")
            raise
    
    def create_playlist(self, name, songs=None):
        """Create a new playlist.
        
        Args:
            name (str): Name of the playlist
            songs (list, optional): List of song IDs to add to the playlist
            
        Returns:
            str: ID of the created playlist
        """
        try:
            # Create empty playlist
            response = self._make_request("createPlaylist", {"name": name}, method="POST")
            playlist_id = response.get('playlist', {}).get('id')
            
            # Add songs if provided
            if songs and playlist_id:
                song_ids = ",".join(songs)
                self._make_request("updatePlaylist", {
                    "playlistId": playlist_id,
                    "songId": song_ids
                }, method="POST")
            
            return playlist_id
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            raise
    
    def get_recent_plays(self, limit=20):
        """Get recently played songs.
        
        Args:
            limit (int, optional): Maximum number of songs to return
            
        Returns:
            list: List of recently played songs
        """
        try:
            response = self._make_request("getAlbumList", {
                "type": "recent",
                "size": limit
            })
            
            albums = response.get('albumList', {}).get('album', [])
            recent_songs = []
            
            # For each album, get the songs
            for album in albums:
                album_id = album.get('id')
                if album_id:
                    album_response = self._make_request("getAlbum", {"id": album_id})
                    songs = album_response.get('album', {}).get('song', [])
                    recent_songs.extend(songs)
            
            # Limit to the requested number
            return recent_songs[:limit]
        except Exception as e:
            logger.error(f"Error getting recent plays: {str(e)}")
            raise
    
    def get_song_info(self, song_id):
        """Get detailed information about a song.
        
        Args:
            song_id (str): ID of the song
            
        Returns:
            dict: Song information
        """
        try:
            response = self._make_request("getSong", {"id": song_id})
            song = response.get('song', {})
            return song
        except Exception as e:
            logger.error(f"Error getting song info for {song_id}: {str(e)}")
            raise
    
    def get_album_info(self, album_id):
        """Get detailed information about an album.
        
        Args:
            album_id (str): ID of the album
            
        Returns:
            dict: Album information with songs
        """
        try:
            response = self._make_request("getAlbum", {"id": album_id})
            album = response.get('album', {})
            return album
        except Exception as e:
            logger.error(f"Error getting album info for {album_id}: {str(e)}")
            raise
    
    def search(self, query, search_type="song", limit=20):
        """Search for songs, albums, or artists.
        
        Args:
            query (str): Search query
            search_type (str, optional): Type of search (song, album, artist)
            limit (int, optional): Maximum number of results
            
        Returns:
            list: Search results
        """
        try:
            response = self._make_request("search3", {
                "query": query,
                "songCount": limit if search_type == "song" else 0,
                "albumCount": limit if search_type == "album" else 0,
                "artistCount": limit if search_type == "artist" else 0
            })
            
            search_result = response.get('searchResult3', {})
            
            if search_type == "song":
                return search_result.get('song', [])
            elif search_type == "album":
                return search_result.get('album', [])
            elif search_type == "artist":
                return search_result.get('artist', [])
            else:
                return search_result
        except Exception as e:
            logger.error(f"Error searching for {query}: {str(e)}")
            raise
