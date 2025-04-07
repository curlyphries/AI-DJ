import requests
import logging
import pylast

logger = logging.getLogger(__name__)

class LastFMClient:
    """Client for interacting with the Last.fm API."""
    
    def __init__(self, api_key, api_secret=None, username=None, password_hash=None):
        """Initialize the Last.fm client.
        
        Args:
            api_key (str): Last.fm API key
            api_secret (str, optional): Last.fm API secret
            username (str, optional): Last.fm username
            password_hash (str, optional): Last.fm password hash
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.username = username
        self.password_hash = password_hash
        
        # Initialize the pylast network
        self.network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
        
        # Authenticate if username and password_hash are provided
        if username and password_hash:
            self.network.session_key = pylast.SessionKeyGenerator(self.network).get_session_key(
                username=username,
                password_hash=password_hash
            )
    
    def get_trending_tracks(self, limit=10, country=None):
        """Get trending tracks from Last.fm.
        
        Args:
            limit (int, optional): Maximum number of tracks to return
            country (str, optional): Country code to get trends for
            
        Returns:
            list: List of trending tracks
        """
        try:
            # Get chart tracks
            if country:
                chart = self.network.get_geo_top_tracks(country, limit=limit)
            else:
                chart = self.network.get_top_tracks(limit=limit)
            
            trending_tracks = []
            
            for item in chart:
                track = item.item
                artist = track.artist.name
                title = track.title
                
                # Get additional track info if available
                try:
                    track_info = track.get_info()
                    listeners = track_info.get('listeners', 0)
                    playcount = track_info.get('playcount', 0)
                except:
                    listeners = 0
                    playcount = 0
                
                trending_tracks.append({
                    'artist': artist,
                    'title': title,
                    'listeners': listeners,
                    'playcount': playcount,
                    'source': 'lastfm'
                })
            
            return trending_tracks
        
        except Exception as e:
            logger.error(f"Error getting trending tracks from Last.fm: {str(e)}")
            # Fallback to API request if pylast fails
            return self._get_trending_tracks_api(limit, country)
    
    def _get_trending_tracks_api(self, limit=10, country=None):
        """Fallback method to get trending tracks using direct API requests.
        
        Args:
            limit (int, optional): Maximum number of tracks to return
            country (str, optional): Country code to get trends for
            
        Returns:
            list: List of trending tracks
        """
        try:
            url = "http://ws.audioscrobbler.com/2.0/"
            
            params = {
                "method": "chart.getTopTracks" if not country else "geo.getTopTracks",
                "api_key": self.api_key,
                "format": "json",
                "limit": limit
            }
            
            if country:
                params["country"] = country
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'tracks' in data and 'track' in data['tracks']:
                tracks = data['tracks']['track']
                
                trending_tracks = []
                
                for track in tracks:
                    trending_tracks.append({
                        'artist': track['artist']['name'],
                        'title': track['name'],
                        'listeners': track.get('listeners', 0),
                        'playcount': track.get('playcount', 0),
                        'source': 'lastfm'
                    })
                
                return trending_tracks
            else:
                logger.error("Unexpected response format from Last.fm API")
                return []
        
        except Exception as e:
            logger.error(f"Error getting trending tracks from Last.fm API: {str(e)}")
            return []
    
    def get_artist_info(self, artist_name):
        """Get information about an artist.
        
        Args:
            artist_name (str): Name of the artist
            
        Returns:
            dict: Artist information
        """
        try:
            artist = self.network.get_artist(artist_name)
            
            # Get basic info
            bio = artist.get_bio_summary()
            if bio:
                # Remove HTML tags
                bio = bio.replace('<a href="', '').replace('</a>', '').replace('">', '')
            
            similar = artist.get_similar(limit=5)
            similar_artists = [a.item.name for a in similar]
            
            tags = artist.get_top_tags(limit=5)
            top_tags = [t.item.name for t in tags]
            
            return {
                'name': artist_name,
                'bio': bio,
                'similar_artists': similar_artists,
                'tags': top_tags,
                'source': 'lastfm'
            }
        
        except Exception as e:
            logger.error(f"Error getting artist info for {artist_name}: {str(e)}")
            return {'name': artist_name, 'error': str(e)}
    
    def get_track_info(self, artist_name, track_name):
        """Get information about a track.
        
        Args:
            artist_name (str): Name of the artist
            track_name (str): Name of the track
            
        Returns:
            dict: Track information
        """
        try:
            track = self.network.get_track(artist_name, track_name)
            
            # Get basic info
            try:
                info = track.get_info()
                listeners = info.get('listeners', 0)
                playcount = info.get('playcount', 0)
                duration = info.get('duration', 0)
                url = info.get('url', '')
            except:
                listeners = 0
                playcount = 0
                duration = 0
                url = ''
            
            # Get tags
            try:
                tags = track.get_top_tags(limit=5)
                top_tags = [t.item.name for t in tags]
            except:
                top_tags = []
            
            return {
                'artist': artist_name,
                'title': track_name,
                'listeners': listeners,
                'playcount': playcount,
                'duration': duration,
                'url': url,
                'tags': top_tags,
                'source': 'lastfm'
            }
        
        except Exception as e:
            logger.error(f"Error getting track info for {artist_name} - {track_name}: {str(e)}")
            return {'artist': artist_name, 'title': track_name, 'error': str(e)}
    
    def get_similar_tracks(self, artist_name, track_name, limit=10):
        """Get similar tracks to a given track.
        
        Args:
            artist_name (str): Name of the artist
            track_name (str): Name of the track
            limit (int, optional): Maximum number of similar tracks to return
            
        Returns:
            list: List of similar tracks
        """
        try:
            track = self.network.get_track(artist_name, track_name)
            similar = track.get_similar(limit=limit)
            
            similar_tracks = []
            
            for item in similar:
                t = item.item
                similar_tracks.append({
                    'artist': t.artist.name,
                    'title': t.title,
                    'source': 'lastfm'
                })
            
            return similar_tracks
        
        except Exception as e:
            logger.error(f"Error getting similar tracks for {artist_name} - {track_name}: {str(e)}")
            return []
