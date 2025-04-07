import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Import custom modules
from utils.config import Config
from utils.navidrome import NavidromeClient
from integrations.openai_client import OpenAIClient
from integrations.elevenlabs_client import ElevenLabsClient
from integrations.lastfm_client import LastFMClient
from integrations.spotify_client import SpotifyClient
from integrations.reddit_client import RedditClient
from server.routes.dj_announcements import dj_announcements
from server.routes.dj_interaction import dj_interaction, init_clients as init_dj_interaction
from server.routes.music_selection import music_selection
from server.routes.settings import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(dj_announcements, url_prefix='/api')
app.register_blueprint(dj_interaction, url_prefix='/api')
app.register_blueprint(music_selection, url_prefix='/api')
app.register_blueprint(settings, url_prefix='/api')

# Initialize configuration
config = Config()

# Initialize clients
try:
    # Initialize OpenAI client
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_client = OpenAIClient(api_key=openai_api_key)
    
    # Initialize ElevenLabs client
    elevenlabs_client = ElevenLabsClient()
    
    # Initialize Navidrome client
    navidrome_url = os.getenv('NAVIDROME_URL')
    navidrome_username = os.getenv('NAVIDROME_USERNAME')
    navidrome_password = os.getenv('NAVIDROME_PASSWORD')
    navidrome_client = NavidromeClient(navidrome_url, navidrome_username, navidrome_password)
    
    # Initialize Last.fm client
    lastfm_api_key = os.getenv('LASTFM_API_KEY')
    lastfm_client = LastFMClient(lastfm_api_key)
    
    # Initialize Spotify client
    spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    spotify_client = SpotifyClient(spotify_client_id, spotify_client_secret)
    
    # Initialize Reddit client
    reddit_client = RedditClient()
    
    # Initialize clients for DJ interaction
    init_dj_interaction(openai_client, elevenlabs_client, navidrome_client)
    
    logger.info("All clients initialized successfully")
except Exception as e:
    logger.error(f"Error initializing clients: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Serve audio files
@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(os.path.join('voicebot', 'outputs'), filename)

@app.route('/api/health')
def health_check():
    """API endpoint for health check."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    """Get all available playlists."""
    try:
        playlists = navidrome_client.get_playlists()
        return jsonify({"playlists": playlists})
    except Exception as e:
        logger.error(f"Error getting playlists: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    """Create a new AI-generated playlist."""
    try:
        data = request.json
        mood = data.get('mood', '')
        theme = data.get('theme', '')
        count = data.get('count', 10)
        
        # Get recent plays from Navidrome
        recent_plays = navidrome_client.get_recent_plays(limit=20)
        
        # Generate playlist with OpenAI
        playlist_data = openai_client.generate_playlist(
            recent_plays=recent_plays,
            mood=mood,
            theme=theme,
            count=count
        )
        
        # Create playlist in Navidrome
        playlist_id = navidrome_client.create_playlist(
            name=playlist_data['name'],
            songs=playlist_data['songs']
        )
        
        # Save playlist metadata locally
        playlist_path = os.path.join('playlists', f"{playlist_id}.json")
        with open(playlist_path, 'w') as f:
            json.dump(playlist_data, f)
        
        return jsonify({
            "success": True,
            "playlist_id": playlist_id,
            "playlist_name": playlist_data['name']
        })
    except Exception as e:
        logger.error(f"Error creating playlist: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/speak', methods=['POST'])
def speak_text():
    """Convert text to speech using ElevenLabs."""
    try:
        data = request.json
        text = data.get('text', '')
        voice_id = data.get('voice_id', config.default_voice_id)
        
        audio_data = elevenlabs_client.text_to_speech(text, voice_id)
        
        # Save audio file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        audio_path = os.path.join('voicebot', 'outputs', f"{timestamp}.mp3")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        
        return jsonify({
            "success": True,
            "audio_path": f"/static/audio/{os.path.basename(audio_path)}"
        })
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trends', methods=['GET'])
def get_music_trends():
    """Get music trends from various sources."""
    try:
        # Get trends from different sources
        lastfm_trends = lastfm_client.get_trending_tracks(limit=10)
        spotify_trends = spotify_client.get_trending_tracks(limit=10)
        reddit_trends = reddit_client.get_music_posts(limit=10)
        
        # Combine and process trends
        all_trends = {
            "lastfm": lastfm_trends,
            "spotify": spotify_trends,
            "reddit": reddit_trends
        }
        
        return jsonify({"trends": all_trends})
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/song_info', methods=['GET'])
def get_song_info():
    """Get detailed information about a song."""
    try:
        song_id = request.args.get('id')
        if not song_id:
            return jsonify({"error": "Song ID is required"}), 400
        
        # Get basic song info from Navidrome
        song_info = navidrome_client.get_song_info(song_id)
        
        # Enrich with AI-generated content
        artist = song_info.get('artist', '')
        title = song_info.get('title', '')
        
        ai_content = openai_client.generate_song_info(
            artist=artist,
            title=title
        )
        
        song_info['ai_content'] = ai_content
        
        return jsonify({"song_info": song_info})
    except Exception as e:
        logger.error(f"Error getting song info: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dj_intro', methods=['POST'])
def generate_dj_intro():
    """Generate a DJ intro for a song or playlist."""
    try:
        data = request.json
        song_info = data.get('song_info', {})
        playlist_name = data.get('playlist_name', '')
        
        # Generate DJ intro text
        intro_text = openai_client.generate_dj_intro(
            song_info=song_info,
            playlist_name=playlist_name
        )
        
        # Convert to speech
        audio_data = elevenlabs_client.text_to_speech(
            intro_text,
            config.default_voice_id
        )
        
        # Save audio file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        audio_path = os.path.join('voicebot', 'outputs', f"intro_{timestamp}.mp3")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
        
        return jsonify({
            "success": True,
            "intro_text": intro_text,
            "audio_path": f"/static/audio/{os.path.basename(audio_path)}"
        })
    except Exception as e:
        logger.error(f"Error generating DJ intro: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/play_song/<song_id>', methods=['POST'])
def play_song(song_id):
    """Play a specific song in Navidrome."""
    try:
        # This would typically send a command to Navidrome to play the song
        # For now, we'll just return success
        return jsonify({
            "success": True,
            "message": f"Playing song {song_id}"
        })
    except Exception as e:
        logger.error(f"Error playing song: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/now_playing', methods=['GET'])
def get_now_playing():
    """Get information about the currently playing song."""
    try:
        # This would typically get the now playing info from Navidrome
        # For now, we'll return a placeholder
        now_playing = None
        
        try:
            with open(os.path.join('logs', 'now_playing.json'), 'r') as f:
                now_playing_data = json.load(f)
                if now_playing_data and len(now_playing_data) > 0:
                    now_playing = now_playing_data[0]
        except:
            pass
        
        return jsonify({
            "playing": now_playing
        })
    except Exception as e:
        logger.error(f"Error getting now playing: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/system_status', methods=['GET'])
def get_system_status():
    """Get system resource usage."""
    try:
        # Read resource data from file
        resources_file = os.path.join('logs', 'resources.json')
        
        if os.path.exists(resources_file):
            with open(resources_file, 'r') as f:
                resources = json.load(f)
                if resources and len(resources) > 0:
                    latest = resources[-1]
                    return jsonify({
                        "cpu_usage": latest.get('cpu_usage', 0),
                        "ram_usage": latest.get('ram_usage', 0),
                        "timestamp": latest.get('timestamp', datetime.now().isoformat())
                    })
        
        # If file doesn't exist or is empty, return defaults
        return jsonify({
            "cpu_usage": 0,
            "ram_usage": 0,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recent_activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity log."""
    try:
        # This would typically read from an activity log
        # For now, we'll return placeholder data
        activities = [
            {
                "type": "song_played",
                "description": "Played 'Example Song' by Example Artist",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "playlist_created",
                "description": "Created playlist 'Example Playlist'",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        return jsonify({
            "activities": activities
        })
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze_trends', methods=['GET'])
def analyze_trends():
    """Analyze music trends and compare with user's taste."""
    try:
        # Get trends
        lastfm_trends = lastfm_client.get_trending_tracks(limit=5)
        spotify_trends = spotify_client.get_trending_tracks(limit=5)
        
        # Get recent plays
        recent_plays = navidrome_client.get_recent_plays(limit=10)
        
        # Combine trends
        all_trends = {
            "lastfm": lastfm_trends,
            "spotify": spotify_trends
        }
        
        # Analyze with OpenAI
        analysis = openai_client.analyze_trends(all_trends, recent_plays)
        
        return jsonify({
            "analysis": analysis
        })
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('playlists', exist_ok=True)
    os.makedirs(os.path.join('voicebot', 'outputs'), exist_ok=True)
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=config.debug_mode)
