Write-Host "=== AI DJ Setup ==="

# This script installs the Python dependencies and optional services needed for
# AI DJ. It is safe to rerun as it checks whether Docker containers or tools are
# already installed before attempting installation. Helpful comments are
# provided so junior administrators can understand each step.

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3 is required. Please install it then rerun this script." -ForegroundColor Red
    exit 1
}

python -m pip install -r requirements.txt

# Pull and run Navidrome via Docker if available and not already running
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $skipNavidrome = $false
    Write-Host "Setting up Navidrome music server..."
    $exists = docker ps -a --format '{{.Names}}' | Select-String -Pattern '^navidrome$'
    $portUsed = Get-NetTCPConnection -LocalPort 4533 -ErrorAction SilentlyContinue
    if ($exists) {
        $answer = Read-Host "Navidrome container already exists. Reinstall? (y/N)"
        if ($answer -match '^[Yy]$') {
            docker stop navidrome | Out-Null 2>&1
            docker rm navidrome | Out-Null 2>&1
        } else {
            Write-Host "Skipping Navidrome installation."
            $skipNavidrome = $true
        }
    } elseif ($portUsed) {
        $answer = Read-Host "Port 4533 is in use. Continue with installation? (y/N)"
        if ($answer -notmatch '^[Yy]$') {
            Write-Host "Skipping Navidrome installation due to port conflict."
            $skipNavidrome = $true
        }
    }

    if (-not $skipNavidrome) {
        docker pull deluan/navidrome:latest
        New-Item -ItemType Directory -Force -Path "data/navidrome" | Out-Null
        docker run -d --name navidrome -p 4533:4533 -v "$PWD/data/navidrome:/data" -v "$env:USERPROFILE\Music:/music:ro" deluan/navidrome:latest | Out-Null
    }
} else {
    Write-Host "Docker not found. Install Docker Desktop to enable the local music server." -ForegroundColor Yellow
}

# Ollama installation
function Install-Ollama {
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        $answer = Read-Host "Ollama already installed. Reinstall/upgrade? (y/N)"
        if ($answer -notmatch '^[Yy]$') {
            Write-Host "Skipping Ollama installation."
            return
        }
    }
    Write-Host "Installing Ollama..."
    Write-Host "Please follow the prompts from the installer." -ForegroundColor Yellow
    Invoke-Expression (Invoke-WebRequest -UseBasicParsing https://ollama.ai/install.ps1).Content
}

Install-Ollama

Write-Host "Setup complete! Edit the .env file with your API keys and run 'python start.py' to launch AI DJ." -ForegroundColor Green

# End of script
