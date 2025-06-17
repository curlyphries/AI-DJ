import os
import json
import logging
import requests
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified client for OpenAI or Ollama language models."""

    def __init__(self, provider='openai', api_key=None, base_url=None, model=None):
        self.provider = provider

        if provider == 'openai':
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            self.client = OpenAI(api_key=api_key)
            self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4')
        elif provider == 'ollama':
            self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.model = model or os.getenv('OLLAMA_MODEL', 'llama3')
        else:
            raise ValueError("Unsupported provider: %s" % provider)

        # Load prompt templates
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load prompt templates from the prompts directory."""
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts')

        if not os.path.exists(prompts_dir):
            os.makedirs(prompts_dir)
            self._create_default_templates(prompts_dir)

        try:
            for filename in os.listdir(prompts_dir):
                if filename.endswith('.json'):
                    template_name = filename[:-5]
                    with open(os.path.join(prompts_dir, filename), 'r') as f:
                        self.templates[template_name] = json.load(f)
            logger.info("Loaded %d prompt templates", len(self.templates))
        except Exception as e:
            logger.error("Error loading prompt templates: %s", str(e))

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
        logger.info("Created %d default prompt templates", len(default_templates))

    def _format_prompt(self, template_name, **kwargs):
        """Format a prompt template with provided variables."""
        if template_name not in self.templates:
            logger.warning("Template %s not found, using default", template_name)
            return [
                {"role": "system", "content": "You are an AI assistant for a music application."},
                {"role": "user", "content": str(kwargs)}
            ]

        template = self.templates[template_name]
        system_content = template["system"]
        user_content = template["user"].format(**kwargs)
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

    def chat_completion(self, messages, temperature=0.7, max_tokens=500):
        """Send a chat completion request to the configured provider."""
        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
                r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                return data.get('message', {}).get('content', '')
        except Exception as e:
            logger.error("Error during chat completion: %s", str(e))
            raise

    def generate_song_info(self, artist, title):
        messages = self._format_prompt("song_info", artist=artist, title=title)
        content = self.chat_completion(messages, max_tokens=500)
        return {
            'info': content,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def generate_dj_intro(self, song_info, playlist_name=""):
        artist = song_info.get('artist', 'Unknown Artist')
        title = song_info.get('title', 'Unknown Title')
        messages = self._format_prompt(
            "dj_intro",
            artist=artist,
            title=title,
            playlist_name=playlist_name
        )
        return self.chat_completion(messages, temperature=0.8, max_tokens=200)

    def analyze_trends(self, trends, recent_plays):
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

        formatted_plays = [f"{s.get('artist', 'Unknown Artist')} - {s.get('title', 'Unknown Title')}" for s in recent_plays]
        recent_plays_str = ", ".join(formatted_plays)

        messages = self._format_prompt(
            "trend_analyzer",
            trends=trends_str,
            recent_plays=recent_plays_str
        )
        content = self.chat_completion(messages, max_tokens=800)
        return {
            'analysis': content,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
