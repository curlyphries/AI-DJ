import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

logger = logging.getLogger(__name__)

class SpotifyClient:
    """Client for interacting with the Spotify API."""
    
    def __init__(self, client_id, client_secret):
        """Initialize the Spotify client.
        
        Args:
            client_id (str): Spotify client ID
            client_secret (str): Spotify client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Initialize the Spotify client
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            logger.info("Spotify client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Spotify client: {str(e)}")
            self.sp = None
    
    def get_trending_tracks(self, limit=10, country='US'):
        """Get trending tracks from Spotify.
        
        Args:
            limit (int, optional): Maximum number of tracks to return
            country (str, optional): Country code to get trends for
            
        Returns:
            list: List of trending tracks
        """
        try:
            if not self.sp:
                raise Exception("Spotify client not initialized")
            
            # Get featured playlists
            featured_playlists = self.sp.featured_playlists(
                country=country,
                limit=5
            )
            
            trending_tracks = []
            
            # Get tracks from featured playlists
            for playlist in featured_playlists['playlists']['items']:
                playlist_id = playlist['id']
                playlist_tracks = self.sp.playlist_tracks(
                    playlist_id,
                    limit=limit // 5  # Divide limit among playlists
                )
                
                for item in playlist_tracks['items']:
                    track = item['track']
                    
                    if track and 'name' in track and 'artists' in track:
                        artist_name = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                        
                        trending_tracks.append({
                            'artist': artist_name,
                            'title': track['name'],
                            'popularity': track.get('popularity', 0),
                            'album': track.get('album', {}).get('name', ''),
                            'source': 'spotify',
                            'playlist': playlist['name']
                        })
            
            # Get tracks from charts (Top 50)
            try:
                charts_playlist_id = f"37i9dQZEVXbLRQDuF5jeBp"  # US Top 50
                if country and country != 'US':
                    # Try to get country-specific playlist
                    results = self.sp.search(f"Top 50 {country}", type='playlist', limit=1)
                    if results and 'playlists' in results and 'items' in results['playlists'] and results['playlists']['items']:
                        charts_playlist_id = results['playlists']['items'][0]['id']
                
                charts_tracks = self.sp.playlist_tracks(
                    charts_playlist_id,
                    limit=limit // 2
                )
                
                for item in charts_tracks['items']:
                    track = item['track']
                    
                    if track and 'name' in track and 'artists' in track:
                        artist_name = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                        
                        trending_tracks.append({
                            'artist': artist_name,
                            'title': track['name'],
                            'popularity': track.get('popularity', 0),
                            'album': track.get('album', {}).get('name', ''),
                            'source': 'spotify',
                            'playlist': 'Top 50'
                        })
            except Exception as e:
                logger.error(f"Error getting charts playlist: {str(e)}")
            
            # Deduplicate and limit results
            seen = set()
            unique_tracks = []
            
            for track in trending_tracks:
                key = f"{track['artist']} - {track['title']}"
                if key not in seen:
                    seen.add(key)
                    unique_tracks.append(track)
                    if len(unique_tracks) >= limit:
                        break
            
            return unique_tracks[:limit]
        
        except Exception as e:
            logger.error(f"Error getting trending tracks from Spotify: {str(e)}")
            return []
    
    def search_track(self, query, limit=10):
        """Search for tracks on Spotify.
        
        Args:
            query (str): Search query
            limit (int, optional): Maximum number of tracks to return
            
        Returns:
            list: List of matching tracks
        """
        try:
            if not self.sp:
                raise Exception("Spotify client not initialized")
            
            results = self.sp.search(q=query, type='track', limit=limit)
            
            tracks = []
            
            for item in results['tracks']['items']:
                artist_name = item['artists'][0]['name'] if item['artists'] else 'Unknown Artist'
                
                tracks.append({
                    'artist': artist_name,
                    'title': item['name'],
                    'popularity': item.get('popularity', 0),
                    'album': item.get('album', {}).get('name', ''),
                    'source': 'spotify',
                    'id': item['id'],
                    'preview_url': item.get('preview_url', None)
                })
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error searching for track '{query}' on Spotify: {str(e)}")
            return []
    
    def get_track_features(self, track_id):
        """Get audio features for a track.
        
        Args:
            track_id (str): Spotify track ID
            
        Returns:
            dict: Audio features
        """
        try:
            if not self.sp:
                raise Exception("Spotify client not initialized")
            
            features = self.sp.audio_features(track_id)[0]
            
            return {
                'danceability': features.get('danceability', 0),
                'energy': features.get('energy', 0),
                'key': features.get('key', 0),
                'loudness': features.get('loudness', 0),
                'mode': features.get('mode', 0),
                'speechiness': features.get('speechiness', 0),
                'acousticness': features.get('acousticness', 0),
                'instrumentalness': features.get('instrumentalness', 0),
                'liveness': features.get('liveness', 0),
                'valence': features.get('valence', 0),
                'tempo': features.get('tempo', 0),
                'duration_ms': features.get('duration_ms', 0),
                'time_signature': features.get('time_signature', 4)
            }
        
        except Exception as e:
            logger.error(f"Error getting audio features for track {track_id}: {str(e)}")
            return {}
    
    def get_artist_top_tracks(self, artist_name, country='US', limit=10):
        """Get top tracks for an artist.
        
        Args:
            artist_name (str): Name of the artist
            country (str, optional): Country code
            limit (int, optional): Maximum number of tracks to return
            
        Returns:
            list: List of top tracks
        """
        try:
            if not self.sp:
                raise Exception("Spotify client not initialized")
            
            # Search for the artist
            results = self.sp.search(q=f"artist:{artist_name}", type='artist', limit=1)
            
            if not results['artists']['items']:
                logger.warning(f"Artist '{artist_name}' not found on Spotify")
                return []
            
            artist_id = results['artists']['items'][0]['id']
            
            # Get top tracks
            top_tracks = self.sp.artist_top_tracks(artist_id, country=country)
            
            tracks = []
            
            for track in top_tracks['tracks'][:limit]:
                tracks.append({
                    'artist': artist_name,
                    'title': track['name'],
                    'popularity': track.get('popularity', 0),
                    'album': track.get('album', {}).get('name', ''),
                    'source': 'spotify',
                    'id': track['id'],
                    'preview_url': track.get('preview_url', None)
                })
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error getting top tracks for artist '{artist_name}': {str(e)}")
            return []
    
    def get_recommendations(self, seed_tracks=None, seed_artists=None, seed_genres=None, limit=10):
        """Get track recommendations based on seeds.
        
        Args:
            seed_tracks (list, optional): List of Spotify track IDs
            seed_artists (list, optional): List of Spotify artist IDs
            seed_genres (list, optional): List of genres
            limit (int, optional): Maximum number of recommendations to return
            
        Returns:
            list: List of recommended tracks
        """
        try:
            if not self.sp:
                raise Exception("Spotify client not initialized")
            
            # Ensure we have at least one seed
            if not seed_tracks and not seed_artists and not seed_genres:
                logger.warning("No seeds provided for recommendations")
                return []
            
            # Limit seeds to 5 total (Spotify API requirement)
            seed_tracks = seed_tracks[:5] if seed_tracks else []
            seed_artists = seed_artists[:5 - len(seed_tracks)] if seed_artists else []
            seed_genres = seed_genres[:5 - len(seed_tracks) - len(seed_artists)] if seed_genres else []
            
            recommendations = self.sp.recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres,
                limit=limit
            )
            
            tracks = []
            
            for track in recommendations['tracks']:
                artist_name = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                
                tracks.append({
                    'artist': artist_name,
                    'title': track['name'],
                    'popularity': track.get('popularity', 0),
                    'album': track.get('album', {}).get('name', ''),
                    'source': 'spotify',
                    'id': track['id'],
                    'preview_url': track.get('preview_url', None)
                })
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
