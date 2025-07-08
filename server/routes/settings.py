import os
import json
import logging
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
settings = Blueprint('settings', __name__)

# Database setup
def get_db_connection():
    """Get a connection to the SQLite database."""
    db_path = os.path.join('data', 'user_settings.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        service TEXT NOT NULL,
        api_key TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, service)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dj_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        voice_id TEXT NOT NULL,
        personality TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Helper functions
def get_available_voices():
    """Get list of available voices from ElevenLabs."""
    # This would typically call the ElevenLabs API
    # For now, return a static list as a placeholder
    return [
        {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "preview_url": "https://example.com/voice1.mp3"},
        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "preview_url": "https://example.com/voice2.mp3"},
        {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "preview_url": "https://example.com/voice3.mp3"},
        {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "preview_url": "https://example.com/voice4.mp3"},
        {"voice_id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "preview_url": "https://example.com/voice5.mp3"},
        {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "preview_url": "https://example.com/voice6.mp3"},
        {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "preview_url": "https://example.com/voice7.mp3"},
        {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "preview_url": "https://example.com/voice8.mp3"},
        {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "preview_url": "https://example.com/voice9.mp3"}
    ]

def get_personality_templates():
    """Get list of available DJ personality templates."""
    return [
        {
            "id": "energetic",
            "name": "Energetic",
            "description": "High-energy, enthusiastic DJ who keeps the party going",
            "prompt_template": "You are an energetic, enthusiastic DJ who loves to keep the energy high. Your commentary is fast-paced and exciting."
        },
        {
            "id": "chill",
            "name": "Chill",
            "description": "Relaxed, laid-back DJ perfect for ambient or lounge music",
            "prompt_template": "You are a relaxed, laid-back DJ with a smooth, calming voice. Your commentary is thoughtful and mellow."
        },
        {
            "id": "professional",
            "name": "Professional",
            "description": "Polished, professional DJ with deep music knowledge",
            "prompt_template": "You are a professional radio DJ with extensive music knowledge. Your commentary is informative and well-structured."
        },
        {
            "id": "humorous",
            "name": "Humorous",
            "description": "Funny, witty DJ who adds humor between tracks",
            "prompt_template": "You are a witty, humorous DJ who loves to make listeners laugh. Your commentary includes jokes and playful observations."
        },
        {
            "id": "sassy",
            "name": "Sassy",
            "description": "Sarcastic, sassy DJ with attitude",
            "prompt_template": "You are a sassy DJ with plenty of attitude. Your commentary is sharp, sometimes sarcastic, but always entertaining."
        }
    ]

# Routes
@settings.route('/api_keys', methods=['GET'])
def get_api_keys():
    """Get all API keys for the current user."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT service, api_key FROM api_keys WHERE user_id = ?', (user_id,))
        keys = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries
        key_list = [{"service": key['service'], "api_key": key['api_key']} for key in keys]
        
        return jsonify(key_list)
    except Exception as e:
        logger.error(f"Error getting API keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/api_keys', methods=['POST'])
def add_api_key():
    """Add or update an API key."""
    data = request.json
    user_id = data.get('user_id')
    service = data.get('service')
    api_key = data.get('api_key')
    
    if not user_id or not service or not api_key:
        return jsonify({"error": "User ID, service, and API key are required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if key already exists
        cursor.execute('SELECT id FROM api_keys WHERE user_id = ? AND service = ?', (user_id, service))
        existing_key = cursor.fetchone()
        
        if existing_key:
            # Update existing key
            cursor.execute(
                'UPDATE api_keys SET api_key = ?, updated_at = ? WHERE user_id = ? AND service = ?',
                (api_key, datetime.now().isoformat(), user_id, service)
            )
        else:
            # Insert new key
            cursor.execute(
                'INSERT INTO api_keys (user_id, service, api_key) VALUES (?, ?, ?)',
                (user_id, service, api_key)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"API key for {service} saved successfully"})
    except Exception as e:
        logger.error(f"Error saving API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/api_keys/<service>', methods=['DELETE'])
def delete_api_key(service):
    """Delete an API key."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM api_keys WHERE user_id = ? AND service = ?', (user_id, service))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"API key for {service} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/voices', methods=['GET'])
def get_voices():
    """Get available voices."""
    try:
        voices = get_available_voices()
        return jsonify(voices)
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/personalities', methods=['GET'])
def get_personalities():
    """Get available DJ personality templates."""
    try:
        personalities = get_personality_templates()
        return jsonify(personalities)
    except Exception as e:
        logger.error(f"Error getting personalities: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/dj_profiles', methods=['GET'])
def get_dj_profiles():
    """Get all DJ profiles for the current user."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, voice_id, personality, is_active FROM dj_profiles WHERE user_id = ?', (user_id,))
        profiles = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries
        profile_list = [{
            "id": profile['id'],
            "name": profile['name'],
            "voice_id": profile['voice_id'],
            "personality": profile['personality'],
            "is_active": bool(profile['is_active'])
        } for profile in profiles]
        
        return jsonify(profile_list)
    except Exception as e:
        logger.error(f"Error getting DJ profiles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/dj_profiles', methods=['POST'])
def add_dj_profile():
    """Add or update a DJ profile."""
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    voice_id = data.get('voice_id')
    personality = data.get('personality')
    
    if not user_id or not name or not voice_id or not personality:
        return jsonify({"error": "User ID, name, voice ID, and personality are required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if profile with this name already exists
        cursor.execute('SELECT id FROM dj_profiles WHERE user_id = ? AND name = ?', (user_id, name))
        existing_profile = cursor.fetchone()
        
        if existing_profile:
            # Update existing profile
            cursor.execute(
                'UPDATE dj_profiles SET voice_id = ?, personality = ?, updated_at = ? WHERE id = ?',
                (voice_id, personality, datetime.now().isoformat(), existing_profile['id'])
            )
            profile_id = existing_profile['id']
        else:
            # Insert new profile
            cursor.execute(
                'INSERT INTO dj_profiles (user_id, name, voice_id, personality) VALUES (?, ?, ?, ?)',
                (user_id, name, voice_id, personality)
            )
            profile_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"DJ profile '{name}' saved successfully",
            "profile_id": profile_id
        })
    except Exception as e:
        logger.error(f"Error saving DJ profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/dj_profiles/<int:profile_id>', methods=['DELETE'])
def delete_dj_profile(profile_id):
    """Delete a DJ profile."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if profile exists and belongs to user
        cursor.execute('SELECT id FROM dj_profiles WHERE id = ? AND user_id = ?', (profile_id, user_id))
        profile = cursor.fetchone()
        
        if not profile:
            conn.close()
            return jsonify({"error": "Profile not found or does not belong to user"}), 404
        
        cursor.execute('DELETE FROM dj_profiles WHERE id = ?', (profile_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "DJ profile deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting DJ profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/dj_profiles/<int:profile_id>/activate', methods=['POST'])
def activate_dj_profile(profile_id):
    """Set a DJ profile as active."""
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if profile exists and belongs to user
        cursor.execute('SELECT id FROM dj_profiles WHERE id = ? AND user_id = ?', (profile_id, user_id))
        profile = cursor.fetchone()
        
        if not profile:
            conn.close()
            return jsonify({"error": "Profile not found or does not belong to user"}), 404
        
        # Set all profiles to inactive
        cursor.execute('UPDATE dj_profiles SET is_active = 0 WHERE user_id = ?', (user_id,))
        
        # Set selected profile to active
        cursor.execute('UPDATE dj_profiles SET is_active = 1 WHERE id = ?', (profile_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "DJ profile activated successfully"})
    except Exception as e:
        logger.error(f"Error activating DJ profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@settings.route('/active_dj_profile', methods=['GET'])
def get_active_dj_profile():
    """Get the active DJ profile for the current user."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, voice_id, personality FROM dj_profiles WHERE user_id = ? AND is_active = 1', (user_id,))
        profile = cursor.fetchone()
        
        conn.close()
        
        if not profile:
            return jsonify({"error": "No active DJ profile found"}), 404
        
        return jsonify({
            "id": profile['id'],
            "name": profile['name'],
            "voice_id": profile['voice_id'],
            "personality": profile['personality']
        })
    except Exception as e:
        logger.error(f"Error getting active DJ profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Export settings
@settings.route('/export', methods=['GET'])
def export_settings():
    """Export all user settings."""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get API keys
        cursor.execute('SELECT service, api_key FROM api_keys WHERE user_id = ?', (user_id,))
        api_keys = [dict(row) for row in cursor.fetchall()]
        
        # Get DJ profiles
        cursor.execute('SELECT id, name, voice_id, personality, is_active FROM dj_profiles WHERE user_id = ?', (user_id,))
        dj_profiles = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Create export data
        export_data = {
            "api_keys": api_keys,
            "dj_profiles": dj_profiles,
            "exported_at": datetime.now().isoformat()
        }
        
        return jsonify(export_data)
    except Exception as e:
        logger.error(f"Error exporting settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Import settings
@settings.route('/import', methods=['POST'])
def import_settings():
    """Import user settings."""
    data = request.json
    user_id = data.get('user_id')
    settings_data = data.get('settings')
    
    if not user_id or not settings_data:
        return jsonify({"error": "User ID and settings data are required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Import API keys
        if 'api_keys' in settings_data:
            for key in settings_data['api_keys']:
                service = key.get('service')
                api_key = key.get('api_key')
                
                if service and api_key:
                    # Check if key already exists
                    cursor.execute('SELECT id FROM api_keys WHERE user_id = ? AND service = ?', (user_id, service))
                    existing_key = cursor.fetchone()
                    
                    if existing_key:
                        # Update existing key
                        cursor.execute(
                            'UPDATE api_keys SET api_key = ?, updated_at = ? WHERE user_id = ? AND service = ?',
                            (api_key, datetime.now().isoformat(), user_id, service)
                        )
                    else:
                        # Insert new key
                        cursor.execute(
                            'INSERT INTO api_keys (user_id, service, api_key) VALUES (?, ?, ?)',
                            (user_id, service, api_key)
                        )
        
        # Import DJ profiles
        if 'dj_profiles' in settings_data:
            for profile in settings_data['dj_profiles']:
                name = profile.get('name')
                voice_id = profile.get('voice_id')
                personality = profile.get('personality')
                is_active = profile.get('is_active', 0)
                
                if name and voice_id and personality:
                    # Check if profile already exists
                    cursor.execute('SELECT id FROM dj_profiles WHERE user_id = ? AND name = ?', (user_id, name))
                    existing_profile = cursor.fetchone()
                    
                    if existing_profile:
                        # Update existing profile
                        cursor.execute(
                            'UPDATE dj_profiles SET voice_id = ?, personality = ?, is_active = ?, updated_at = ? WHERE id = ?',
                            (voice_id, personality, is_active, datetime.now().isoformat(), existing_profile['id'])
                        )
                    else:
                        # Insert new profile
                        cursor.execute(
                            'INSERT INTO dj_profiles (user_id, name, voice_id, personality, is_active) VALUES (?, ?, ?, ?, ?)',
                            (user_id, name, voice_id, personality, is_active)
                        )
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Settings imported successfully"})
    except Exception as e:
        logger.error(f"Error importing settings: {str(e)}")
        return jsonify({"error": str(e)}), 500
