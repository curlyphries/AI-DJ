/**
 * AI DJ Settings Management
 * Handles API keys, DJ profiles, and user preferences
 */

// Global variables
let userId = localStorage.getItem('dj_user_id') || generateUserId();
let selectedVoiceId = null;
let selectedPersonalityId = null;
let availableVoices = [];
let availablePersonalities = [];

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if first-time user
    if (!localStorage.getItem('ai_dj_settings_initialized')) {
        document.getElementById('welcome-container').style.display = 'block';
        document.getElementById('settingsTabs').style.display = 'none';
        document.getElementById('settingsTabContent').style.display = 'none';
    }

    // Get Started button
    document.getElementById('get-started-btn').addEventListener('click', function() {
        document.getElementById('welcome-container').style.display = 'none';
        document.getElementById('settingsTabs').style.display = 'flex';
        document.getElementById('settingsTabContent').style.display = 'block';
        localStorage.setItem('ai_dj_settings_initialized', 'true');
    });

    // Initialize Bootstrap components
    const importModal = new bootstrap.Modal(document.getElementById('importModal'));
    const clearDataModal = new bootstrap.Modal(document.getElementById('clearDataModal'));
    
    // Initialize variables
    let selectedVoiceId = null;
    let selectedPersonalityId = null;
    const personalities = [
        { id: 'energetic', name: 'Energetic', description: 'High-energy, enthusiastic DJ who brings excitement to every announcement.' },
        { id: 'chill', name: 'Chill', description: 'Laid-back, smooth DJ with a relaxed vibe perfect for easy listening.' },
        { id: 'professional', name: 'Professional', description: 'Polished, informative DJ who focuses on music knowledge and facts.' },
        { id: 'humorous', name: 'Humorous', description: 'Fun, witty DJ who adds humor and jokes between tracks.' },
        { id: 'sassy', name: 'Sassy', description: 'Bold, opinionated DJ with attitude and strong music opinions.' }
    ];

    // Service help text
    const serviceHelpText = {
        'openai': 'Required for AI responses. Get your key at <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI</a>.',
        'elevenlabs': 'Required for voice generation. Get your key at <a href="https://elevenlabs.io/subscription" target="_blank">ElevenLabs</a>.',
        'lastfm': 'Optional for music data. Get your key at <a href="https://www.last.fm/api/account/create" target="_blank">Last.fm</a>.',
        'spotify': 'Optional for music recommendations. Get your credentials at <a href="https://developer.spotify.com/dashboard" target="_blank">Spotify</a>.',
        'navidrome': 'Optional for local music library. Enter your Navidrome server details.'
    };

    // Update service help text
    document.getElementById('service-select').addEventListener('change', function() {
        const service = this.value;
        const helpTextElement = document.getElementById('service-help-text');
        helpTextElement.innerHTML = serviceHelpText[service] || '';
    });

    // Load API Keys
    function loadApiKeys() {
        fetch('/settings/api-keys')
            .then(response => response.json())
            .then(data => {
                const apiKeysList = document.getElementById('api-keys-list');
                if (data.keys && Object.keys(data.keys).length > 0) {
                    let html = '';
                    for (const [service, apiKey] of Object.entries(data.keys)) {
                        const maskedKey = maskApiKey(apiKey);
                        html += `
                            <div class="api-key-item">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <h5 class="mb-0 text-capitalize">${service}</h5>
                                    <div>
                                        <span class="btn-reveal me-3" data-service="${service}" data-key="${apiKey}">
                                            <i class="fas fa-eye"></i>
                                        </span>
                                        <span class="text-danger" style="cursor: pointer;" onclick="deleteApiKey('${service}')">
                                            <i class="fas fa-trash"></i>
                                        </span>
                                    </div>
                                </div>
                                <div class="api-key-masked" id="key-${service}">${maskedKey}</div>
                            </div>
                        `;
                    }
                    apiKeysList.innerHTML = html;
                    
                    // Add event listeners for reveal buttons
                    document.querySelectorAll('.btn-reveal').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const service = this.getAttribute('data-service');
                            const key = this.getAttribute('data-key');
                            const keyElement = document.getElementById(`key-${service}`);
                            
                            if (keyElement.textContent === key) {
                                keyElement.textContent = maskApiKey(key);
                                this.innerHTML = '<i class="fas fa-eye"></i>';
                            } else {
                                keyElement.textContent = key;
                                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
                            }
                        });
                    });
                } else {
                    apiKeysList.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i> No API keys found. Add your first API key using the form above.
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading API keys:', error);
                showAlert('Error loading API keys. Please try again.', 'danger');
            });
    }

    // Mask API Key
    function maskApiKey(apiKey) {
        if (apiKey.length <= 8) {
            return '••••••••';
        }
        return apiKey.substring(0, 4) + '••••••••••••' + apiKey.substring(apiKey.length - 4);
    }

    // Add/Update API Key
    document.getElementById('api-key-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const service = document.getElementById('service-select').value;
        const apiKey = document.getElementById('api-key-input').value;
        
        if (!service || !apiKey) {
            showAlert('Please select a service and enter an API key.', 'warning');
            return;
        }
        
        fetch('/settings/api-keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service: service,
                api_key: apiKey
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`${service.charAt(0).toUpperCase() + service.slice(1)} API key saved successfully.`, 'success');
                document.getElementById('api-key-form').reset();
                loadApiKeys();
            } else {
                showAlert(data.message || 'Error saving API key.', 'danger');
            }
        })
        .catch(error => {
            console.error('Error saving API key:', error);
            showAlert('Error saving API key. Please try again.', 'danger');
        });
    });

    // Delete API Key
    window.deleteApiKey = function(service) {
        if (confirm(`Are you sure you want to delete the ${service} API key?`)) {
            fetch(`/settings/api-keys/${service}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(`${service.charAt(0).toUpperCase() + service.slice(1)} API key deleted successfully.`, 'success');
                    loadApiKeys();
                } else {
                    showAlert(data.message || 'Error deleting API key.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error deleting API key:', error);
                showAlert('Error deleting API key. Please try again.', 'danger');
            });
        }
    };

    // Refresh API Keys
    document.getElementById('refresh-keys-btn').addEventListener('click', function() {
        loadApiKeys();
    });

    // Load DJ Profiles
    function loadDjProfiles() {
        fetch('/settings/dj-profiles')
            .then(response => response.json())
            .then(data => {
                const profilesList = document.getElementById('dj-profiles-list');
                if (data.profiles && data.profiles.length > 0) {
                    let html = '';
                    data.profiles.forEach(profile => {
                        const isActive = profile.active ? 'active' : '';
                        html += `
                            <div class="col-md-6 col-lg-4 mb-4">
                                <div class="profile-card ${isActive}">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h4 class="mb-0">${profile.name}</h4>
                                        <div class="dropdown">
                                            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                                                <i class="fas fa-ellipsis-v"></i>
                                            </button>
                                            <ul class="dropdown-menu dropdown-menu-dark">
                                                <li><a class="dropdown-item" href="#" onclick="activateProfile('${profile.id}')">
                                                    <i class="fas fa-check-circle me-2"></i> Set as Active
                                                </a></li>
                                                <li><a class="dropdown-item" href="#" onclick="editProfile('${profile.id}')">
                                                    <i class="fas fa-edit me-2"></i> Edit
                                                </a></li>
                                                <li><a class="dropdown-item" href="#" onclick="deleteProfile('${profile.id}')">
                                                    <i class="fas fa-trash me-2"></i> Delete
                                                </a></li>
                                            </ul>
                                        </div>
                                    </div>
                                    <div class="mb-2">
                                        <span class="badge bg-primary me-2">Voice: ${profile.voice_name}</span>
                                        <span class="badge bg-secondary">${profile.personality_type}</span>
                                    </div>
                                    <p class="text-muted small mb-2">${profile.description.substring(0, 100)}${profile.description.length > 100 ? '...' : ''}</p>
                                    ${profile.active ? '<div class="text-success mt-2"><i class="fas fa-check-circle me-1"></i> Active Profile</div>' : ''}
                                </div>
                            </div>
                        `;
                    });
                    profilesList.innerHTML = html;
                } else {
                    profilesList.innerHTML = `
                        <div class="col-12">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i> No DJ profiles found. Create your first profile using the "Create DJ Profile" tab.
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading DJ profiles:', error);
                showAlert('Error loading DJ profiles. Please try again.', 'danger');
            });
    }

    // Activate Profile
    window.activateProfile = function(profileId) {
        fetch(`/settings/dj-profiles/${profileId}/activate`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('DJ profile activated successfully.', 'success');
                loadDjProfiles();
            } else {
                showAlert(data.message || 'Error activating DJ profile.', 'danger');
            }
        })
        .catch(error => {
            console.error('Error activating DJ profile:', error);
            showAlert('Error activating DJ profile. Please try again.', 'danger');
        });
    };

    // Edit Profile
    window.editProfile = function(profileId) {
        // Redirect to edit page or show edit modal
        document.getElementById('create-profile-tab').click();
        // Load profile data and populate form
        fetch(`/settings/dj-profiles/${profileId}`)
            .then(response => response.json())
            .then(data => {
                if (data.profile) {
                    const profile = data.profile;
                    document.getElementById('profile-name').value = profile.name;
                    selectedVoiceId = profile.voice_id;
                    selectedPersonalityId = profile.personality_type;
                    
                    // Update UI to reflect selections
                    setTimeout(() => {
                        if (document.querySelector(`.voice-card[data-voice-id="${selectedVoiceId}"]`)) {
                            document.querySelector(`.voice-card[data-voice-id="${selectedVoiceId}"]`).classList.add('selected');
                        }
                        
                        if (document.querySelector(`.personality-card[data-personality-id="${selectedPersonalityId}"]`)) {
                            document.querySelector(`.personality-card[data-personality-id="${selectedPersonalityId}"]`).classList.add('selected');
                        } else {
                            // Custom personality
                            document.getElementById('custom-personality-check').checked = true;
                            document.getElementById('custom-personality-container').style.display = 'block';
                            document.getElementById('custom-personality-input').value = profile.description;
                        }
                    }, 500);
                }
            })
            .catch(error => {
                console.error('Error loading profile for editing:', error);
                showAlert('Error loading profile for editing. Please try again.', 'danger');
            });
    };

    // Delete Profile
    window.deleteProfile = function(profileId) {
        if (confirm('Are you sure you want to delete this DJ profile?')) {
            fetch(`/settings/dj-profiles/${profileId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('DJ profile deleted successfully.', 'success');
                    loadDjProfiles();
                } else {
                    showAlert(data.message || 'Error deleting DJ profile.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error deleting DJ profile:', error);
                showAlert('Error deleting DJ profile. Please try again.', 'danger');
            });
        }
    };

    // Load Voices
    function loadVoices() {
        fetch('/settings/voices')
            .then(response => response.json())
            .then(data => {
                const voicesContainer = document.getElementById('voices-container');
                if (data.voices && data.voices.length > 0) {
                    let html = '';
                    data.voices.forEach(voice => {
                        html += `
                            <div class="col-md-6 col-lg-4 mb-4">
                                <div class="card voice-card" data-voice-id="${voice.voice_id}">
                                    <div class="card-body">
                                        <h5 class="card-title">${voice.name}</h5>
                                        <p class="card-text text-muted small">${voice.description || 'No description available'}</p>
                                        <audio controls class="w-100 mt-2">
                                            <source src="${voice.preview_url}" type="audio/mpeg">
                                            Your browser does not support the audio element.
                                        </audio>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    voicesContainer.innerHTML = html;
                    
                    // Add event listeners for voice selection
                    document.querySelectorAll('.voice-card').forEach(card => {
                        card.addEventListener('click', function() {
                            document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
                            this.classList.add('selected');
                            selectedVoiceId = this.getAttribute('data-voice-id');
                        });
                    });
                } else {
                    voicesContainer.innerHTML = `
                        <div class="col-12">
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle me-2"></i> No voices found. Please add your ElevenLabs API key first.
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading voices:', error);
                showAlert('Error loading voices. Please try again.', 'danger');
            });
    }

    // Load Personalities
    function loadPersonalities() {
        const personalitiesContainer = document.getElementById('personalities-container');
        let html = '';
        personalities.forEach(personality => {
            html += `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card personality-card" data-personality-id="${personality.id}">
                        <div class="card-body">
                            <h5 class="card-title">${personality.name}</h5>
                            <p class="card-text">${personality.description}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        personalitiesContainer.innerHTML = html;
        
        // Add event listeners for personality selection
        document.querySelectorAll('.personality-card').forEach(card => {
            card.addEventListener('click', function() {
                document.querySelectorAll('.personality-card').forEach(c => c.classList.remove('selected'));
                this.classList.add('selected');
                selectedPersonalityId = this.getAttribute('data-personality-id');
                
                // Uncheck custom personality
                document.getElementById('custom-personality-check').checked = false;
                document.getElementById('custom-personality-container').style.display = 'none';
            });
        });
    }

    // Custom Personality Toggle
    document.getElementById('custom-personality-check').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('custom-personality-container').style.display = 'block';
            document.querySelectorAll('.personality-card').forEach(c => c.classList.remove('selected'));
            selectedPersonalityId = 'custom';
        } else {
            document.getElementById('custom-personality-container').style.display = 'none';
            selectedPersonalityId = null;
        }
    });

    // Create DJ Profile
    document.getElementById('create-profile-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const profileName = document.getElementById('profile-name').value;
        
        if (!profileName) {
            showAlert('Please enter a profile name.', 'warning');
            return;
        }
        
        if (!selectedVoiceId) {
            showAlert('Please select a voice for your DJ.', 'warning');
            return;
        }
        
        if (!selectedPersonalityId) {
            showAlert('Please select a personality for your DJ.', 'warning');
            return;
        }
        
        let personalityDescription = '';
        if (selectedPersonalityId === 'custom') {
            personalityDescription = document.getElementById('custom-personality-input').value;
            if (!personalityDescription) {
                showAlert('Please enter a custom personality description.', 'warning');
                return;
            }
        } else {
            // Find the selected personality from our array
            const selectedPersonality = personalities.find(p => p.id === selectedPersonalityId);
            personalityDescription = selectedPersonality ? selectedPersonality.description : '';
        }
        
        fetch('/settings/dj-profiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: profileName,
                voice_id: selectedVoiceId,
                personality_type: selectedPersonalityId,
                description: personalityDescription
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('DJ profile created successfully.', 'success');
                document.getElementById('create-profile-form').reset();
                document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
                document.querySelectorAll('.personality-card').forEach(c => c.classList.remove('selected'));
                document.getElementById('custom-personality-container').style.display = 'none';
                selectedVoiceId = null;
                selectedPersonalityId = null;
                
                // Switch to DJ Profiles tab
                document.getElementById('dj-profiles-tab').click();
                loadDjProfiles();
            } else {
                showAlert(data.message || 'Error creating DJ profile.', 'danger');
            }
        })
        .catch(error => {
            console.error('Error creating DJ profile:', error);
            showAlert('Error creating DJ profile. Please try again.', 'danger');
        });
    });

    // Export Settings
    document.getElementById('export-settings-btn').addEventListener('click', function() {
        fetch('/settings/export')
            .then(response => response.json())
            .then(data => {
                if (data.settings) {
                    // Create a download link
                    const blob = new Blob([JSON.stringify(data.settings, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'ai_dj_settings.json';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    showAlert('Settings exported successfully.', 'success');
                } else {
                    showAlert(data.message || 'Error exporting settings.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error exporting settings:', error);
                showAlert('Error exporting settings. Please try again.', 'danger');
            });
    });

    // Import Settings
    document.getElementById('import-settings-btn').addEventListener('click', function() {
        importModal.show();
    });

    document.getElementById('confirm-import-btn').addEventListener('click', function() {
        const fileInput = document.getElementById('import-file');
        if (!fileInput.files || fileInput.files.length === 0) {
            showAlert('Please select a file to import.', 'warning');
            return;
        }
        
        const file = fileInput.files[0];
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                const settings = JSON.parse(e.target.result);
                
                fetch('/settings/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ settings: settings })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('Settings imported successfully.', 'success');
                        importModal.hide();
                        fileInput.value = '';
                        
                        // Reload data
                        loadApiKeys();
                        loadDjProfiles();
                    } else {
                        showAlert(data.message || 'Error importing settings.', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error importing settings:', error);
                    showAlert('Error importing settings. Please try again.', 'danger');
                });
            } catch (error) {
                console.error('Error parsing settings file:', error);
                showAlert('Invalid settings file. Please select a valid JSON file.', 'danger');
            }
        };
        
        reader.readAsText(file);
    });

    // Clear Data
    document.getElementById('clear-data-btn').addEventListener('click', function() {
        clearDataModal.show();
    });

    document.getElementById('confirm-clear-data-btn').addEventListener('click', function() {
        fetch('/settings/clear', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('All data cleared successfully.', 'success');
                clearDataModal.hide();
                
                // Reload data
                loadApiKeys();
                loadDjProfiles();
                
                // Reset preferences
                document.getElementById('theme-dark-btn').classList.add('active');
                document.getElementById('theme-light-btn').classList.remove('active');
                document.getElementById('font-size-range').value = 16;
                document.getElementById('auto-play-audio').checked = true;
                document.getElementById('voice-recognition-enabled').checked = true;
                document.getElementById('response-length').value = 'medium';
                document.getElementById('save-interaction-history').checked = true;
            } else {
                showAlert(data.message || 'Error clearing data.', 'danger');
            }
        })
        .catch(error => {
            console.error('Error clearing data:', error);
            showAlert('Error clearing data. Please try again.', 'danger');
        });
    });

    // Theme Toggle
    document.getElementById('theme-dark-btn').addEventListener('click', function() {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        this.classList.add('active');
        document.getElementById('theme-light-btn').classList.remove('active');
        localStorage.setItem('ai_dj_theme', 'dark');
    });

    document.getElementById('theme-light-btn').addEventListener('click', function() {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        this.classList.add('active');
        document.getElementById('theme-dark-btn').classList.remove('active');
        localStorage.setItem('ai_dj_theme', 'light');
    });

    // Font Size
    document.getElementById('font-size-range').addEventListener('input', function() {
        document.documentElement.style.setProperty('--base-font-size', this.value + 'px');
        localStorage.setItem('ai_dj_font_size', this.value);
    });

    // Load saved preferences
    function loadPreferences() {
        // Theme
        const savedTheme = localStorage.getItem('ai_dj_theme') || 'dark';
        if (savedTheme === 'light') {
            document.getElementById('theme-light-btn').click();
        } else {
            document.getElementById('theme-dark-btn').click();
        }
        
        // Font Size
        const savedFontSize = localStorage.getItem('ai_dj_font_size') || '16';
        document.getElementById('font-size-range').value = savedFontSize;
        document.documentElement.style.setProperty('--base-font-size', savedFontSize + 'px');
        
        // Auto-play audio
        const autoPlayAudio = localStorage.getItem('ai_dj_auto_play_audio') !== 'false';
        document.getElementById('auto-play-audio').checked = autoPlayAudio;
        
        // Voice recognition
        const voiceRecognition = localStorage.getItem('ai_dj_voice_recognition') !== 'false';
        document.getElementById('voice-recognition-enabled').checked = voiceRecognition;
        
        // Response length
        const responseLength = localStorage.getItem('ai_dj_response_length') || 'medium';
        document.getElementById('response-length').value = responseLength;
        
        // Save interaction history
        const saveHistory = localStorage.getItem('ai_dj_save_history') !== 'false';
        document.getElementById('save-interaction-history').checked = saveHistory;
    }

    // Save preferences
    document.getElementById('auto-play-audio').addEventListener('change', function() {
        localStorage.setItem('ai_dj_auto_play_audio', this.checked);
    });
    
    document.getElementById('voice-recognition-enabled').addEventListener('change', function() {
        localStorage.setItem('ai_dj_voice_recognition', this.checked);
    });
    
    document.getElementById('response-length').addEventListener('change', function() {
        localStorage.setItem('ai_dj_response_length', this.value);
    });
    
    document.getElementById('save-interaction-history').addEventListener('change', function() {
        localStorage.setItem('ai_dj_save_history', this.checked);
    });

    // Show Alert
    function showAlert(message, type) {
        const alertContainer = document.getElementById('alert-container');
        const alertId = 'alert-' + Date.now();
        
        const alertHTML = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        alertContainer.innerHTML += alertHTML;
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) {
                const bsAlert = new bootstrap.Alert(alertElement);
                bsAlert.close();
            }
        }, 5000);
    }

    // Initialize
    loadApiKeys();
    loadDjProfiles();
    loadVoices();
    loadPersonalities();
    loadPreferences();

    // Add responsive behavior for mobile
    function adjustForMobile() {
        if (window.innerWidth < 768) {
            // Adjust tab labels to use icons only on small screens
            document.querySelectorAll('.nav-link').forEach(link => {
                const icon = link.querySelector('i');
                const text = link.textContent.trim();
                link.setAttribute('data-original-text', text);
                link.innerHTML = '';
                link.appendChild(icon);
            });
        } else {
            // Restore original tab labels on larger screens
            document.querySelectorAll('.nav-link').forEach(link => {
                const originalText = link.getAttribute('data-original-text');
                if (originalText) {
                    const icon = link.querySelector('i');
                    link.innerHTML = '';
                    link.appendChild(icon);
                    link.innerHTML += ' ' + originalText;
                }
            });
        }
    }

    // Run on load and resize
    adjustForMobile();
    window.addEventListener('resize', adjustForMobile);
});

/**
 * Generate a unique user ID if not already set
 */
function generateUserId() {
    const id = 'user_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('dj_user_id', id);
    return id;
}

/**
 * Load API keys from the server
 */
function loadApiKeys() {
    const keysContainer = document.getElementById('api-keys-list');
    
    // Show loading message
    keysContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin me-2"></i> Loading API keys...</div>';
    
    // Fetch API keys
    fetch(`/api/api_keys?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                keysContainer.innerHTML = '<div class="text-center text-danger">Error loading API keys</div>';
                return;
            }
            
            if (data.length === 0) {
                keysContainer.innerHTML = '<div class="text-center">No API keys found. Add your first API key above.</div>';
                return;
            }
            
            // Clear container
            keysContainer.innerHTML = '';
            
            // Add each API key
            data.forEach(key => {
                const keyItem = document.createElement('div');
                keyItem.className = 'api-key-item d-flex justify-content-between align-items-center';
                
                // Mask API key
                const maskedKey = maskApiKey(key.api_key);
                
                keyItem.innerHTML = `
                    <div>
                        <h5>${formatServiceName(key.service)}</h5>
                        <div class="d-flex align-items-center">
                            <span class="api-key-masked" data-key="${key.api_key}">${maskedKey}</span>
                            <i class="fas fa-eye ms-2 btn-reveal" data-service="${key.service}" title="Show API key"></i>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-danger delete-key-btn" data-service="${key.service}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                
                keysContainer.appendChild(keyItem);
            });
            
            // Add event listeners for reveal buttons
            document.querySelectorAll('.btn-reveal').forEach(btn => {
                btn.addEventListener('click', toggleApiKeyVisibility);
            });
            
            // Add event listeners for delete buttons
            document.querySelectorAll('.delete-key-btn').forEach(btn => {
                btn.addEventListener('click', deleteApiKey);
            });
        })
        .catch(error => {
            console.error('Error loading API keys:', error);
            keysContainer.innerHTML = '<div class="text-center text-danger">Error loading API keys</div>';
        });
}

/**
 * Format service name for display
 * @param {string} service - Service name
 * @returns {string} Formatted service name
 */
function formatServiceName(service) {
    switch (service) {
        case 'openai':
            return 'OpenAI';
        case 'elevenlabs':
            return 'ElevenLabs';
        case 'lastfm':
            return 'Last.fm';
        case 'spotify':
            return 'Spotify';
        case 'navidrome':
            return 'Navidrome';
        default:
            return service.charAt(0).toUpperCase() + service.slice(1);
    }
}

/**
 * Mask API key for display
 * @param {string} key - API key
 * @returns {string} Masked API key
 */
function maskApiKey(key) {
    if (key.length <= 8) {
        return '••••••••';
    }
    
    return key.substring(0, 4) + '••••••••' + key.substring(key.length - 4);
}

/**
 * Toggle API key visibility
 */
function toggleApiKeyVisibility() {
    const service = this.getAttribute('data-service');
    const keySpan = this.parentElement.querySelector('.api-key-masked');
    const fullKey = keySpan.getAttribute('data-key');
    
    if (keySpan.textContent === fullKey) {
        // Currently showing full key, mask it
        keySpan.textContent = maskApiKey(fullKey);
        this.classList.remove('fa-eye-slash');
        this.classList.add('fa-eye');
        this.title = 'Show API key';
    } else {
        // Currently masked, show full key
        keySpan.textContent = fullKey;
        this.classList.remove('fa-eye');
        this.classList.add('fa-eye-slash');
        this.title = 'Hide API key';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            keySpan.textContent = maskApiKey(fullKey);
            this.classList.remove('fa-eye-slash');
            this.classList.add('fa-eye');
            this.title = 'Show API key';
        }, 10000);
    }
}

/**
 * Save API key
 * @param {Event} e - Form submit event
 */
function saveApiKey(e) {
    e.preventDefault();
    
    const service = document.getElementById('service-select').value;
    const apiKey = document.getElementById('api-key-input').value;
    
    if (!service || !apiKey) {
        showAlert('error', 'Please select a service and enter an API key');
        return;
    }
    
    // Send to server
    fetch('/api/api_keys', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            service: service,
            api_key: apiKey
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
            return;
        }
        
        showAlert('success', data.message);
        
        // Reset form
        document.getElementById('api-key-form').reset();
        
        // Reload API keys
        loadApiKeys();
    })
    .catch(error => {
        console.error('Error saving API key:', error);
        showAlert('error', 'Failed to save API key');
    });
}

/**
 * Delete API key
 */
function deleteApiKey() {
    const service = this.getAttribute('data-service');
    
    if (!confirm(`Are you sure you want to delete your ${formatServiceName(service)} API key?`)) {
        return;
    }
    
    // Send to server
    fetch(`/api/api_keys/${service}?user_id=${userId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
            return;
        }
        
        showAlert('success', data.message);
        
        // Reload API keys
        loadApiKeys();
    })
    .catch(error => {
        console.error('Error deleting API key:', error);
        showAlert('error', 'Failed to delete API key');
    });
}

/**
 * Load DJ profiles from the server
 */
function loadDjProfiles() {
    const profilesContainer = document.getElementById('dj-profiles-list');
    
    // Show loading message
    profilesContainer.innerHTML = '<div class="col-12 text-center"><i class="fas fa-spinner fa-spin me-2"></i> Loading DJ profiles...</div>';
    
    // Fetch DJ profiles
    fetch(`/api/dj_profiles?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                profilesContainer.innerHTML = '<div class="col-12 text-center text-danger">Error loading DJ profiles</div>';
                return;
            }
            
            if (data.length === 0) {
                profilesContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <p>No DJ profiles found. Create your first DJ profile in the "Create DJ Profile" tab.</p>
                        <button class="btn btn-primary" onclick="document.getElementById('create-profile-tab').click()">
                            <i class="fas fa-plus-circle me-2"></i> Create DJ Profile
                        </button>
                    </div>
                `;
                return;
            }
            
            // Clear container
            profilesContainer.innerHTML = '';
            
            // Add each DJ profile
            data.forEach(profile => {
                const profileCard = document.createElement('div');
                profileCard.className = 'col-md-6 col-lg-4 mb-4';
                
                // Get voice name
                const voice = availableVoices.find(v => v.voice_id === profile.voice_id);
                const voiceName = voice ? voice.name : 'Unknown Voice';
                
                profileCard.innerHTML = `
                    <div class="profile-card ${profile.is_active ? 'active' : ''}">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h4>${profile.name}</h4>
                            <div>
                                ${!profile.is_active ? `
                                <button class="btn btn-sm btn-outline-success activate-profile-btn me-2" data-profile-id="${profile.id}">
                                    <i class="fas fa-check-circle"></i>
                                </button>
                                ` : `
                                <span class="badge bg-success me-2">Active</span>
                                `}
                                <button class="btn btn-sm btn-outline-danger delete-profile-btn" data-profile-id="${profile.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div class="mb-2">
                            <strong>Voice:</strong> ${voiceName}
                        </div>
                        <div>
                            <strong>Personality:</strong>
                            <p class="mb-0 text-muted small">${truncateText(profile.personality, 100)}</p>
                        </div>
                    </div>
                `;
                
                profilesContainer.appendChild(profileCard);
            });
            
            // Add event listeners for activate buttons
            document.querySelectorAll('.activate-profile-btn').forEach(btn => {
                btn.addEventListener('click', activateDjProfile);
            });
            
            // Add event listeners for delete buttons
            document.querySelectorAll('.delete-profile-btn').forEach(btn => {
                btn.addEventListener('click', deleteDjProfile);
            });
        })
        .catch(error => {
            console.error('Error loading DJ profiles:', error);
            profilesContainer.innerHTML = '<div class="col-12 text-center text-danger">Error loading DJ profiles</div>';
        });
}

/**
 * Load available voices
 */
function loadVoices() {
    const voicesContainer = document.getElementById('voices-container');
    
    // Show loading message
    voicesContainer.innerHTML = '<div class="col-12 text-center"><i class="fas fa-spinner fa-spin me-2"></i> Loading voices...</div>';
    
    // Fetch voices
    fetch('/api/voices')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                voicesContainer.innerHTML = '<div class="col-12 text-center text-danger">Error loading voices</div>';
                return;
            }
            
            // Store voices globally
            availableVoices = data;
            
            // Clear container
            voicesContainer.innerHTML = '';
            
            // Add each voice
            data.forEach(voice => {
                const voiceCard = document.createElement('div');
                voiceCard.className = 'col-md-4 mb-3';
                
                voiceCard.innerHTML = `
                    <div class="card voice-card" data-voice-id="${voice.voice_id}">
                        <div class="card-body text-center">
                            <h5 class="card-title">${voice.name}</h5>
                            <audio controls src="${voice.preview_url}" class="w-100 mt-2"></audio>
                        </div>
                    </div>
                `;
                
                voicesContainer.appendChild(voiceCard);
            });
            
            // Add event listeners for voice selection
            document.querySelectorAll('.voice-card').forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all cards
                    document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
                    
                    // Add selected class to this card
                    this.classList.add('selected');
                    
                    // Update selected voice ID
                    selectedVoiceId = this.getAttribute('data-voice-id');
                });
            });
        })
        .catch(error => {
            console.error('Error loading voices:', error);
            voicesContainer.innerHTML = '<div class="col-12 text-center text-danger">Error loading voices</div>';
        });
}

/**
 * Load available personalities
 */
function loadPersonalities() {
    const personalitiesContainer = document.getElementById('personalities-container');
    
    // Show loading message
    personalitiesContainer.innerHTML = '<div class="col-12 text-center"><i class="fas fa-spinner fa-spin me-2"></i> Loading personalities...</div>';
    
    // Fetch personalities
    fetch('/api/personalities')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                personalitiesContainer.innerHTML = '<div class="col-12 text-center text-danger">Error loading personalities</div>';
                return;
            }
            
            // Store personalities globally
            availablePersonalities = data;
            
            // Clear container
            personalitiesContainer.innerHTML = '';
            
            // Add each personality
            data.forEach(personality => {
                const personalityCard = document.createElement('div');
                personalityCard.className = 'col-md-4 mb-3';
                
                personalityCard.innerHTML = `
                    <div class="card personality-card" data-personality-id="${personality.id}">
                        <div class="card-body">
                            <h5 class="card-title">${personality.name}</h5>
                            <p class="card-text">${personality.description}</p>
                        </div>
                    </div>
                `;
                
                personalitiesContainer.appendChild(personalityCard);
            });
            
            // Add event listeners for personality selection
            document.querySelectorAll('.personality-card').forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all cards
                    document.querySelectorAll('.personality-card').forEach(c => c.classList.remove('selected'));
                    
                    // Add selected class to this card
                    this.classList.add('selected');
                    
                    // Update selected personality ID
                    selectedPersonalityId = this.getAttribute('data-personality-id');
                    
                    // Uncheck custom personality checkbox
                    document.getElementById('custom-personality-check').checked = false;
                    document.getElementById('custom-personality-container').style.display = 'none';
                });
            });
        })
        .catch(error => {
            console.error('Error loading personalities:', error);
            personalitiesContainer.innerHTML = '<div class="col-12 text-center text-danger">Error loading personalities</div>';
        });
}

/**
 * Toggle custom personality input
 */
function toggleCustomPersonality() {
    const customContainer = document.getElementById('custom-personality-container');
    
    if (this.checked) {
        customContainer.style.display = 'block';
        
        // Deselect any selected personality
        document.querySelectorAll('.personality-card').forEach(card => card.classList.remove('selected'));
        selectedPersonalityId = null;
    } else {
        customContainer.style.display = 'none';
    }
}

/**
 * Create a new DJ profile
 * @param {Event} e - Form submit event
 */
function createDjProfile(e) {
    e.preventDefault();
    
    const name = document.getElementById('profile-name').value;
    const customPersonalityCheck = document.getElementById('custom-personality-check').checked;
    let personality;
    
    if (!name) {
        showAlert('error', 'Please enter a profile name');
        return;
    }
    
    if (!selectedVoiceId) {
        showAlert('error', 'Please select a voice');
        return;
    }
    
    if (customPersonalityCheck) {
        personality = document.getElementById('custom-personality-input').value;
        
        if (!personality) {
            showAlert('error', 'Please enter a custom personality description');
            return;
        }
    } else {
        if (!selectedPersonalityId) {
            showAlert('error', 'Please select a personality');
            return;
        }
        
        // Get personality template
        const personalityTemplate = availablePersonalities.find(p => p.id === selectedPersonalityId);
        personality = personalityTemplate.prompt_template;
    }
    
    // Send to server
    fetch('/api/dj_profiles', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            name: name,
            voice_id: selectedVoiceId,
            personality: personality
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
            return;
        }
        
        showAlert('success', data.message);
        
        // Reset form
        document.getElementById('create-profile-form').reset();
        document.querySelectorAll('.voice-card').forEach(card => card.classList.remove('selected'));
        document.querySelectorAll('.personality-card').forEach(card => card.classList.remove('selected'));
        selectedVoiceId = null;
        selectedPersonalityId = null;
        document.getElementById('custom-personality-container').style.display = 'none';
        
        // Reload DJ profiles
        loadDjProfiles();
        
        // Switch to DJ profiles tab
        document.getElementById('dj-profiles-tab').click();
    })
    .catch(error => {
        console.error('Error creating DJ profile:', error);
        showAlert('error', 'Failed to create DJ profile');
    });
}

/**
 * Activate a DJ profile
 */
function activateDjProfile() {
    const profileId = this.getAttribute('data-profile-id');
    
    // Send to server
    fetch(`/api/dj_profiles/${profileId}/activate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
            return;
        }
        
        showAlert('success', data.message);
        
        // Reload DJ profiles
        loadDjProfiles();
    })
    .catch(error => {
        console.error('Error activating DJ profile:', error);
        showAlert('error', 'Failed to activate DJ profile');
    });
}

/**
 * Delete a DJ profile
 */
function deleteDjProfile() {
    const profileId = this.getAttribute('data-profile-id');
    
    if (!confirm('Are you sure you want to delete this DJ profile?')) {
        return;
    }
    
    // Send to server
    fetch(`/api/dj_profiles/${profileId}?user_id=${userId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
            return;
        }
        
        showAlert('success', data.message);
        
        // Reload DJ profiles
        loadDjProfiles();
    })
    .catch(error => {
        console.error('Error deleting DJ profile:', error);
        showAlert('error', 'Failed to delete DJ profile');
    });
}

/**
 * Export settings
 */
function exportSettings() {
    // Fetch settings
    fetch(`/api/export?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('error', data.error);
                return;
            }
            
            // Create a download link
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai_dj_settings_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showAlert('success', 'Settings exported successfully');
        })
        .catch(error => {
            console.error('Error exporting settings:', error);
            showAlert('error', 'Failed to export settings');
        });
}

/**
 * Show import modal
 */
function showImportModal() {
    // Reset file input
    document.getElementById('import-file').value = '';
    
    // Show modal
    const importModal = new bootstrap.Modal(document.getElementById('importModal'));
    importModal.show();
}

/**
 * Import settings
 */
function importSettings() {
    const fileInput = document.getElementById('import-file');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showAlert('error', 'Please select a file to import');
        return;
    }
    
    const file = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            const settings = JSON.parse(e.target.result);
            
            // Send to server
            fetch('/api/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    settings: settings
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert('error', data.error);
                    return;
                }
                
                showAlert('success', data.message);
                
                // Hide modal
                bootstrap.Modal.getInstance(document.getElementById('importModal')).hide();
                
                // Reload data
                loadApiKeys();
                loadDjProfiles();
            })
            .catch(error => {
                console.error('Error importing settings:', error);
                showAlert('error', 'Failed to import settings');
            });
        } catch (error) {
            console.error('Error parsing settings file:', error);
            showAlert('error', 'Invalid settings file');
        }
    };
    
    reader.readAsText(file);
}

/**
 * Show alert message
 * @param {string} type - Alert type ('success', 'error')
 * @param {string} message - Alert message
 */
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}

/**
 * Truncate text if too long
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}
