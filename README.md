# AI DJ

![AI DJ Logo](server/static/images/logo.png)

An AI-powered DJ system that creates a personalized radio experience with automated announcements, music selection, and user interaction. The system uses AI to generate natural-sounding DJ commentary between songs, curate music based on themes or moods, and interact with users through text or voice commands.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup Instructions](#setup-instructions)
  - [API Keys](#api-keys)
- [Usage](#usage)
  - [Starting the DJ](#starting-the-dj)
  - [Interacting with the DJ](#interacting-with-the-dj)
  - [User Management System](#user-management-system)
  - [Settings Management](#settings-management)
- [Customization](#customization)
  - [DJ Personality](#dj-personality)
  - [Voice Options](#voice-options)
  - [Moderation Settings](#moderation-settings)
- [Deployment](#deployment)
  - [Docker Deployment](#docker-deployment)
  - [Manual Deployment](#manual-deployment)
- [Cross-Platform Support](#cross-platform-support)
- [Data Storage](#data-storage)
- [Future Plans](#future-plans)
- [Contributing](#contributing)
- [License](#license)
- [Troubleshooting](#troubleshooting)

## Features

- **AI-Generated DJ Announcements**: Creates natural-sounding DJ commentary between songs
- **Intelligent Music Selection**: Curates music based on themes, moods, or genres
- **Weather Integration**: Incorporates local weather into announcements
- **Time-Aware**: References the time of day in announcements
- **Special Events**: Recognizes holidays and special occasions
- **Voice Customization**: Multiple voice options for the DJ personality
- **DJ Interaction**: Chat with the DJ to request music trivia, song facts, specific songs, or playlists
- **Voice Recognition**: Speak your requests directly to the DJ
- **User Management**: System to moderate user interactions, including warnings, temporary muting, and account suspension for inappropriate content
- **Settings Management**: Secure local storage for API keys and customization options
- **DJ Profiles**: Create and manage multiple DJ personalities with different voices and styles
- **Cross-Platform**: Works on Windows, Linux, Mac, Android, and iOS devices

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher (for development)
- Docker (optional, for containerized deployment)
- API keys for OpenAI and ElevenLabs (required)
- API keys for Last.fm and Spotify (optional, for enhanced music data)

### Setup Instructions

#### Option 1: Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/curlyphries/ai-dj.git
   cd ai-dj
   ```

2. Create a virtual environment and activate it:
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the template:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your API keys and configuration settings.

6. Initialize the database:
   ```bash
   python server/init_db.py
   ```

7. Start the application:
   ```bash
   python server/app.py
   ```

8. Access the application at `http://localhost:5000`

#### Option 2: Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/curlyphries/ai-dj.git
   cd ai-dj
   ```

2. Create a `.env` file based on the template:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your API keys and configuration settings.

4. Build and start the Docker containers:
   ```bash
   docker-compose up -d
   ```

5. Access the application at `http://localhost:5000`

### API Keys

The following API keys are required or optional for full functionality:

- **OpenAI API Key** (Required): For generating DJ responses
  - Sign up at [OpenAI](https://platform.openai.com/signup)
  - Create an API key at [OpenAI API Keys](https://platform.openai.com/api-keys)

- **ElevenLabs API Key** (Required): For text-to-speech conversion
  - Sign up at [ElevenLabs](https://elevenlabs.io/)
  - Get your API key from the [ElevenLabs Dashboard](https://elevenlabs.io/subscription)

- **Last.fm API Key** (Optional): For music trend data
  - Sign up at [Last.fm](https://www.last.fm/)
  - Create an API account at [Last.fm API](https://www.last.fm/api/account/create)

- **Spotify API Credentials** (Optional): For music recommendations
  - Sign up at [Spotify Developer](https://developer.spotify.com/)
  - Create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
  - Get your Client ID and Client Secret

- **Navidrome Credentials** (Optional): For local music library integration
  - Set up [Navidrome](https://www.navidrome.org/) for your music library
  - Enter your server URL, username, and password in the settings

## Usage

### Starting the DJ

Run the start script:
```bash
# If installed locally
python server/app.py

# If using Docker
docker-compose up -d
```

This will launch the web interface, which you can access at `http://localhost:5000` (or the port specified in your `.env` file).

### Interacting with the DJ

- **Text Chat**: Type your requests in the chat box
- **Voice Input**: Click the microphone button to speak your request
- **Quick Actions**: Use the quick action buttons for common requests

#### Example Requests:
- "Tell me some interesting music trivia"
- "What can you tell me about this song?"
- "Play something from the 80s"
- "Create a workout playlist"
- "What's the weather like today?"
- "Tell me about the artist of this song"

### User Management System

The AI DJ includes a moderation system to ensure appropriate interactions:

1. **Content Filtering**: All requests are checked to ensure they're music-related
2. **Warning System**: 
   - Users receive warnings for non-music related content
   - After 2 warnings, users are temporarily muted
3. **Temporary Muting**:
   - Muted users cannot interact with the DJ for 60 seconds
   - After 3 mutes, the user's account is suspended
4. **Account Suspension**:
   - Suspended accounts cannot interact with the DJ for 1 hour
   - Administrators can reset user status if needed

### Settings Management

The AI DJ includes a comprehensive settings management system:

1. **API Key Management**:
   - Securely store and manage API keys for various services
   - All keys are stored locally in a SQLite database
   - Keys are never shared with external services

2. **DJ Profiles**:
   - Create multiple DJ personalities with different voices and styles
   - Choose from a variety of pre-defined personality templates
   - Create custom personalities with your own descriptions
   - Select from multiple voice options

3. **Export/Import**:
   - Export your settings to a JSON file for backup
   - Import settings from a JSON file to restore or share configurations

4. **Preferences**:
   - Choose between light and dark themes
   - Adjust font size and other display settings
   - Configure interaction preferences

## Customization

### DJ Personality

Create and manage DJ profiles through the Settings page:

1. Go to the Settings page by clicking the gear icon in the DJ interaction panel
2. Navigate to the "Create DJ Profile" tab
3. Choose a voice, personality template, and give your DJ a name
4. Create multiple profiles and switch between them as desired

Available personality templates:
- **Energetic**: High-energy, enthusiastic DJ who brings excitement to every announcement
- **Chill**: Laid-back, smooth DJ with a relaxed vibe perfect for easy listening
- **Professional**: Polished, informative DJ who focuses on music knowledge and facts
- **Humorous**: Fun, witty DJ who adds humor and jokes between tracks
- **Sassy**: Bold, opinionated DJ with attitude and strong music opinions

### Voice Options

Choose from a variety of voices provided by ElevenLabs:

1. Go to the Settings page
2. When creating a DJ profile, select from the available voices
3. Listen to voice previews before making your selection

### Moderation Settings

Adjust moderation settings by modifying the `moderation_rules` dictionary in `server/routes/dj_interaction.py`:

```python
moderation_rules = {
    "mute_duration": 60,  # seconds
    "warning_threshold": 2,  # warnings before muting
    "mute_threshold": 3,  # mutes before suspension
    "suspension_duration": 3600,  # seconds (1 hour)
}
```

## Deployment

### Docker Deployment

The recommended way to deploy AI DJ is using Docker:

1. Ensure Docker and Docker Compose are installed on your system
2. Clone the repository and navigate to the project directory
3. Create and configure your `.env` file
4. Run the following command:

```bash
docker-compose up -d
```

This will start the AI DJ container in detached mode. You can view logs with:

```bash
docker-compose logs -f
```

### Manual Deployment

For manual deployment on a server:

1. Set up a Python environment with all dependencies installed
2. Configure a production web server (e.g., Nginx, Apache) as a reverse proxy
3. Use a process manager like Supervisor or systemd to manage the application process
4. Set up SSL/TLS for secure connections

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Example systemd service file (`/etc/systemd/system/aidj.service`):

```ini
[Unit]
Description=AI DJ Service
After=network.target

[Service]
User=curlyphries
WorkingDirectory=/path/to/ai-dj
ExecStart=/path/to/ai-dj/venv/bin/python server/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Cross-Platform Support

AI DJ is designed to work across multiple platforms:

- **Desktop**: Windows, macOS, Linux
- **Mobile**: Android, iOS (via responsive web interface)
- **Tablets**: iPad, Android tablets

The responsive interface automatically adapts to different screen sizes and input methods, providing an optimal experience on any device.

## Data Storage

All user settings and preferences are stored locally:

- **SQLite Database**: Located in the `data` directory
- **User Settings**: API keys, DJ profiles, and preferences
- **Interaction Logs**: Records of user-DJ interactions

Database schema:

```
users
- id (INTEGER PRIMARY KEY)
- username (TEXT)
- created_at (TIMESTAMP)

api_keys
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER)
- service (TEXT)
- api_key (TEXT)

dj_profiles
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER)
- name (TEXT)
- voice_id (TEXT)
- personality_type (TEXT)
- description (TEXT)
- active (BOOLEAN)

user_interactions
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER)
- request (TEXT)
- response (TEXT)
- timestamp (TIMESTAMP)

user_status
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER)
- status (TEXT)
- warnings (INTEGER)
- mutes (INTEGER)
- last_warning_time (TIMESTAMP)
- last_mute_time (TIMESTAMP)
- suspension_end_time (TIMESTAMP)
```

## Future Plans

- **Cloud Storage Option**: Optional cloud backup for settings and profiles
- **Enhanced Customization**: More voice and personality options
- **Mobile App Integration**: Native mobile apps for Android and iOS
- **Advanced Music Analysis**: AI-powered music recommendations based on listening history
- **Multi-user Support**: Family and shared accounts with personalized profiles
- **Integration with Smart Home**: Control your AI DJ through smart speakers and displays

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

#### Application won't start

- Check that all required dependencies are installed
- Verify that your `.env` file contains all necessary configuration
- Ensure the database has been initialized

#### API key errors

- Verify that your API keys are correct and have not expired
- Check that you have sufficient credits on your API accounts
- Ensure your network can reach the API services

#### Voice generation issues

- Verify your ElevenLabs API key and subscription status
- Check that you have selected a valid voice ID
- Ensure your request is not too long for the service limits

#### Database errors

- Check file permissions on the `data` directory
- Verify the database schema is up to date
- Try reinitializing the database if corruption is suspected

### Getting Help

If you encounter issues not covered here:

1. Check the [Issues](https://github.com/curlyphries/ai-dj/issues) page for similar problems
2. Create a new issue with details about your problem
3. Include relevant logs and system information
