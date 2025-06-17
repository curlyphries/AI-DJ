#!/usr/bin/env bash
# Quick setup script for AI DJ. Designed for beginners and idempotent so it can
# be safely re-run. The script installs Python requirements and optional
# services (Navidrome and Ollama) only if they are not already present.
set -euo pipefail

# Function to prompt user with a yes/no question
confirm() {
    # $1: message
    read -r -p "$1 [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]
}

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

# Check if a TCP port is already in use (requires lsof or netstat)
port_in_use() {
    local port="$1"
    if command_exists lsof; then
        lsof -i ":${port}" >/dev/null 2>&1
    elif command_exists netstat; then
        netstat -tuln | grep -q ":${port} "
    else
        return 1
    fi
}

# Helper to install Navidrome only when the container is not already running
install_navidrome() {
    echo "Setting up Navidrome music server..."
    if docker ps -a --format '{{.Names}}' | grep -q '^navidrome$'; then
        echo "Navidrome container already exists."
        if confirm "Reinstall Navidrome container?"; then
            docker stop navidrome >/dev/null 2>&1 || true
            docker rm navidrome >/dev/null 2>&1 || true
        else
            echo "Skipping Navidrome installation."
            return
        fi
    elif port_in_use 4533; then
        echo "Port 4533 is already in use."
        if ! confirm "Continue with Navidrome installation anyway?"; then
            echo "Skipping Navidrome installation due to port conflict."
            return
        fi
    fi

    docker pull deluan/navidrome:latest
    mkdir -p data/navidrome
    docker run -d --name navidrome -p 4533:4533 \
        -v "$PWD/data/navidrome:/data" \
        -v "$HOME/Music:/music:ro" deluan/navidrome:latest
}

# Ensure Python 3 is available
if ! command_exists python3; then
    echo "Python 3 is required. Please install it and rerun this script." >&2
    exit 1
fi

# Install dependencies (assumes you are running inside a virtual environment)
python3 -m pip install -r requirements.txt

# Pull and run Navidrome if Docker is available and container isn't already present
if command_exists docker; then
    install_navidrome
else
    echo "Docker not found. Please install Docker to enable the local music server." >&2
fi

# Install Ollama for local LLMs
install_ollama() {
    if command_exists ollama; then
        if ! confirm "Ollama is already installed. Reinstall/upgrade?"; then
            echo "Skipping Ollama installation."
            return
        fi
    fi

    echo "Installing Ollama..."
    case "$PLATFORM" in
        mac|linux)
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        *)
            echo "Please install Ollama manually from https://ollama.ai" >&2
            ;;
    esac
}

install_ollama

echo "Setup complete! Edit the .env file with your API keys and run 'python start.py' to launch AI DJ."

# End of script
