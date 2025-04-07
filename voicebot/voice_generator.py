import os
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from elevenlabs import generate, set_api_key, voices
from elevenlabs.api import Voice, VoiceSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'voice_generator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Class to generate voice announcements for the AI DJ."""
    
    def __init__(self):
        """Initialize the voice generator."""
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment
        self.api_key = os.getenv('ELEVENLABS_API_KEY', '')
        if not self.api_key:
            logger.error("ElevenLabs API key not set in environment variables")
            raise ValueError("ElevenLabs API key not set")
        
        # Set API key for elevenlabs library
        set_api_key(self.api_key)
        
        # Get default voice ID from environment or use a default
        self.default_voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')
        
        # Voice settings optimized for a DJ-like voice
        self.voice_settings = VoiceSettings(
            stability=0.71,  # Higher stability for consistent DJ voice
            similarity_boost=0.5,  # Balanced similarity
            style=0.0,  # Neutral style
            use_speaker_boost=True  # Enhanced clarity
        )
        
        # Create output directory
        os.makedirs(os.path.join('voicebot', 'outputs'), exist_ok=True)
        
        # Load available voices
        self.available_voices = self._get_available_voices()
    
    def _get_available_voices(self):
        """Get available voices from ElevenLabs API."""
        try:
            available_voices = voices()
            logger.info(f"Loaded {len(available_voices)} voices from ElevenLabs")
            return available_voices
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []
    
    def generate_speech(self, text, voice_id=None, output_path=None):
        """Generate speech from text.
        
        Args:
            text (str): Text to convert to speech
            voice_id (str, optional): Voice ID to use
            output_path (str, optional): Path to save the audio file
            
        Returns:
            str: Path to the generated audio file
        """
        if not text:
            logger.error("No text provided for speech generation")
            return None
        
        # Use default voice ID if not provided
        if not voice_id:
            voice_id = self.default_voice_id
        
        # Generate a default output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = os.path.join('voicebot', 'outputs', f"speech_{timestamp}.mp3")
        
        try:
            # Generate audio using the elevenlabs library
            audio_data = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=self.voice_settings
                ),
                model="eleven_monolingual_v1"
            )
            
            # Save audio to file
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Generated speech saved to {output_path}")
            
            # Save metadata
            metadata_path = output_path.replace('.mp3', '.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    'text': text,
                    'voice_id': voice_id,
                    'timestamp': datetime.now().isoformat(),
                    'audio_path': output_path
                }, f, indent=2)
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return None
    
    def generate_dj_intro(self, song_info, playlist_name="", voice_id=None):
        """Generate a DJ introduction for a song.
        
        Args:
            song_info (dict): Information about the song
            playlist_name (str, optional): Name of the playlist
            voice_id (str, optional): Voice ID to use
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Extract song information
            artist = song_info.get('artist', 'Unknown Artist')
            title = song_info.get('title', 'Unknown Title')
            
            # Load intro template
            intro_template_path = os.path.join('prompts', 'dj_intro.json')
            if os.path.exists(intro_template_path):
                with open(intro_template_path, 'r') as f:
                    template = json.load(f)
                    intro_text = template.get('user', '').format(
                        artist=artist,
                        title=title,
                        playlist_name=playlist_name
                    )
            else:
                # Fallback template if file doesn't exist
                intro_text = f"Up next, we've got '{title}' by {artist}"
                if playlist_name:
                    intro_text += f" from the {playlist_name} playlist"
                intro_text += ". Enjoy the vibe!"
            
            # Generate speech
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = os.path.join('voicebot', 'outputs', f"dj_intro_{timestamp}.mp3")
            
            return self.generate_speech(intro_text, voice_id, output_path)
        
        except Exception as e:
            logger.error(f"Error generating DJ intro: {str(e)}")
            return None
    
    def generate_song_info(self, song_info, voice_id=None):
        """Generate song information announcement.
        
        Args:
            song_info (dict): Information about the song
            voice_id (str, optional): Voice ID to use
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Extract song information
            artist = song_info.get('artist', 'Unknown Artist')
            title = song_info.get('title', 'Unknown Title')
            
            # Check if we have AI-generated content
            if 'ai_content' in song_info and song_info['ai_content'].get('info'):
                info_text = song_info['ai_content']['info']
            else:
                # Fallback if no AI content
                info_text = f"That was '{title}' by {artist}. A great track from their collection."
            
            # Generate speech
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = os.path.join('voicebot', 'outputs', f"song_info_{timestamp}.mp3")
            
            return self.generate_speech(info_text, voice_id, output_path)
        
        except Exception as e:
            logger.error(f"Error generating song info: {str(e)}")
            return None
    
    def announce_playlist(self, playlist_info, voice_id=None):
        """Generate a playlist announcement.
        
        Args:
            playlist_info (dict): Information about the playlist
            voice_id (str, optional): Voice ID to use
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Extract playlist information
            name = playlist_info.get('name', 'Unknown Playlist')
            song_count = playlist_info.get('songCount', 0)
            
            # Create announcement text
            announcement_text = f"Starting playlist: {name}. "
            
            if 'comment' in playlist_info and playlist_info['comment']:
                announcement_text += f"{playlist_info['comment']}. "
            
            announcement_text += f"This playlist contains {song_count} tracks. Let's dive in!"
            
            # Generate speech
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = os.path.join('voicebot', 'outputs', f"playlist_announce_{timestamp}.mp3")
            
            return self.generate_speech(announcement_text, voice_id, output_path)
        
        except Exception as e:
            logger.error(f"Error announcing playlist: {str(e)}")
            return None
    
    def announce_custom_message(self, message, voice_id=None):
        """Generate a custom announcement.
        
        Args:
            message (str): Custom message to announce
            voice_id (str, optional): Voice ID to use
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            # Generate speech
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = os.path.join('voicebot', 'outputs', f"custom_message_{timestamp}.mp3")
            
            return self.generate_speech(message, voice_id, output_path)
        
        except Exception as e:
            logger.error(f"Error announcing custom message: {str(e)}")
            return None

def main():
    """Main function to test voice generation."""
    try:
        # Create voice generator
        voice_gen = VoiceGenerator()
        
        # Test DJ intro
        song_info = {
            'artist': 'Daft Punk',
            'title': 'Get Lucky'
        }
        
        dj_intro_path = voice_gen.generate_dj_intro(song_info, "Summer Vibes")
        print(f"DJ intro generated: {dj_intro_path}")
        
        # Test custom message
        custom_message_path = voice_gen.announce_custom_message(
            "Welcome to AI DJ! I'll be your virtual DJ today, playing the best tracks from your collection."
        )
        print(f"Custom message generated: {custom_message_path}")
        
    except Exception as e:
        logger.error(f"Error in voice generator test: {str(e)}")

if __name__ == "__main__":
    main()
