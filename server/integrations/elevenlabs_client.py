import os
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ElevenLabsClient:
    """Client for interacting with the ElevenLabs API."""
    
    def __init__(self):
        """Initialize the ElevenLabs client."""
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.base_url = 'https://api.elevenlabs.io/v1'
        self.default_voice_id = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Default voice (Rachel)
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not found. Text-to-speech functionality will be limited.")
    
    def text_to_speech(self, text, voice_id=None):
        """Convert text to speech using ElevenLabs API.
        
        Args:
            text (str): The text to convert to speech
            voice_id (str, optional): The voice ID to use. Defaults to None (uses default voice).
            
        Returns:
            bytes: Audio data in MP3 format
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not set. Cannot generate speech.")
            return None
        
        # Use provided voice ID or fall back to default
        voice_id = voice_id or self.default_voice_id
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json',
            'xi-api-key': self.api_key
        }
        
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in text-to-speech request: {str(e)}")
            return None
    
    def get_available_voices(self):
        """Get a list of available voices from ElevenLabs.
        
        Returns:
            list: List of voice objects with id, name, and preview_url
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not set. Cannot retrieve voices.")
            return []
        
        url = f"{self.base_url}/voices"
        
        headers = {
            'Accept': 'application/json',
            'xi-api-key': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            voices_data = response.json().get('voices', [])
            
            # Format the response
            voices = []
            for voice in voices_data:
                preview_url = None
                if voice.get('preview_url'):
                    preview_url = voice['preview_url']
                
                voices.append({
                    'voice_id': voice['voice_id'],
                    'name': voice['name'],
                    'preview_url': preview_url
                })
            
            return voices
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving voices: {str(e)}")
            return []
