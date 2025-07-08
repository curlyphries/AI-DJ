#!/usr/bin/env bash
# Quick setup script for AI DJ. Designed for beginners and idempotent so it can
# be safely re-run. The script installs Python requirements and optional
# services (Navidrome and Ollama) only if they are not already present.
set -euo pipefail

# Logging setup
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/install.log"
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

log_msg() {
    # $1: message to log
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to prompt user with a yes/no question
confirm() {
    # $1: message
    read -r -p "$1 [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]
}

log_msg "=== AI DJ Setup ==="

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

# Check for a required command and print installation guidance
check_dependency() {
    local cmd="$1"
    if ! command_exists "$cmd"; then
        log_msg "Missing dependency: $cmd"
        echo "\n'$cmd' is not installed." >&2
        case "$cmd" in
            docker)
                echo "Please install Docker: https://docs.docker.com/get-docker/" >&2
                ;;
            curl)
                echo "Install curl using your package manager, e.g., 'sudo apt install curl'" >&2
                ;;
            python3)
                echo "Python 3 is required. Please install it and rerun this script." >&2
                exit 1
                ;;
        esac
        return 1
    else
        log_msg "Found dependency: $cmd"
    fi
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

# Check core dependencies
check_dependency python3
check_dependency curl
check_dependency docker || true

# Helper to install Navidrome only when the container is not already running
install_navidrome() {
    log_msg "Setting up Navidrome music server..."
    if docker ps -a --format '{{.Names}}' | grep -q '^navidrome$'; then
        log_msg "Navidrome container already exists."
        if confirm "Reinstall Navidrome container?"; then
            docker stop navidrome >/dev/null 2>&1 || true
            docker rm navidrome >/dev/null 2>&1 || true
        else
            log_msg "Skipping Navidrome installation."
            return
        fi
    elif port_in_use 4533; then
        log_msg "Port 4533 is already in use."
        if ! confirm "Continue with Navidrome installation anyway?"; then
            log_msg "Skipping Navidrome installation due to port conflict."
            return
        fi
    fi

    log_msg "Pulling Navidrome Docker image..."
    docker pull deluan/navidrome:latest 2>&1 | tee -a "$LOG_FILE"
    mkdir -p data/navidrome
    docker run -d --name navidrome -p 4533:4533 \
        -v "$PWD/data/navidrome:/data" \
        -v "$HOME/Music:/music:ro" deluan/navidrome:latest 2>&1 | tee -a "$LOG_FILE"
}

# Install dependencies (assumes you are running inside a virtual environment)
log_msg "Installing Python packages..."
python3 -m pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"

# Pull and run Navidrome if Docker is available and container isn't already present
if command_exists docker; then
    install_navidrome
else
    log_msg "Docker not found. Please install Docker to enable the local music server." >&2
fi

# Install Ollama for local LLMs
install_ollama() {
    if command_exists ollama; then
        if ! confirm "Ollama is already installed. Reinstall/upgrade?"; then
            log_msg "Skipping Ollama installation."
            return
        fi
    fi

    log_msg "Installing Ollama..."
    case "$PLATFORM" in
        mac|linux)
            curl -fsSL https://ollama.ai/install.sh | sh 2>&1 | tee -a "$LOG_FILE"
            ;;
        *)
            log_msg "Please install Ollama manually from https://ollama.ai" >&2
            ;;
    esac
}

install_ollama

log_msg "Setup complete! Edit the .env file with your API keys and run 'python start.py' to launch AI DJ."

# End of script
