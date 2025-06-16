/**
 * AI DJ - DJ Interaction Module
 * Handles user interactions with the AI DJ system
 */

// Global variables
let recognition = null;
let isListening = false;
let requestQueue = [];
let isProcessingRequest = false;
let userId = localStorage.getItem('dj_user_id') || generateUserId();
let userStatus = 'active';
let warningCount = 0;
let mutedUntil = null;
let suspendedUntil = null;
let activeDjProfile = null;

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initDJInteraction();
});

/**
 * Initialize DJ interaction components
 */
function initDJInteraction() {
    // Initialize speech recognition if available
    initSpeechRecognition();
    
    // Add event listeners
    document.getElementById('send-request-btn').addEventListener('click', sendDJRequest);
    document.getElementById('voice-input-btn').addEventListener('click', toggleVoiceInput);
    document.getElementById('dj-request-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendDJRequest();
        }
    });
    
    // Quick action buttons
    document.getElementById('trivia-btn').addEventListener('click', function() {
        document.getElementById('dj-request-input').value = "Tell me some music trivia";
        sendDJRequest();
    });
    
    document.getElementById('song-fact-btn').addEventListener('click', function() {
        document.getElementById('dj-request-input').value = "Tell me a fun fact about the current song";
        sendDJRequest();
    });
    
    document.getElementById('play-song-btn').addEventListener('click', function() {
        document.getElementById('dj-request-input').value = "Play a song that sounds like The Beatles";
        sendDJRequest();
    });
    
    document.getElementById('create-playlist-btn').addEventListener('click', function() {
        document.getElementById('dj-request-input').value = "Create a playlist for a road trip";
        sendDJRequest();
    });
    
    // Add settings button to DJ interaction container
    addSettingsButton();
    
    // Load active DJ profile
    loadActiveDjProfile();
    
    // Check user status
    checkUserStatus();
    
    // Start processing queue
    setInterval(processRequestQueue, 1000);
    
    // Periodically check user status (every 10 seconds)
    setInterval(checkUserStatus, 10000);
}

/**
 * Add settings button to DJ interaction container
 */
function addSettingsButton() {
    const container = document.querySelector('.dj-interaction-container .card-header');
    if (container) {
        const settingsBtn = document.createElement('a');
        settingsBtn.href = '/settings';
        settingsBtn.className = 'btn btn-sm btn-outline-light ms-2';
        settingsBtn.innerHTML = '<i class="fas fa-cog"></i> Settings';
        
        // Find the title element
        const title = container.querySelector('h3') || container.querySelector('h4');
        if (title) {
            // Create a container for the title and button
            const headerContainer = document.createElement('div');
            headerContainer.className = 'd-flex justify-content-between align-items-center';
            
            // Move the title to the container
            title.parentNode.insertBefore(headerContainer, title);
            headerContainer.appendChild(title);
            
            // Add the button to the container
            headerContainer.appendChild(settingsBtn);
        } else {
            // Just append to the end if no title found
            container.appendChild(settingsBtn);
        }
    }
}

/**
 * Load active DJ profile
 */
function loadActiveDjProfile() {
    fetch(`/api/active_dj_profile?user_id=${userId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    // No active profile, that's okay
                    return null;
                }
                throw new Error('Failed to load active DJ profile');
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                activeDjProfile = data;
                console.log('Active DJ profile loaded:', activeDjProfile);
                
                // Update UI to show active profile
                updateActiveDjProfileDisplay();
            }
        })
        .catch(error => {
            console.error('Error loading active DJ profile:', error);
        });
}

/**
 * Update active DJ profile display
 */
function updateActiveDjProfileDisplay() {
    if (!activeDjProfile) return;
    
    const container = document.querySelector('.dj-interaction-container .card-header');
    if (container) {
        // Check if profile display already exists
        let profileDisplay = container.querySelector('.active-dj-profile');
        
        if (!profileDisplay) {
            // Create profile display
            profileDisplay = document.createElement('div');
            profileDisplay.className = 'active-dj-profile mt-2 text-center';
            container.appendChild(profileDisplay);
        }
        
        // Update profile display
        profileDisplay.innerHTML = `
            <small class="text-muted">
                Active DJ: <span class="badge bg-success">${activeDjProfile.name}</span>
            </small>
        `;
    }
}

/**
 * Generate a unique user ID
 */
function generateUserId() {
    const id = 'user_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('dj_user_id', id);
    return id;
}

/**
 * Check user status
 */
function checkUserStatus() {
    fetch(`/api/user_status/${userId}`)
        .then(response => response.json())
        .then(data => {
            userStatus = data.status;
            warningCount = data.warnings || 0;
            mutedUntil = data.muted_until;
            suspendedUntil = data.suspended_until;
            
            updateUserStatusDisplay();
        })
        .catch(error => {
            console.error('Error checking user status:', error);
        });
}

/**
 * Update user status display
 */
function updateUserStatusDisplay() {
    const statusContainer = document.createElement('div');
    statusContainer.id = 'user-status-container';
    statusContainer.className = 'mt-2 text-center';
    
    let statusHtml = '';
    const currentTime = Math.floor(Date.now() / 1000);
    
    if (userStatus === 'suspended' && suspendedUntil && suspendedUntil > currentTime) {
        const timeLeft = suspendedUntil - currentTime;
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        statusHtml = `
            <div class="alert alert-danger">
                <i class="fas fa-ban me-2"></i>
                Your account is suspended. Please try again in ${minutes}m ${seconds}s.
            </div>
        `;
    } else if (userStatus === 'muted' && mutedUntil && mutedUntil > currentTime) {
        const timeLeft = mutedUntil - currentTime;
        
        statusHtml = `
            <div class="alert alert-warning">
                <i class="fas fa-volume-mute me-2"></i>
                You've been muted for non-music content. You can try again in ${timeLeft}s.
            </div>
        `;
    } else if (warningCount > 0) {
        statusHtml = `
            <div class="alert alert-info">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Warning: Please keep requests music-related (${warningCount}/2 warnings).
            </div>
        `;
    }
    
    // Only update if there's status to show
    if (statusHtml) {
        // Remove existing status container if present
        const existingContainer = document.getElementById('user-status-container');
        if (existingContainer) {
            existingContainer.remove();
        }
        
        // Add new status container
        statusContainer.innerHTML = statusHtml;
        const chatContainer = document.getElementById('dj-chat-container');
        chatContainer.parentNode.insertBefore(statusContainer, chatContainer);
    } else {
        // Remove existing status container if present and no status to show
        const existingContainer = document.getElementById('user-status-container');
        if (existingContainer) {
            existingContainer.remove();
        }
    }
    
    // Disable/enable input based on status
    const requestInput = document.getElementById('dj-request-input');
    const sendButton = document.getElementById('send-request-btn');
    const voiceButton = document.getElementById('voice-input-btn');
    const quickButtons = document.querySelectorAll('.card-body .btn-outline-primary');
    
    if (userStatus === 'suspended' || userStatus === 'muted') {
        requestInput.disabled = true;
        sendButton.disabled = true;
        voiceButton.disabled = true;
        quickButtons.forEach(btn => btn.disabled = true);
    } else {
        requestInput.disabled = false;
        sendButton.disabled = false;
        voiceButton.disabled = false;
        quickButtons.forEach(btn => btn.disabled = false);
    }
}

/**
 * Initialize speech recognition
 */
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('dj-request-input').value = transcript;
            sendDJRequest();
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            isListening = false;
            updateVoiceButtonState();
        };
        
        recognition.onend = function() {
            isListening = false;
            updateVoiceButtonState();
        };
    } else {
        document.getElementById('voice-input-btn').disabled = true;
        document.getElementById('voice-input-btn').title = 'Speech recognition not supported in this browser';
    }
}

/**
 * Toggle voice input
 */
function toggleVoiceInput() {
    if (!recognition) return;
    
    if (isListening) {
        recognition.stop();
        isListening = false;
    } else {
        recognition.start();
        isListening = true;
    }
    
    updateVoiceButtonState();
}

/**
 * Update voice button state
 */
function updateVoiceButtonState() {
    const btn = document.getElementById('voice-input-btn');
    
    if (isListening) {
        btn.classList.add('btn-danger');
        btn.classList.remove('btn-outline-primary');
        btn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
    } else {
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-outline-primary');
        btn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
}

/**
 * Send DJ request
 */
function sendDJRequest() {
    const input = document.getElementById('dj-request-input');
    const request = input.value.trim();
    
    if (request === '') return;
    
    // Check if user is allowed to interact
    if (userStatus === 'suspended' || userStatus === 'muted') {
        updateUserStatusDisplay();
        return;
    }
    
    // Add user message to chat
    addMessageToChat('user', request);
    
    // Add to request queue
    requestQueue.push(request);
    updateRequestQueue();
    
    // Clear input
    input.value = '';
}

/**
 * Add message to chat
 * @param {string} sender - 'user' or 'dj'
 * @param {string} message - Message text
 * @param {string} audioUrl - Optional URL to audio file
 * @param {string} messageType - Optional message type ('normal', 'warning', 'error')
 */
function addMessageToChat(sender, message, audioUrl = null, messageType = 'normal') {
    const chatContainer = document.getElementById('dj-chat-container');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = sender === 'user' ? 'user-message' : 'dj-message';
    
    // Add additional classes based on message type
    if (sender === 'dj' && messageType === 'warning') {
        messageDiv.classList.add('dj-message-warning');
    } else if (sender === 'dj' && messageType === 'error') {
        messageDiv.classList.add('dj-message-error');
    }
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${message}</p>
            ${audioUrl ? `<audio controls src="${audioUrl}" class="w-100 mt-2"></audio>` : ''}
        </div>
        <small class="text-muted">${timestamp}</small>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Update request queue display
 */
function updateRequestQueue() {
    const queueContainer = document.getElementById('request-queue');
    
    if (requestQueue.length === 0) {
        queueContainer.innerHTML = '<p class="text-muted">No pending requests</p>';
        return;
    }
    
    let html = '<ul class="list-group list-group-flush bg-transparent">';
    
    requestQueue.forEach((request, index) => {
        html += `
            <li class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
                <span class="text-truncate">${request}</span>
                <button class="btn btn-sm btn-outline-danger remove-request" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            </li>
        `;
    });
    
    html += '</ul>';
    queueContainer.innerHTML = html;
    
    // Add event listeners to remove buttons
    document.querySelectorAll('.remove-request').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.getAttribute('data-index'));
            requestQueue.splice(index, 1);
            updateRequestQueue();
        });
    });
}

/**
 * Process request queue
 */
function processRequestQueue() {
    if (isProcessingRequest || requestQueue.length === 0) return;
    
    // Check if user is allowed to interact
    if (userStatus === 'suspended' || userStatus === 'muted') {
        updateUserStatusDisplay();
        return;
    }
    
    isProcessingRequest = true;
    const request = requestQueue.shift();
    updateRequestQueue();
    
    // Show loading message
    addMessageToChat('dj', '<i class="fas fa-spinner fa-spin"></i> Processing your request...');
    
    // Send request to server
    fetch('/api/dj_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            request: request,
            user_id: userId,
            tone: localStorage.getItem('ai_dj_response_tone') || 'default',
            voice_speed: parseFloat(localStorage.getItem('ai_dj_voice_speed') || '1'),
            context: {
                now_playing: getCurrentSongInfo(),
                dj_profile: activeDjProfile ? activeDjProfile.id : null
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        const chatContainer = document.getElementById('dj-chat-container');
        chatContainer.removeChild(chatContainer.lastChild);
        
        if (data.success) {
            // Add DJ response to chat
            addMessageToChat('dj', data.response, data.audio_path);
            
            // Play audio if available
            if (data.audio_path) {
                const audioPlayer = document.getElementById('audio-player');
                audioPlayer.src = data.audio_path;
                audioPlayer.play();
            }
        } else {
            // Handle moderation response
            if (data.warnings !== undefined) {
                warningCount = data.warnings;
                addMessageToChat('dj', data.response, null, 'warning');
                updateUserStatusDisplay();
            } else if (data.muted_until || data.suspended_until) {
                mutedUntil = data.muted_until;
                suspendedUntil = data.suspended_until;
                userStatus = data.muted_until ? 'muted' : 'suspended';
                addMessageToChat('dj', data.response, null, 'error');
                updateUserStatusDisplay();
            } else {
                // General error
                addMessageToChat('dj', data.error || 'Sorry, I encountered an error processing your request.', null, 'error');
            }
        }
        
        isProcessingRequest = false;
    })
    .catch(error => {
        console.error('Error processing DJ request:', error);
        
        // Remove loading message
        const chatContainer = document.getElementById('dj-chat-container');
        chatContainer.removeChild(chatContainer.lastChild);
        
        // Add error message
        addMessageToChat('dj', 'Sorry, I encountered an error processing your request. Please try again.', null, 'error');
        
        isProcessingRequest = false;
    });
}

/**
 * Get current song information
 * @returns {Object} Current song info or null
 */
function getCurrentSongInfo() {
    const currentSong = document.getElementById('current-song');
    
    if (currentSong.classList.contains('d-none')) {
        return null;
    }
    
    return {
        title: document.getElementById('current-song-title').textContent,
        artist: document.getElementById('current-song-artist').textContent
    };
}

/**
 * Export functions for use in other modules
 */
window.DJInteraction = {
    sendRequest: sendDJRequest,
    addMessageToChat: addMessageToChat
};
