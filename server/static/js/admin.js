/**
 * AI DJ Admin Interface
 * Provides tools for managing user moderation and system settings
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin interface
    initAdminInterface();
});

/**
 * Initialize admin interface components
 */
function initAdminInterface() {
    // Load current moderation settings
    loadModerationSettings();
    
    // Load user status list
    loadUserStatusList();
    
    // Load recent interactions
    loadRecentInteractions();
    
    // Add event listeners
    document.getElementById('save-settings-btn').addEventListener('click', saveModerationSettings);
    document.getElementById('refresh-users-btn').addEventListener('click', loadUserStatusList);
    document.getElementById('refresh-interactions-btn').addEventListener('click', loadRecentInteractions);
    
    // Set up interval to refresh user list every 30 seconds
    setInterval(loadUserStatusList, 30000);
    
    // Set up interval to refresh interactions every 60 seconds
    setInterval(loadRecentInteractions, 60000);
}

/**
 * Load current moderation settings
 */
function loadModerationSettings() {
    fetch('/api/moderation_settings')
        .then(response => response.json())
        .then(data => {
            // Update form fields
            document.getElementById('mute-duration').value = data.mute_duration;
            document.getElementById('warning-threshold').value = data.warning_threshold;
            document.getElementById('mute-threshold').value = data.mute_threshold;
            document.getElementById('suspension-duration').value = data.suspension_duration;
        })
        .catch(error => {
            console.error('Error loading moderation settings:', error);
            showAlert('error', 'Failed to load moderation settings');
        });
}

/**
 * Save moderation settings
 */
function saveModerationSettings() {
    // Get values from form
    const muteDuration = parseInt(document.getElementById('mute-duration').value);
    const warningThreshold = parseInt(document.getElementById('warning-threshold').value);
    const muteThreshold = parseInt(document.getElementById('mute-threshold').value);
    const suspensionDuration = parseInt(document.getElementById('suspension-duration').value);
    
    // Validate inputs
    if (isNaN(muteDuration) || isNaN(warningThreshold) || isNaN(muteThreshold) || isNaN(suspensionDuration)) {
        showAlert('error', 'All values must be numbers');
        return;
    }
    
    // Send to server
    fetch('/api/moderation_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            mute_duration: muteDuration,
            warning_threshold: warningThreshold,
            mute_threshold: muteThreshold,
            suspension_duration: suspensionDuration
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Settings saved successfully');
        } else {
            showAlert('error', 'Failed to save settings');
        }
    })
    .catch(error => {
        console.error('Error saving moderation settings:', error);
        showAlert('error', 'Failed to save settings');
    });
}

/**
 * Load user status list
 */
function loadUserStatusList() {
    // Get user list container
    const userListContainer = document.getElementById('user-list');
    
    // Show loading message
    userListContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading user data...</div>';
    
    // Get recent interactions to find active users
    fetch('/api/recent_interactions')
        .then(response => response.json())
        .then(data => {
            // Extract unique user IDs
            const userIds = [...new Set(data.map(item => item.user_id))];
            
            // If no users found
            if (userIds.length === 0) {
                userListContainer.innerHTML = '<div class="text-center">No active users found</div>';
                return;
            }
            
            // Get status for each user
            Promise.all(userIds.map(userId => 
                fetch(`/api/user_status/${userId}`)
                    .then(response => response.json())
                    .then(status => ({ userId, ...status }))
            ))
            .then(userStatuses => {
                // Clear container
                userListContainer.innerHTML = '';
                
                // Create table
                const table = document.createElement('table');
                table.className = 'table table-dark table-striped';
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Status</th>
                            <th>Warnings</th>
                            <th>Mutes</th>
                            <th>Time Remaining</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="user-table-body"></tbody>
                `;
                
                userListContainer.appendChild(table);
                const tableBody = document.getElementById('user-table-body');
                
                // Add rows for each user
                userStatuses.forEach(user => {
                    const row = document.createElement('tr');
                    
                    // Calculate time remaining if muted or suspended
                    let timeRemaining = '';
                    const currentTime = Math.floor(Date.now() / 1000);
                    
                    if (user.status === 'muted' && user.muted_until && user.muted_until > currentTime) {
                        const seconds = Math.floor(user.muted_until - currentTime);
                        timeRemaining = `${seconds}s`;
                    } else if (user.status === 'suspended' && user.suspended_until && user.suspended_until > currentTime) {
                        const totalSeconds = Math.floor(user.suspended_until - currentTime);
                        const minutes = Math.floor(totalSeconds / 60);
                        const seconds = totalSeconds % 60;
                        timeRemaining = `${minutes}m ${seconds}s`;
                    }
                    
                    // Status badge class
                    let statusBadgeClass = 'bg-success';
                    if (user.status === 'muted') {
                        statusBadgeClass = 'bg-warning';
                    } else if (user.status === 'suspended') {
                        statusBadgeClass = 'bg-danger';
                    }
                    
                    row.innerHTML = `
                        <td>${user.userId}</td>
                        <td><span class="badge ${statusBadgeClass}">${user.status}</span></td>
                        <td>${user.warnings || 0}</td>
                        <td>${user.mutes || 0}</td>
                        <td>${timeRemaining}</td>
                        <td>
                            <button class="btn btn-sm btn-primary reset-user-btn" data-user-id="${user.userId}">
                                Reset
                            </button>
                        </td>
                    `;
                    
                    tableBody.appendChild(row);
                });
                
                // Add event listeners to reset buttons
                document.querySelectorAll('.reset-user-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        const userId = this.getAttribute('data-user-id');
                        resetUser(userId);
                    });
                });
            });
        })
        .catch(error => {
            console.error('Error loading user data:', error);
            userListContainer.innerHTML = '<div class="text-center text-danger">Error loading user data</div>';
        });
}

/**
 * Reset a user's status
 * @param {string} userId - User ID to reset
 */
function resetUser(userId) {
    fetch(`/api/reset_user/${userId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `User ${userId} has been reset`);
            loadUserStatusList(); // Refresh the list
        } else {
            showAlert('error', 'Failed to reset user');
        }
    })
    .catch(error => {
        console.error('Error resetting user:', error);
        showAlert('error', 'Failed to reset user');
    });
}

/**
 * Load recent interactions
 */
function loadRecentInteractions() {
    // Get interactions container
    const interactionsContainer = document.getElementById('interactions-list');
    
    // Show loading message
    interactionsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading interactions...</div>';
    
    // Fetch recent interactions
    fetch('/api/recent_interactions')
        .then(response => response.json())
        .then(data => {
            // If no interactions found
            if (data.length === 0) {
                interactionsContainer.innerHTML = '<div class="text-center">No recent interactions found</div>';
                return;
            }
            
            // Create table
            const table = document.createElement('table');
            table.className = 'table table-dark table-striped';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>User ID</th>
                        <th>Request</th>
                        <th>Response</th>
                    </tr>
                </thead>
                <tbody id="interactions-table-body"></tbody>
            `;
            
            interactionsContainer.appendChild(table);
            const tableBody = document.getElementById('interactions-table-body');
            
            // Add rows for each interaction (most recent first)
            data.reverse().forEach(interaction => {
                const row = document.createElement('tr');
                
                // Format timestamp
                const timestamp = new Date(interaction.timestamp);
                const formattedTime = timestamp.toLocaleString();
                
                // Truncate long text
                const truncateText = (text, maxLength = 100) => {
                    if (text.length <= maxLength) return text;
                    return text.substring(0, maxLength) + '...';
                };
                
                row.innerHTML = `
                    <td>${formattedTime}</td>
                    <td>${interaction.user_id || 'Unknown'}</td>
                    <td title="${interaction.request}">${truncateText(interaction.request)}</td>
                    <td title="${interaction.response}">${truncateText(interaction.response)}</td>
                `;
                
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading interactions:', error);
            interactionsContainer.innerHTML = '<div class="text-center text-danger">Error loading interactions</div>';
        });
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
