#!/usr/bin/env bash
# Quick setup script for AI DJ
set -e

echo "=== AI DJ Setup ==="

OS="$(uname)"
case "$OS" in
    Darwin*) PLATFORM="mac";;
    Linux*) PLATFORM="linux";;
    *) PLATFORM="other";;
esac

# Ensure Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Please install it and rerun this script." >&2
    exit 1
fi

# Install dependencies
python3 -m pip install --user -r requirements.txt

# Pull and run Navidrome if Docker is available
if command -v docker >/dev/null 2>&1; then
    echo "Setting up Navidrome music server..."
    docker pull deluan/navidrome:latest
    mkdir -p data/navidrome
    docker run -d --name navidrome -p 4533:4533 \
        -v "$PWD/data/navidrome:/data" \
        -v "$HOME/Music:/music:ro" deluan/navidrome:latest || true
else
    echo "Docker not found. Please install Docker to enable the local music server." >&2
fi

# Install Ollama for local LLMs
if ! command -v ollama >/dev/null 2>&1; then
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
