import os
from dotenv import load_dotenv

class Config:
    """Configuration class for the AI DJ application."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Navidrome configuration
        self.navidrome_url = os.getenv('NAVIDROME_URL', 'http://localhost:4533')
        self.navidrome_username = os.getenv('NAVIDROME_USERNAME', '')
        self.navidrome_password = os.getenv('NAVIDROME_PASSWORD', '')
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4')
        
        # ElevenLabs configuration
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', '')
        self.default_voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default voice ID
        
        # Last.fm configuration
        self.lastfm_api_key = os.getenv('LASTFM_API_KEY', '')
        
        # Spotify configuration
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID', '')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', '')
        
        # Reddit configuration (no API key needed for public data)
        
        # Application configuration
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Resource limits (to maintain target 50% load)
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))  # seconds
        
    def validate(self):
        """Validate that all required configuration is present."""
        missing_vars = []
        
        # Check required variables
        if not self.openai_api_key:
            missing_vars.append('OPENAI_API_KEY')
        if not self.elevenlabs_api_key:
            missing_vars.append('ELEVENLABS_API_KEY')
        if not self.navidrome_username or not self.navidrome_password:
            missing_vars.append('NAVIDROME_USERNAME and/or NAVIDROME_PASSWORD')
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
