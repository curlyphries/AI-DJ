document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
    
    // Update system status periodically
    setInterval(updateSystemStatus, 10000);
});

// Global variables
let currentPlaylist = null;
let currentSong = null;
let audioPlayer = document.getElementById('audio-player');
let isPlaying = false;

/**
 * Initialize the application
 */
function initApp() {
    console.log('Initializing AI DJ Assistant...');
    
    // Check if API keys are set
    checkApiKeys();
    
    // Load settings from localStorage
    loadSettings();
}

/**
 * Set up event listeners for UI elements
 */
function setupEventListeners() {
    // Navigation links
    document.getElementById('dashboard-link').addEventListener('click', () => showSection('dashboard'));
    document.getElementById('playlists-link').addEventListener('click', () => showSection('playlists'));
    document.getElementById('trends-link').addEventListener('click', () => showSection('trends'));
    document.getElementById('voice-link').addEventListener('click', () => showSection('voice'));
    document.getElementById('settings-link').addEventListener('click', () => showSection('settings'));
    
    // Dashboard buttons
    document.getElementById('refresh-btn').addEventListener('click', refreshDashboard);
    document.getElementById('navidrome-btn').addEventListener('click', openNavidrome);
    document.getElementById('playlist-form').addEventListener('submit', createPlaylist);
    document.getElementById('refresh-trends-btn').addEventListener('click', loadTrends);
    
    // Player controls
    document.getElementById('play-pause-btn').addEventListener('click', togglePlayPause);
    document.getElementById('prev-btn').addEventListener('click', playPreviousSong);
    document.getElementById('next-btn').addEventListener('click', playNextSong);
    document.getElementById('dj-intro-btn').addEventListener('click', playDjIntro);
    document.getElementById('open-player-btn').addEventListener('click', openNavidrome);
    
    // Trends analysis
    document.getElementById('analyze-trends-btn').addEventListener('click', analyzeTrends);
    
    // Voice DJ
    document.getElementById('speak-btn').addEventListener('click', speakCustomText);
    
    // Settings forms
    document.getElementById('api-settings-form').addEventListener('submit', saveApiSettings);
    document.getElementById('navidrome-settings-form').addEventListener('submit', saveNavidromeSettings);
    
    // Settings switches
    document.getElementById('dark-mode-switch').addEventListener('change', toggleDarkMode);
    document.getElementById('resource-limit-switch').addEventListener('change', toggleResourceLimit);
    document.getElementById('startup-switch').addEventListener('change', toggleStartup);
    
    // Audio player events
    audioPlayer.addEventListener('timeupdate', updateProgressBar);
    audioPlayer.addEventListener('ended', playNextSong);
}

/**
 * Load initial data for the dashboard
 */
function loadInitialData() {
    // Load playlists
    loadPlaylists();
    
    // Load recent activity
    loadRecentActivity();
    
    // Load trends
    loadTrends();
    
    // Check now playing
    checkNowPlaying();
    
    // Load DJ voices
    loadVoices();
}

/**
 * Show a specific section and hide others
 * @param {string} sectionName - Name of the section to show
 */
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Show the selected section
    document.getElementById(`${sectionName}-content`).classList.remove('d-none');
    
    // Update active link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.getElementById(`${sectionName}-link`).classList.add('active');
    
    // Load section-specific data
    if (sectionName === 'playlists') {
        loadPlaylists();
    } else if (sectionName === 'trends') {
        loadTrends();
    } else if (sectionName === 'voice') {
        loadVoices();
        loadDjHistory();
    }
}

/**
 * Check if API keys are set
 */
function checkApiKeys() {
    const openaiKey = localStorage.getItem('openai_api_key');
    const elevenlabsKey = localStorage.getItem('elevenlabs_api_key');
    
    if (!openaiKey || !elevenlabsKey) {
        showToast('Please set your API keys in Settings', 'warning');
    }
}

/**
 * Load settings from localStorage
 */
function loadSettings() {
    // Load API keys
    document.getElementById('openai-key').value = localStorage.getItem('openai_api_key') || '';
    document.getElementById('elevenlabs-key').value = localStorage.getItem('elevenlabs_api_key') || '';
    document.getElementById('lastfm-key').value = localStorage.getItem('lastfm_api_key') || '';
    document.getElementById('spotify-id').value = localStorage.getItem('spotify_client_id') || '';
    document.getElementById('spotify-secret').value = localStorage.getItem('spotify_client_secret') || '';
    
    // Load Navidrome settings
    document.getElementById('navidrome-url').value = localStorage.getItem('navidrome_url') || 'http://localhost:4533';
    document.getElementById('navidrome-user').value = localStorage.getItem('navidrome_username') || '';
    document.getElementById('navidrome-pass').value = localStorage.getItem('navidrome_password') || '';
    
    // Load switches
    document.getElementById('dark-mode-switch').checked = localStorage.getItem('dark_mode') !== 'false';
    document.getElementById('resource-limit-switch').checked = localStorage.getItem('resource_limit') !== 'false';
    document.getElementById('startup-switch').checked = localStorage.getItem('start_with_system') === 'true';
    document.getElementById('auto-intro-switch').checked = localStorage.getItem('auto_intro') !== 'false';
    document.getElementById('trivia-switch').checked = localStorage.getItem('include_trivia') !== 'false';
    document.getElementById('announce-trends-switch').checked = localStorage.getItem('announce_trends') === 'true';
}

/**
 * Save API settings
 * @param {Event} e - Form submit event
 */
function saveApiSettings(e) {
    e.preventDefault();
    
    localStorage.setItem('openai_api_key', document.getElementById('openai-key').value);
    localStorage.setItem('elevenlabs_api_key', document.getElementById('elevenlabs-key').value);
    localStorage.setItem('lastfm_api_key', document.getElementById('lastfm-key').value);
    localStorage.setItem('spotify_client_id', document.getElementById('spotify-id').value);
    localStorage.setItem('spotify_client_secret', document.getElementById('spotify-secret').value);
    
    showToast('API settings saved successfully', 'success');
    
    // Update server with new settings
    updateServerSettings();
}

/**
 * Save Navidrome settings
 * @param {Event} e - Form submit event
 */
function saveNavidromeSettings(e) {
    e.preventDefault();
    
    localStorage.setItem('navidrome_url', document.getElementById('navidrome-url').value);
    localStorage.setItem('navidrome_username', document.getElementById('navidrome-user').value);
    localStorage.setItem('navidrome_password', document.getElementById('navidrome-pass').value);
    
    showToast('Navidrome settings saved successfully', 'success');
    
    // Update server with new settings
    updateServerSettings();
}

/**
 * Update server with settings from localStorage
 */
function updateServerSettings() {
    const settings = {
        openai_api_key: localStorage.getItem('openai_api_key'),
        elevenlabs_api_key: localStorage.getItem('elevenlabs_api_key'),
        lastfm_api_key: localStorage.getItem('lastfm_api_key'),
        spotify_client_id: localStorage.getItem('spotify_client_id'),
        spotify_client_secret: localStorage.getItem('spotify_client_secret'),
        navidrome_url: localStorage.getItem('navidrome_url'),
        navidrome_username: localStorage.getItem('navidrome_username'),
        navidrome_password: localStorage.getItem('navidrome_password')
    };
    
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Server settings updated');
        } else {
            console.error('Failed to update server settings:', data.error);
        }
    })
    .catch(error => {
        console.error('Error updating server settings:', error);
    });
}

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (success, warning, error)
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type === 'error' ? 'danger' : type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    const toastHeader = document.createElement('div');
    toastHeader.className = 'toast-header';
    
    const title = document.createElement('strong');
    title.className = 'me-auto';
    title.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close';
    closeButton.setAttribute('data-bs-dismiss', 'toast');
    closeButton.setAttribute('aria-label', 'Close');
    
    toastHeader.appendChild(title);
    toastHeader.appendChild(closeButton);
    
    const toastBody = document.createElement('div');
    toastBody.className = 'toast-body';
    toastBody.textContent = message;
    
    toast.appendChild(toastHeader);
    toast.appendChild(toastBody);
    
    toastContainer.appendChild(toast);
    
    // Remove toast after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

/**
 * Update system status (CPU and RAM usage)
 */
function updateSystemStatus() {
    fetch('/api/system_status')
    .then(response => response.json())
    .then(data => {
        document.getElementById('cpu-usage').textContent = `CPU: ${data.cpu_usage}%`;
        document.getElementById('ram-usage').textContent = `RAM: ${data.ram_usage}%`;
        
        // Warn if usage is too high
        if (data.cpu_usage > 50 || data.ram_usage > 50) {
            showToast('System resource usage is high', 'warning');
        }
    })
    .catch(error => {
        console.error('Error fetching system status:', error);
    });
}

// More functions will be implemented in api.js
