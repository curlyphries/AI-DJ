#!/usr/bin/env bash
# Quick setup script for AI DJ. Designed for beginners and idempotent so it can
# be safely re-run. The script installs Python requirements and optional
# services (Navidrome and Ollama) only if they are not already present.
set -euo pipefail

echo "=== AI DJ Setup ==="

# Determine platform for optional Ollama installer
OS="$(uname)"
case "$OS" in
    Darwin*) PLATFORM="mac";;
    Linux*) PLATFORM="linux";;
    *) PLATFORM="other";;
esac

# Utility to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Helper to install Navidrome only when the container is not already running
install_navidrome() {
    echo "Setting up Navidrome music server..."
    if ! docker ps -a --format '{{.Names}}' | grep -q '^navidrome$'; then
        docker pull deluan/navidrome:latest
        mkdir -p data/navidrome
        docker run -d --name navidrome -p 4533:4533 \
            -v "$PWD/data/navidrome:/data" \
            -v "$HOME/Music:/music:ro" deluan/navidrome:latest
    else
        echo "Navidrome container already exists. Skipping installation."
    fi
}

# Ensure Python 3 is available
if ! command_exists python3; then
    echo "Python 3 is required. Please install it and rerun this script." >&2
    exit 1
fi

# Install dependencies
python3 -m pip install --user -r requirements.txt

# Pull and run Navidrome if Docker is available and container isn't already present
if command_exists docker; then
    install_navidrome
else
    echo "Docker not found. Please install Docker to enable the local music server." >&2
fi

# Install Ollama for local LLMs if missing
if ! command_exists ollama; then
    echo "Installing Ollama..."
    case "$PLATFORM" in
        mac|linux)
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        *)
            echo "Please install Ollama manually from https://ollama.ai" >&2
            ;;
    esac
fi

echo "Setup complete! Edit the .env file with your API keys and run 'python start.py' to launch AI DJ."

# End of script
