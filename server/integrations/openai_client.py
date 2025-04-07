import os
import json
import logging
from openai import OpenAI
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with the OpenAI API."""
    
    def __init__(self, api_key):
        """Initialize the OpenAI client.
        
        Args:
            api_key (str): OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        
        # Load prompt templates
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load prompt templates from the prompts directory."""
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts')
        
        if not os.path.exists(prompts_dir):
            os.makedirs(prompts_dir)
            # Create default templates if they don't exist
            self._create_default_templates(prompts_dir)
        
        try:
            for filename in os.listdir(prompts_dir):
                if filename.endswith('.json'):
                    template_name = filename[:-5]  # Remove .json extension
                    with open(os.path.join(prompts_dir, filename), 'r') as f:
                        self.templates[template_name] = json.load(f)
            
            logger.info(f"Loaded {len(self.templates)} prompt templates")
        except Exception as e:
            logger.error(f"Error loading prompt templates: {str(e)}")
    
    def _create_default_templates(self, prompts_dir):
        """Create default prompt templates."""
        default_templates = {
            "playlist_generator": {
                "system": "You are an expert music curator and DJ assistant. Your task is to create a cohesive and engaging playlist based on the user's preferences, recent listening history, and specified mood or theme.",
                "user": "Create a playlist with {count} songs that matches the mood: '{mood}' and theme: '{theme}'. Consider these recently played songs: {recent_plays}. For each song, include the artist name, song title, and a brief reason why it fits the playlist."
            },
            "song_info": {
                "system": "You are a music expert with deep knowledge of artists, genres, music history, and interesting trivia. Provide engaging and accurate information about songs.",
                "user": "Provide interesting information about the song '{title}' by {artist}. Include genre information, historical context, fun facts, and what makes this song special. Keep it concise but engaging, like a DJ might introduce the song."
            },
            "dj_intro": {
                "system": "You are a charismatic DJ introducing the next song or playlist to your audience. Your intros are engaging, informative, and build excitement for the music that's about to play.",
                "user": "Create a DJ introduction for the song '{title}' by {artist} from the playlist '{playlist_name}'. Make it sound natural, engaging, and brief (30-60 words). Include a reference to the mood, genre, or theme of the song."
            },
            "trend_analyzer": {
                "system": "You are a music trend analyst who can identify patterns and connections between different music trends and a user's personal music collection.",
                "user": "Analyze these current music trends: {trends}. Compare them with the user's recent listening: {recent_plays}. Identify connections, recommend songs from trends that match the user's taste, and suggest songs from their collection that align with current trends."
            }
        }
        
        for name, template in default_templates.items():
            with open(os.path.join(prompts_dir, f"{name}.json"), 'w') as f:
                json.dump(template, f, indent=2)
        
        logger.info(f"Created {len(default_templates)} default prompt templates")
    
    def _format_prompt(self, template_name, **kwargs):
        """Format a prompt template with the provided variables.
        
        Args:
            template_name (str): Name of the template to use
            **kwargs: Variables to format the template with
            
        Returns:
            list: Formatted messages for the API call
        """
        if template_name not in self.templates:
            logger.warning(f"Template {template_name} not found, using default")
            return [
                {"role": "system", "content": "You are an AI assistant for a music application."},
                {"role": "user", "content": str(kwargs)}
            ]
        
        template = self.templates[template_name]
        
        # Format the system and user prompts
        system_content = template["system"]
        user_content = template["user"].format(**kwargs)
        
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    
    def generate_playlist(self, recent_plays, mood="", theme="", count=10):
        """Generate a playlist based on recent plays, mood, and theme.
        
        Args:
            recent_plays (list): List of recently played songs
            mood (str, optional): Desired mood for the playlist
            theme (str, optional): Desired theme for the playlist
            count (int, optional): Number of songs to include
            
        Returns:
            dict: Generated playlist with name and songs
        """
        try:
            # Format the recent plays for the prompt
            formatted_plays = []
            for song in recent_plays:
                formatted_plays.append(f"{song.get('artist', 'Unknown Artist')} - {song.get('title', 'Unknown Title')}")
            
            recent_plays_str = ", ".join(formatted_plays)
            
            # Prepare the prompt
            messages = self._format_prompt(
                "playlist_generator",
                recent_plays=recent_plays_str,
                mood=mood,
                theme=theme,
                count=count
            )
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Extract playlist name and songs
            lines = content.strip().split('\n')
            playlist_name = lines[0].strip()
            
            if playlist_name.startswith('# '):
                playlist_name = playlist_name[2:]
            elif playlist_name.startswith('Playlist: '):
                playlist_name = playlist_name[10:]
            
            # Extract songs
            songs = []
            current_song = {}
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('- ') or line.startswith('* '):
                    line = line[2:]
                
                if ' - ' in line:
                    # New song
                    if current_song and 'artist' in current_song and 'title' in current_song:
                        songs.append(current_song)
                    
                    parts = line.split(' - ', 1)
                    current_song = {
                        'artist': parts[0].strip(),
                        'title': parts[1].strip(),
                        'reason': ''
                    }
                elif current_song and 'artist' in current_song:
                    # This is probably the reason
                    current_song['reason'] += line + ' '
            
            # Add the last song
            if current_song and 'artist' in current_song and 'title' in current_song:
                songs.append(current_song)
            
            # Create timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'name': f"{playlist_name} ({timestamp})",
                'songs': songs,
                'metadata': {
                    'mood': mood,
                    'theme': theme,
                    'created_at': timestamp
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating playlist: {str(e)}")
            raise
    
    def generate_song_info(self, artist, title):
        """Generate interesting information about a song.
        
        Args:
            artist (str): Artist name
            title (str): Song title
            
        Returns:
            dict: Generated information about the song
        """
        try:
            # Prepare the prompt
            messages = self._format_prompt(
                "song_info",
                artist=artist,
                title=title
            )
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            return {
                'info': content,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        except Exception as e:
            logger.error(f"Error generating song info: {str(e)}")
            raise
    
    def generate_dj_intro(self, song_info, playlist_name=""):
        """Generate a DJ introduction for a song.
        
        Args:
            song_info (dict): Information about the song
            playlist_name (str, optional): Name of the playlist
            
        Returns:
            str: Generated DJ introduction
        """
        try:
            # Extract song information
            artist = song_info.get('artist', 'Unknown Artist')
            title = song_info.get('title', 'Unknown Title')
            
            # Prepare the prompt
            messages = self._format_prompt(
                "dj_intro",
                artist=artist,
                title=title,
                playlist_name=playlist_name
            )
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=200
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            return content
        
        except Exception as e:
            logger.error(f"Error generating DJ intro: {str(e)}")
            raise
    
    def analyze_trends(self, trends, recent_plays):
        """Analyze music trends and compare with user's recent plays.
        
        Args:
            trends (dict): Current music trends from various sources
            recent_plays (list): User's recently played songs
            
        Returns:
            dict: Analysis and recommendations
        """
        try:
            # Format the trends for the prompt
            formatted_trends = []
            
            for source, items in trends.items():
                formatted_trends.append(f"{source.upper()} TRENDS:")
                for item in items:
                    if isinstance(item, dict):
                        if 'artist' in item and 'title' in item:
                            formatted_trends.append(f"- {item['artist']} - {item['title']}")
                        elif 'name' in item:
                            formatted_trends.append(f"- {item['name']}")
                    else:
                        formatted_trends.append(f"- {item}")
            
            trends_str = "\n".join(formatted_trends)
            
            # Format the recent plays for the prompt
            formatted_plays = []
            for song in recent_plays:
                formatted_plays.append(f"{song.get('artist', 'Unknown Artist')} - {song.get('title', 'Unknown Title')}")
            
            recent_plays_str = ", ".join(formatted_plays)
            
            # Prepare the prompt
            messages = self._format_prompt(
                "trend_analyzer",
                trends=trends_str,
                recent_plays=recent_plays_str
            )
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            return {
                'analysis': content,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            raise
