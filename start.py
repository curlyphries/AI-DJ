import os
import sys
import subprocess
import time
import webbrowser
import signal
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('playlists', exist_ok=True)
os.makedirs(os.path.join('voicebot', 'outputs'), exist_ok=True)

# Load environment variables
load_dotenv()

def check_env_file():
    """Check if .env file exists and create it from example if not."""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            logger.info("No .env file found. Creating from .env.example...")
            with open('.env.example', 'r') as example_file:
                example_content = example_file.read()
            
            with open('.env', 'w') as env_file:
                env_file.write(example_content)
            
            logger.info("Created .env file. Please edit it with your API keys and settings.")
            logger.info("Exiting. Please restart after configuring .env file.")
            sys.exit(1)
        else:
            logger.error("No .env or .env.example file found. Please create a .env file with your settings.")
            sys.exit(1)

def check_dependencies():
    """Check if required Python packages are installed."""
    try:
        import flask
        import openai
        import elevenlabs
        logger.info("All required packages are installed.")
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Installing dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_flask_server():
    """Start the Flask server."""
    logger.info("Starting AI DJ Flask server...")
    
    # Start the Flask server
    flask_process = subprocess.Popen(
        [sys.executable, "server/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to start
    time.sleep(2)
    
    if flask_process.poll() is not None:
        # Process has terminated
        stdout, stderr = flask_process.communicate()
        logger.error(f"Flask server failed to start: {stderr}")
        sys.exit(1)
    
    logger.info("Flask server started successfully.")
    return flask_process

def open_browser():
    """Open the web browser to the AI DJ interface."""
    url = "http://localhost:5000"
    logger.info(f"Opening AI DJ interface in browser: {url}")
    webbrowser.open(url)

def handle_shutdown(flask_process):
    """Handle graceful shutdown of processes."""
    def signal_handler(sig, frame):
        logger.info("Shutting down AI DJ...")
        flask_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main function to start the AI DJ system."""
    logger.info("Starting AI DJ Assistant...")
    
    # Check for .env file
    check_env_file()
    
    # Check dependencies
    check_dependencies()
    
    # Start Flask server
    flask_process = start_flask_server()
    
    # Set up signal handlers for graceful shutdown
    handle_shutdown(flask_process)
    
    # Open browser
    open_browser()
    
    logger.info("AI DJ Assistant is running. Press Ctrl+C to stop.")
    
    # Keep the script running
    try:
        while True:
            if flask_process.poll() is not None:
                # Flask server has stopped
                stdout, stderr = flask_process.communicate()
                logger.error(f"Flask server stopped unexpectedly: {stderr}")
                sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down AI DJ...")
        flask_process.terminate()

if __name__ == "__main__":
    main()
