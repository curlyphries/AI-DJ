Write-Host "=== AI DJ Setup ==="

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3 is required. Please install it then rerun this script." -ForegroundColor Red
    exit 1
}

python -m pip install -r requirements.txt

# Pull and run Navidrome via Docker if available
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Setting up Navidrome music server..."
    docker pull deluan/navidrome:latest
    New-Item -ItemType Directory -Force -Path "data/navidrome" | Out-Null
    docker run -d --name navidrome -p 4533:4533 -v "$PWD/data/navidrome:/data" -v "$env:USERPROFILE\Music:/music:ro" deluan/navidrome:latest | Out-Null
} else {
    Write-Host "Docker not found. Install Docker Desktop to enable the local music server." -ForegroundColor Yellow
}

# Ollama installation hint
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Please install Ollama manually from https://ollama.ai" -ForegroundColor Yellow
}

Write-Host "Setup complete! Edit the .env file with your API keys and run 'python start.py' to launch AI DJ." -ForegroundColor Green
