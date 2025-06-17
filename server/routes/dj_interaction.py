import os
import json
import random
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
import openai

# Initialize logger
logger = logging.getLogger(__name__)

# Create Blueprint
dj_interaction = Blueprint('dj_interaction', __name__)

# Global clients
openai_client = None
elevenlabs_client = None
navidrome_client = None

# User management
user_states = {}  # Store user states (active, muted, suspended)
moderation_rules = {
    "mute_duration": 60,  # seconds
    "warning_threshold": 2,  # warnings before muting
    "mute_threshold": 3,  # mutes before suspension
    "suspension_duration": 3600,  # seconds (1 hour)
}

def init_clients(openai_c, elevenlabs_c, navidrome_c):
    """Initialize clients for use in this module."""
    global openai_client, elevenlabs_client, navidrome_client
    openai_client = openai_c
    elevenlabs_client = elevenlabs_c
    navidrome_client = navidrome_c
    logger.info("DJ Interaction clients initialized")

def process_dj_request(user_request, context=None):
    """Process a DJ request and return a response."""
    if context is None:
        context = {}
    
    # Get DJ profile if provided
    dj_profile = None
    if context.get('dj_profile'):
        dj_profile = get_dj_profile(context.get('dj_profile'))
    
    # Get tone setting if provided
    tone = context.get('tone')

    # Categorize the request
    request_type = categorize_request(user_request)
    
    # Process based on request type
    if request_type == 'trivia':
        return generate_music_trivia(dj_profile, tone)
    elif request_type == 'song_info':
        now_playing = context.get('now_playing', {})
        return generate_song_info(now_playing, dj_profile, tone)
    elif request_type == 'play_song':
        return handle_play_song_request(user_request, dj_profile)
    elif request_type == 'create_playlist':
        return handle_create_playlist_request(user_request, dj_profile)
    else:
        # General conversation
        return handle_general_conversation(user_request, context, dj_profile, tone)

def categorize_request(request_text):
    """Categorize the type of request from the user."""
    request_lower = request_text.lower()
    
    # Simple keyword matching for now
    if any(word in request_lower for word in ['trivia', 'quiz', 'question', 'challenge']):
        return 'trivia'
    elif any(word in request_lower for word in ['fact', 'info', 'about', 'tell me about']):
        return 'song_info'
    elif any(word in request_lower for word in ['play', 'listen', 'hear']):
        return 'play_song'
    elif any(word in request_lower for word in ['playlist', 'mix', 'compilation', 'collection']):
        return 'create_playlist'
    else:
        return 'generic'

def generate_music_trivia(dj_profile=None, tone=None):
    """Generate a random music trivia fact."""
    try:
        # Load trivia prompt
        with open(os.path.join('prompts', 'trivia.json'), 'r') as f:
            trivia_prompt = json.load(f)
        
        # Customize prompt with DJ profile if available
        if dj_profile:
            system_prompt = f"{dj_profile.get('personality')}\n\n{trivia_prompt['system']}"
        else:
            system_prompt = trivia_prompt['system']

        if tone and tone != 'default':
            system_prompt = f"{system_prompt}\nRespond in a {tone} style."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": trivia_prompt["user"]}
        ]
        trivia_text = openai_client.chat_completion(messages, max_tokens=250).strip()
        
        return {
            "response": trivia_text,
            "generate_audio": True,
            "voice_id": dj_profile.get('voice_id') if dj_profile else None,
            "actions": []
        }
    except Exception as e:
        logger.error(f"Error generating music trivia: {str(e)}")
        return {
            "response": "I'm sorry, I couldn't generate music trivia at the moment. Please try again later.",
            "generate_audio": True,
            "actions": []
        }

def generate_song_info(now_playing, dj_profile=None, tone=None):
    """Generate interesting information about the current song."""
    try:
        # Check if now_playing info is available
        if not now_playing or not now_playing.get('title'):
            return {
                "response": "I don't have information about the current song. Is something playing?",
                "generate_audio": True,
                "actions": []
            }
        
        # Load song info prompt
        with open(os.path.join('prompts', 'song_info.json'), 'r') as f:
            song_info_prompt = json.load(f)
        
        # Format the prompt with song info
        user_prompt = song_info_prompt["user"].format(
            title=now_playing.get('title', 'Unknown'),
            artist=now_playing.get('artist', 'Unknown'),
            album=now_playing.get('album', 'Unknown'),
            year=now_playing.get('year', 'Unknown')
        )
        
        # Customize prompt with DJ profile if available
        if dj_profile:
            system_prompt = f"{dj_profile.get('personality')}\n\n{song_info_prompt['system']}"
        else:
            system_prompt = song_info_prompt['system']

        if tone and tone != 'default':
            system_prompt = f"{system_prompt}\nRespond in a {tone} style."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        song_info_text = openai_client.chat_completion(messages, max_tokens=300).strip()
        
        return {
            "response": song_info_text,
            "generate_audio": True,
            "voice_id": dj_profile.get('voice_id') if dj_profile else None,
            "actions": []
        }
    except Exception as e:
        logger.error(f"Error generating song info: {str(e)}")
        return {
            "response": "I'm sorry, I couldn't generate information about this song at the moment. Please try again later.",
            "generate_audio": True,
            "actions": []
        }

def handle_general_conversation(user_request, context, dj_profile=None, tone=None):
    """Handle general conversation with the DJ."""
    try:
        # Load chat prompt
        with open(os.path.join('prompts', 'dj_chat.json'), 'r') as f:
            chat_prompt = json.load(f)
        
        # Format the prompt with context
        now_playing = context.get('now_playing', {})
        
        # Customize prompt with DJ profile if available
        if dj_profile:
            system_prompt = f"{dj_profile.get('personality')}\n\n{chat_prompt['system']}"
        else:
            system_prompt = chat_prompt['system']

        if tone and tone != 'default':
            system_prompt = f"{system_prompt}\nRespond in a {tone} style."
        
        # Generate chat response using OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current song: {now_playing.get('title', 'Unknown')} by {now_playing.get('artist', 'Unknown')}\n\nUser request: {user_request}"}
        ]
        
        chat_response = openai_client.chat_completion(messages, max_tokens=250).strip()
        
        return {
            "response": chat_response,
            "generate_audio": True,
            "voice_id": dj_profile.get('voice_id') if dj_profile else None,
            "actions": []
        }
    except Exception as e:
        logger.error(f"Error handling general conversation: {str(e)}")
        return {
            "response": "I'm sorry, I couldn't process your request at the moment. Please try again later.",
            "generate_audio": True,
            "actions": []
        }

def handle_play_song_request(request_text, dj_profile=None):
    """Handle requests to play specific songs."""
    # Extract song/artist from request
    # This is a simple implementation - in a real system, you'd use NLP to extract entities
    request_lower = request_text.lower().replace('play', '').replace('a song', '').strip()
    
    # Search for songs in Navidrome
    try:
        search_results = navidrome_client.search_songs(request_lower, limit=5)
        
        if not search_results or len(search_results) == 0:
            return {
                "response": f"I couldn't find any songs matching '{request_lower}'. Would you like to try another search?",
                "generate_audio": True,
                "actions": []
            }
        
        # Get the first result
        song = search_results[0]
        
        # Create action to play the song
        actions = [{
            "type": "play_song",
            "label": f"Play {song.get('title', 'this song')}",
            "icon": "bi-play-circle",
            "data": {
                "song_id": song.get('id')
            }
        }]
        
        return {
            "response": f"I found '{song.get('title')}' by {song.get('artist')}. Would you like me to play it?",
            "generate_audio": True,
            "voice_id": dj_profile.get('voice_id') if dj_profile else None,
            "actions": actions
        }
    except Exception as e:
        logger.error(f"Error searching for songs: {str(e)}")
        return {
            "response": "I'm having trouble searching for songs right now. Please try again later.",
            "generate_audio": True,
            "actions": []
        }

def handle_create_playlist_request(request_text, dj_profile=None):
    """Handle requests to create playlists."""
    # Extract mood/theme from request
    # This is a simple implementation - in a real system, you'd use NLP to extract entities
    request_words = request_text.lower().split()
    
    # Default values
    mood = "energetic"
    theme = "general"
    
    # Look for mood keywords
    mood_keywords = ["happy", "sad", "energetic", "chill", "relaxed", "upbeat", "melancholic"]
    for keyword in mood_keywords:
        if keyword in request_words:
            mood = keyword
            break
    
    # Look for theme keywords
    theme_keywords = ["workout", "study", "party", "road trip", "focus", "romantic", "dinner"]
    for keyword in theme_keywords:
        if keyword in request_words or keyword.replace(" ", "") in request_words:
            theme = keyword
            break
    
    # Create action to generate playlist
    actions = [{
        "type": "create_playlist",
        "label": f"Create {mood} {theme} playlist",
        "icon": "bi-music-note-list",
        "data": {
            "mood": mood,
            "theme": theme,
            "count": 10
        }
    }]
    
    return {
        "response": f"I'd be happy to create a {mood} playlist with a {theme} theme. How does that sound?",
        "generate_audio": True,
        "voice_id": dj_profile.get('voice_id') if dj_profile else None,
        "actions": actions
    }

@dj_interaction.route('/dj_request', methods=['POST'])
def handle_dj_request():
    """Handle user requests sent to the DJ."""
    try:
        data = request.json
        user_request = data.get('request', '')
        context = data.get('context', {})
        user_id = data.get('user_id', 'default_user')
        tone = data.get('tone', 'default')
        voice_speed = data.get('voice_speed', 1.0)

        # Pass tone and speed in context
        context['tone'] = tone
        context['voice_speed'] = voice_speed
        
        logger.info(f"Received DJ request from {user_id}: {user_request}")
        
        # Check if user is allowed to interact
        user_status = check_user_status(user_id)
        if user_status.get('status') != 'active':
            return jsonify({
                "success": False,
                "response": user_status.get('message'),
                "muted_until": user_status.get('muted_until'),
                "suspended_until": user_status.get('suspended_until')
            })
        
        # Check for non-music content
        is_music_related, moderation_result = check_music_relevance(user_request)
        if not is_music_related:
            # Update user warnings
            update_user_warnings(user_id)
            return jsonify({
                "success": False,
                "response": moderation_result,
                "warnings": user_states.get(user_id, {}).get('warnings', 0)
            })
        
        # Process the request
        response_data = process_dj_request(user_request, context)
        
        # Generate audio response if needed
        audio_path = None
        if response_data.get('generate_audio', True):
            # Get voice ID from response data or use default
            voice_id = response_data.get('voice_id')
            voice_speed = context.get('voice_speed', 1.0)

            audio_data = elevenlabs_client.text_to_speech(
                response_data['response'],
                voice_id=voice_id,
                speed=voice_speed
            )
            
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            audio_path = os.path.join('voicebot', 'outputs', f"dj_{timestamp}.mp3")
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            audio_path = f"/static/audio/{os.path.basename(audio_path)}"
        
        # Log the request and response
        log_interaction(user_request, response_data['response'], user_id)
        
        return jsonify({
            "success": True,
            "response": response_data['response'],
            "audio_path": audio_path,
            "actions": response_data.get('actions', [])
        })
    except Exception as e:
        logger.error(f"Error handling DJ request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_dj_profile(profile_id):
    """Get a DJ profile by ID."""
    try:
        # Import here to avoid circular imports
        from server.routes.settings import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, voice_id, personality FROM dj_profiles WHERE id = ?', (profile_id,))
        profile = cursor.fetchone()
        
        conn.close()
        
        if profile:
            return {
                "id": profile['id'],
                "name": profile['name'],
                "voice_id": profile['voice_id'],
                "personality": profile['personality']
            }
        
        return None
    except Exception as e:
        logger.error(f"Error getting DJ profile: {str(e)}")
        return None

def check_music_relevance(request_text):
    """Check if the request is music-related and appropriate.
    
    Returns:
        tuple: (is_music_related, message)
    """
    # Load moderation prompt
    try:
        with open(os.path.join('prompts', 'moderation.json'), 'r') as f:
            moderation_prompt = json.load(f)
    except FileNotFoundError:
        # Fallback prompt if file not found
        moderation_prompt = {
            "system": "You are a content moderator for a music DJ system. Your job is to determine if user requests are music-related and appropriate. Respond with 'MUSIC_RELATED' if the request is about music, artists, songs, playlists, or music history. Respond with 'NOT_MUSIC_RELATED' followed by a witty but authoritative explanation if the request is inappropriate or not related to music.",
            "user": "{request}"
        }
    
    # Format the prompt with the request
    user_prompt = moderation_prompt["user"].format(request=request_text)
    
    messages = [
        {"role": "system", "content": moderation_prompt["system"]},
        {"role": "user", "content": user_prompt}
    ]
    result = openai_client.chat_completion(messages, max_tokens=150).strip()
    
    if result.startswith("MUSIC_RELATED"):
        return True, "Music-related content"
    else:
        # Extract the explanation (remove the NOT_MUSIC_RELATED prefix)
        explanation = result.replace("NOT_MUSIC_RELATED", "").strip()
        if not explanation:
            explanation = "Sorry, I only respond to music-related questions. I'm a DJ, not a general assistant."
        return False, explanation

def check_user_status(user_id):
    """Check if a user is allowed to interact with the DJ.
    
    Returns:
        dict: User status information
    """
    if user_id not in user_states:
        # Initialize new user
        user_states[user_id] = {
            'status': 'active',
            'warnings': 0,
            'mutes': 0,
            'muted_until': None,
            'suspended_until': None,
            'last_request': datetime.now().timestamp()
        }
        return {'status': 'active', 'message': 'Welcome to AI DJ!'}
    
    user_state = user_states[user_id]
    current_time = datetime.now().timestamp()
    
    # Check if user is suspended
    if user_state.get('suspended_until') and current_time < user_state['suspended_until']:
        time_left = int(user_state['suspended_until'] - current_time)
        return {
            'status': 'suspended',
            'message': f"Your account is suspended. Please try again in {time_left // 60} minutes and {time_left % 60} seconds.",
            'suspended_until': user_state['suspended_until']
        }
    
    # Check if user is muted
    if user_state.get('muted_until') and current_time < user_state['muted_until']:
        time_left = int(user_state['muted_until'] - current_time)
        return {
            'status': 'muted',
            'message': f"You've been muted for non-music content. You can try again in {time_left} seconds.",
            'muted_until': user_state['muted_until']
        }
    
    # If user was muted or suspended but time has passed, reset status
    if user_state.get('status') != 'active':
        user_state['status'] = 'active'
        user_state['muted_until'] = None
        user_state['suspended_until'] = None
    
    # Update last request time
    user_state['last_request'] = current_time
    
    return {'status': 'active', 'message': 'Active user'}

def update_user_warnings(user_id):
    """Update user warnings and apply muting/suspension if needed."""
    if user_id not in user_states:
        user_states[user_id] = {
            'status': 'active',
            'warnings': 1,
            'mutes': 0,
            'last_request': datetime.now().timestamp()
        }
        return
    
    user_state = user_states[user_id]
    current_time = datetime.now().timestamp()
    
    # Increment warnings
    user_state['warnings'] = user_state.get('warnings', 0) + 1
    
    # Check if user should be muted
    if user_state['warnings'] >= moderation_rules['warning_threshold']:
        user_state['status'] = 'muted'
        user_state['muted_until'] = current_time + moderation_rules['mute_duration']
        user_state['mutes'] = user_state.get('mutes', 0) + 1
        user_state['warnings'] = 0  # Reset warnings after muting
        
        # Check if user should be suspended after multiple mutes
        if user_state['mutes'] >= moderation_rules['mute_threshold']:
            user_state['status'] = 'suspended'
            user_state['suspended_until'] = current_time + moderation_rules['suspension_duration']
            user_state['mutes'] = 0  # Reset mutes after suspension

def log_interaction(request, response, user_id='default_user'):
    """Log user-DJ interactions."""
    try:
        log_dir = os.path.join('logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'dj_interactions.json')
        
        # Load existing log or create new one
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        else:
            logs = []
        
        # Add new log entry
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "request": request,
            "response": response
        })
        
        # Save logs (keep only last 100 entries)
        with open(log_file, 'w') as f:
            json.dump(logs[-100:], f, indent=2)
    except Exception as e:
        logger.error(f"Error logging interaction: {str(e)}")

# Additional routes for DJ interaction

@dj_interaction.route('/recent_dj_interactions', methods=['GET'])
def get_recent_interactions():
    """Get recent DJ interactions."""
    try:
        log_file = os.path.join('logs', 'dj_interactions.json')
        
        if not os.path.exists(log_file):
            return jsonify({"interactions": []})
        
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        return jsonify({"interactions": logs[-10:]})  # Return last 10 interactions
    except Exception as e:
        logger.error(f"Error getting recent interactions: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Additional routes for user management

@dj_interaction.route('/user_status/<user_id>', methods=['GET'])
def get_user_status(user_id):
    """Get the status of a specific user."""
    if user_id not in user_states:
        return jsonify({
            "status": "active",
            "warnings": 0,
            "mutes": 0
        })
    
    user_state = user_states[user_id]
    current_time = datetime.now().timestamp()
    
    # Check if mute/suspension has expired
    if user_state.get('status') != 'active':
        if (user_state.get('status') == 'muted' and 
            user_state.get('muted_until') and 
            current_time >= user_state['muted_until']):
            user_state['status'] = 'active'
            user_state['muted_until'] = None
        
        if (user_state.get('status') == 'suspended' and 
            user_state.get('suspended_until') and 
            current_time >= user_state['suspended_until']):
            user_state['status'] = 'active'
            user_state['suspended_until'] = None
    
    return jsonify({
        "status": user_state.get('status', 'active'),
        "warnings": user_state.get('warnings', 0),
        "mutes": user_state.get('mutes', 0),
        "muted_until": user_state.get('muted_until'),
        "suspended_until": user_state.get('suspended_until')
    })

@dj_interaction.route('/reset_user/<user_id>', methods=['POST'])
def reset_user(user_id):
    """Reset a user's status (admin function)."""
    if user_id in user_states:
        user_states[user_id] = {
            'status': 'active',
            'warnings': 0,
            'mutes': 0,
            'muted_until': None,
            'suspended_until': None,
            'last_request': datetime.now().timestamp()
        }
    
    return jsonify({
        "success": True,
        "message": f"User {user_id} has been reset"
    })

@dj_interaction.route('/moderation_settings', methods=['GET', 'POST'])
def manage_moderation_settings():
    """Get or update moderation settings."""
    global moderation_rules
    
    if request.method == 'POST':
        data = request.json
        
        # Update moderation rules
        for key in ['mute_duration', 'warning_threshold', 'mute_threshold', 'suspension_duration']:
            if key in data:
                moderation_rules[key] = data[key]
        
        return jsonify({
            "success": True,
            "message": "Moderation settings updated",
            "settings": moderation_rules
        })
    
    # GET request - return current settings
    return jsonify(moderation_rules)
