/**
 * API functions for the AI DJ Assistant
 */

/**
 * Load playlists from the server
 */
function loadPlaylists() {
    fetch('/api/playlists')
        .then(response => response.json())
        .then(data => {
            if (data.playlists) {
                updatePlaylistsUI(data.playlists);
            } else {
                console.error('No playlists found');
                showToast('No playlists found', 'warning');
            }
        })
        .catch(error => {
            console.error('Error loading playlists:', error);
            showToast('Error loading playlists', 'error');
        });
}

/**
 * Update the UI with playlists
 * @param {Array} playlists - List of playlists
 */
function updatePlaylistsUI(playlists) {
    // Update sidebar recent playlists
    const recentPlaylistsEl = document.getElementById('recent-playlists');
    recentPlaylistsEl.innerHTML = '';
    
    const recentPlaylists = playlists.slice(0, 5);
    
    if (recentPlaylists.length === 0) {
        recentPlaylistsEl.innerHTML = `
            <li class="nav-item">
                <a class="nav-link text-truncate" href="#">
                    <i class="bi bi-music-note me-2"></i>
                    No playlists found
                </a>
            </li>
        `;
    } else {
        recentPlaylists.forEach(playlist => {
            recentPlaylistsEl.innerHTML += `
                <li class="nav-item">
                    <a class="nav-link text-truncate" href="#" onclick="loadPlaylistDetails('${playlist.id}')">
                        <i class="bi bi-music-note me-2"></i>
                        ${playlist.name}
                    </a>
                </li>
            `;
        });
    }
    
    // Update playlists table if visible
    const playlistsTable = document.getElementById('playlists-table');
    if (playlistsTable) {
        playlistsTable.innerHTML = '';
        
        if (playlists.length === 0) {
            playlistsTable.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">No playlists found</td>
                </tr>
            `;
        } else {
            playlists.forEach(playlist => {
                const duration = formatDuration(playlist.duration || 0);
                const created = formatDate(playlist.created || '');
                
                playlistsTable.innerHTML += `
                    <tr>
                        <td>${playlist.name}</td>
                        <td>${playlist.songCount || 0}</td>
                        <td>${duration}</td>
                        <td>${created}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="loadPlaylistDetails('${playlist.id}')">
                                <i class="bi bi-info-circle"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="playPlaylist('${playlist.id}')">
                                <i class="bi bi-play"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deletePlaylist('${playlist.id}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
        }
    }
}

/**
 * Load details for a specific playlist
 * @param {string} playlistId - ID of the playlist
 */
function loadPlaylistDetails(playlistId) {
    fetch(`/api/playlists/${playlistId}`)
        .then(response => response.json())
        .then(data => {
            if (data.playlist) {
                displayPlaylistDetails(data.playlist);
                
                // Switch to playlists tab if not already there
                if (!document.getElementById('playlists-content').classList.contains('d-none')) {
                    showSection('playlists');
                }
            } else {
                console.error('Playlist not found');
                showToast('Playlist not found', 'warning');
            }
        })
        .catch(error => {
            console.error('Error loading playlist details:', error);
            showToast('Error loading playlist details', 'error');
        });
}

/**
 * Display playlist details in the UI
 * @param {Object} playlist - Playlist object
 */
function displayPlaylistDetails(playlist) {
    const playlistDetailsEl = document.getElementById('playlist-details');
    
    let songsHtml = '';
    if (playlist.songs && playlist.songs.length > 0) {
        songsHtml = '<div class="table-responsive"><table class="table table-dark table-hover"><thead><tr><th>#</th><th>Title</th><th>Artist</th><th>Album</th><th>Duration</th></tr></thead><tbody>';
        
        playlist.songs.forEach((song, index) => {
            const duration = formatDuration(song.duration || 0);
            
            songsHtml += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${song.title}</td>
                    <td>${song.artist}</td>
                    <td>${song.album || '-'}</td>
                    <td>${duration}</td>
                </tr>
            `;
        });
        
        songsHtml += '</tbody></table></div>';
    } else {
        songsHtml = '<p class="text-center">No songs in this playlist</p>';
    }
    
    playlistDetailsEl.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4>${playlist.name}</h4>
            <button class="btn btn-success" onclick="playPlaylist('${playlist.id}')">
                <i class="bi bi-play-fill"></i> Play
            </button>
        </div>
        <div class="mb-3">
            <span class="badge bg-info">${playlist.songCount || 0} songs</span>
            <span class="badge bg-secondary">${formatDuration(playlist.duration || 0)}</span>
            <span class="badge bg-primary">Created: ${formatDate(playlist.created || '')}</span>
        </div>
        ${songsHtml}
    `;
}

/**
 * Create a new AI-generated playlist
 * @param {Event} e - Form submit event
 */
function createPlaylist(e) {
    e.preventDefault();
    
    const mood = document.getElementById('mood').value;
    const theme = document.getElementById('theme').value;
    const count = document.getElementById('count').value;
    
    if (!mood) {
        showToast('Please enter a mood', 'warning');
        return;
    }
    
    // Show loading state
    const submitButton = e.target.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
    submitButton.disabled = true;
    
    fetch('/api/create_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            mood: mood,
            theme: theme,
            count: parseInt(count)
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset form
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
        
        if (data.success) {
            showToast(`Playlist "${data.playlist_name}" created successfully`, 'success');
            
            // Reset form
            document.getElementById('mood').value = '';
            document.getElementById('theme').value = '';
            document.getElementById('count').value = '10';
            
            // Reload playlists
            loadPlaylists();
            
            // Load the new playlist details
            loadPlaylistDetails(data.playlist_id);
        } else {
            showToast(`Error creating playlist: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error creating playlist:', error);
        showToast('Error creating playlist', 'error');
        
        // Reset button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    });
}

/**
 * Delete a playlist
 * @param {string} playlistId - ID of the playlist to delete
 */
function deletePlaylist(playlistId) {
    if (confirm('Are you sure you want to delete this playlist?')) {
        fetch(`/api/playlists/${playlistId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Playlist deleted successfully', 'success');
                
                // Reload playlists
                loadPlaylists();
                
                // Clear playlist details
                document.getElementById('playlist-details').innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-music-note-list display-1 text-muted"></i>
                        <p class="mt-3">Select a playlist to view details</p>
                    </div>
                `;
            } else {
                showToast(`Error deleting playlist: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting playlist:', error);
            showToast('Error deleting playlist', 'error');
        });
    }
}

/**
 * Load recent activity
 */
function loadRecentActivity() {
    fetch('/api/recent_activity')
        .then(response => response.json())
        .then(data => {
            if (data.activities) {
                updateRecentActivityUI(data.activities);
            } else {
                console.error('No recent activity found');
                document.getElementById('recent-activity').innerHTML = `
                    <li class="list-group-item bg-dark text-light border-secondary">No recent activity</li>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading recent activity:', error);
            document.getElementById('recent-activity').innerHTML = `
                <li class="list-group-item bg-dark text-light border-secondary">Error loading activity</li>
            `;
        });
}

/**
 * Update the UI with recent activity
 * @param {Array} activities - List of activities
 */
function updateRecentActivityUI(activities) {
    const recentActivityEl = document.getElementById('recent-activity');
    recentActivityEl.innerHTML = '';
    
    if (activities.length === 0) {
        recentActivityEl.innerHTML = `
            <li class="list-group-item bg-dark text-light border-secondary">No recent activity</li>
        `;
    } else {
        activities.forEach(activity => {
            const time = formatTime(activity.timestamp);
            let icon = 'bi-music-note';
            
            if (activity.type === 'playlist_created') {
                icon = 'bi-file-plus';
            } else if (activity.type === 'song_played') {
                icon = 'bi-play-circle';
            } else if (activity.type === 'dj_announcement') {
                icon = 'bi-mic';
            }
            
            recentActivityEl.innerHTML += `
                <li class="list-group-item bg-dark text-light border-secondary">
                    <div class="d-flex justify-content-between">
                        <div>
                            <i class="bi ${icon} me-2"></i>
                            ${activity.description}
                        </div>
                        <small class="text-muted">${time}</small>
                    </div>
                </li>
            `;
        });
    }
}

/**
 * Load music trends
 */
function loadTrends() {
    fetch('/api/trends')
        .then(response => response.json())
        .then(data => {
            if (data.trends) {
                updateTrendsUI(data.trends);
            } else {
                console.error('No trends found');
                document.getElementById('trending-tracks').innerHTML = `
                    <li class="list-group-item bg-dark text-light border-secondary">No trends available</li>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading trends:', error);
            document.getElementById('trending-tracks').innerHTML = `
                <li class="list-group-item bg-dark text-light border-secondary">Error loading trends</li>
            `;
        });
}

/**
 * Update the UI with music trends
 * @param {Object} trends - Trends data
 */
function updateTrendsUI(trends) {
    // Update dashboard trends
    const trendingTracksEl = document.getElementById('trending-tracks');
    trendingTracksEl.innerHTML = '';
    
    // Combine and sort all trends
    const allTrends = [];
    
    if (trends.spotify) {
        trends.spotify.forEach(track => {
            allTrends.push({
                ...track,
                source: 'spotify'
            });
        });
    }
    
    if (trends.lastfm) {
        trends.lastfm.forEach(track => {
            allTrends.push({
                ...track,
                source: 'lastfm'
            });
        });
    }
    
    if (trends.reddit) {
        trends.reddit.forEach(track => {
            allTrends.push({
                ...track,
                source: 'reddit'
            });
        });
    }
    
    // Sort by popularity (if available) or random
    allTrends.sort((a, b) => {
        if (a.popularity && b.popularity) {
            return b.popularity - a.popularity;
        }
        return Math.random() - 0.5;
    });
    
    // Take top 5 for dashboard
    const topTrends = allTrends.slice(0, 5);
    
    if (topTrends.length === 0) {
        trendingTracksEl.innerHTML = `
            <li class="list-group-item bg-dark text-light border-secondary">No trends available</li>
        `;
    } else {
        topTrends.forEach(track => {
            let sourceIcon = '';
            if (track.source === 'spotify') {
                sourceIcon = '<i class="bi bi-spotify text-success"></i>';
            } else if (track.source === 'lastfm') {
                sourceIcon = '<i class="bi bi-broadcast text-danger"></i>';
            } else if (track.source === 'reddit') {
                sourceIcon = '<i class="bi bi-reddit text-warning"></i>';
            }
            
            trendingTracksEl.innerHTML += `
                <li class="list-group-item bg-dark text-light border-secondary">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${track.artist}</strong> - ${track.title}
                        </div>
                        <div>
                            ${sourceIcon}
                        </div>
                    </div>
                </li>
            `;
        });
    }
    
    // Update trends page if visible
    if (trends.spotify) {
        updateSourceTrends('spotify', trends.spotify);
    }
    
    if (trends.lastfm) {
        updateSourceTrends('lastfm', trends.lastfm);
    }
    
    if (trends.reddit) {
        updateSourceTrends('reddit', trends.reddit);
    }
}

/**
 * Update trends for a specific source
 * @param {string} source - Source name (spotify, lastfm, reddit)
 * @param {Array} tracks - List of tracks
 */
function updateSourceTrends(source, tracks) {
    const trendsEl = document.getElementById(`${source}-trends`);
    if (!trendsEl) return;
    
    trendsEl.innerHTML = '';
    
    if (tracks.length === 0) {
        trendsEl.innerHTML = `
            <li class="list-group-item bg-dark text-light border-secondary">No ${source} trends available</li>
        `;
    } else {
        tracks.forEach(track => {
            let extraInfo = '';
            
            if (track.listeners) {
                extraInfo = `<span class="badge bg-secondary">${track.listeners} listeners</span>`;
            } else if (track.popularity) {
                extraInfo = `<span class="badge bg-secondary">Popularity: ${track.popularity}</span>`;
            } else if (track.score) {
                extraInfo = `<span class="badge bg-secondary">Score: ${track.score}</span>`;
            }
            
            trendsEl.innerHTML += `
                <li class="list-group-item bg-dark text-light border-secondary">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${track.artist}</strong> - ${track.title}
                        </div>
                        <div>
                            ${extraInfo}
                        </div>
                    </div>
                </li>
            `;
        });
    }
}

/**
 * Analyze music trends
 */
function analyzeTrends() {
    const analyzeBtn = document.getElementById('analyze-trends-btn');
    const originalText = analyzeBtn.innerHTML;
    analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
    analyzeBtn.disabled = true;
    
    fetch('/api/analyze_trends')
        .then(response => response.json())
        .then(data => {
            analyzeBtn.innerHTML = originalText;
            analyzeBtn.disabled = false;
            
            if (data.analysis) {
                document.getElementById('analysis-result').classList.remove('d-none');
                document.getElementById('analysis-content').innerHTML = data.analysis.analysis.replace(/\n/g, '<br>');
            } else {
                showToast('Error analyzing trends', 'error');
            }
        })
        .catch(error => {
            console.error('Error analyzing trends:', error);
            showToast('Error analyzing trends', 'error');
            
            analyzeBtn.innerHTML = originalText;
            analyzeBtn.disabled = false;
        });
}

/**
 * Check what's currently playing
 */
function checkNowPlaying() {
    fetch('/api/now_playing')
        .then(response => response.json())
        .then(data => {
            if (data.playing) {
                updateNowPlayingUI(data.playing);
            } else {
                // No song playing
                document.getElementById('no-playing').classList.remove('d-none');
                document.getElementById('playing-info').classList.add('d-none');
            }
        })
        .catch(error => {
            console.error('Error checking now playing:', error);
        });
}

/**
 * Update the UI with now playing information
 * @param {Object} song - Currently playing song
 */
function updateNowPlayingUI(song) {
    document.getElementById('no-playing').classList.add('d-none');
    document.getElementById('playing-info').classList.remove('d-none');
    
    document.getElementById('song-title').textContent = song.title;
    document.getElementById('song-artist').textContent = song.artist;
    document.getElementById('song-album').textContent = song.album || '';
    
    if (song.albumArt) {
        document.getElementById('album-art').src = song.albumArt;
    } else {
        document.getElementById('album-art').src = '/static/img/default-album.png';
    }
    
    // Update player state
    if (song.isPlaying) {
        document.getElementById('play-pause-btn').innerHTML = '<i class="bi bi-pause"></i>';
        isPlaying = true;
    } else {
        document.getElementById('play-pause-btn').innerHTML = '<i class="bi bi-play"></i>';
        isPlaying = false;
    }
    
    // Update progress
    if (song.duration) {
        document.getElementById('total-time').textContent = formatDuration(song.duration);
    }
    
    if (song.position) {
        document.getElementById('current-time').textContent = formatDuration(song.position);
        const progress = (song.position / song.duration) * 100;
        document.getElementById('song-progress').style.width = `${progress}%`;
    }
    
    // Store current song
    currentSong = song;
}

// Helper functions for formatting

/**
 * Format duration in seconds to MM:SS
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
function formatDuration(seconds) {
    if (!seconds) return '0:00';
    
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format date to readable format
 * @param {string} dateString - Date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

/**
 * Format time to readable format
 * @param {string} timeString - Time string
 * @returns {string} Formatted time
 */
function formatTime(timeString) {
    if (!timeString) return '';
    
    const date = new Date(timeString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
