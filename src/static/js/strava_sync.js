// Strava Sync Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Strava sync button
    const stravaSyncBtn = document.querySelector('.strava-sync-btn');
    if (stravaSyncBtn) {
        stravaSyncBtn.addEventListener('click', syncStravaData);
    }
    
    // Initialize Strava connect button
    const stravaConnectBtn = document.getElementById('strava-connect-btn');
    if (stravaConnectBtn) {
        stravaConnectBtn.addEventListener('click', connectStrava);
    }
    
    // Check Strava connection status on page load
    checkStravaStatus();
    
    // Check URL for Strava callback status
    checkCallbackStatus();
});

function checkCallbackStatus() {
    // Check if we're returning from a Strava OAuth flow
    const urlParams = new URLSearchParams(window.location.hash.substring(1));
    const status = urlParams.get('status');
    const source = urlParams.get('source');
    const message = urlParams.get('message');
    
    if (status && source === 'strava') {
        if (status === 'success') {
            showNotification('Success! Your Strava account has been connected.', 'success');
            // Refresh Strava status
            checkStravaStatus();
        } else if (status === 'error') {
            showNotification(`Error connecting to Strava: ${message || 'Unknown error'}`, 'error');
        }
    }
}

function connectStrava() {
    // Show loading state
    const connectBtn = document.getElementById('strava-connect-btn');
    const originalText = connectBtn.textContent;
    connectBtn.textContent = 'Connecting...';
    connectBtn.disabled = true;
    
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    fetch(`/api/strava/auth?user_id=${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                throw new Error('Failed to get Strava auth URL');
            }
        })
        .catch(error => {
            console.error('Error connecting to Strava:', error);
            showNotification(`Error connecting to Strava: ${error.message}`, 'error');
            
            // Reset button
            connectBtn.textContent = originalText;
            connectBtn.disabled = false;
        });
}

function syncStravaData() {
    // Show loading state
    const syncBtn = document.querySelector('.strava-sync-btn');
    const originalText = syncBtn.textContent;
    syncBtn.textContent = 'Syncing...';
    syncBtn.disabled = true;
    
    // Update sync status
    const syncStatus = document.getElementById('strava-sync-status');
    if (syncStatus) {
        syncStatus.textContent = 'Syncing...';
        syncStatus.className = 'sync-status syncing';
    }
    
    // Get user ID from button data attribute
    const userId = syncBtn.getAttribute('data-user-id');
    
    fetch('/api/strava/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP error! Status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Update sync status
        if (syncStatus) {
            const lastSyncDate = new Date().toLocaleString();
            syncStatus.textContent = `Last synced: ${lastSyncDate}`;
            syncStatus.className = 'sync-status success';
        }
        
        // Show success notification
        showNotification(data.message, 'success');
        
        // Load activities
        loadStravaActivities();
        
        // Reset button
        syncBtn.textContent = originalText;
        syncBtn.disabled = false;
    })
    .catch(error => {
        console.error('Error syncing Strava data:', error);
        
        // Update sync status
        if (syncStatus) {
            syncStatus.textContent = `Sync failed: ${error.message}`;
            syncStatus.className = 'sync-status error';
        }
        
        // Show error notification
        showNotification(`Error syncing Strava data: ${error.message}`, 'error');
        
        // Reset button
        syncBtn.textContent = originalText;
        syncBtn.disabled = false;
    });
}

function checkStravaStatus() {
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    // Show loading indicator
    const connectionStatus = document.getElementById('strava-connection-status');
    if (connectionStatus) {
        connectionStatus.textContent = 'Checking...';
    }
    
    fetch(`/api/strava/status?user_id=${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateStravaUI(data);
            
            // If connected, load activities
            if (data.connected) {
                loadStravaActivities();
            }
        })
        .catch(error => {
            console.error('Error checking Strava status:', error);
            
            // Update UI to show error
            const connectionStatus = document.getElementById('strava-connection-status');
            if (connectionStatus) {
                connectionStatus.textContent = 'Connection Error';
                connectionStatus.className = 'error';
            }
        });
}

function updateStravaUI(statusData) {
    const connectionStatus = document.getElementById('strava-connection-status');
    const connectBtn = document.getElementById('strava-connect-btn');
    const syncBtn = document.querySelector('.strava-sync-btn');
    const configureBtn = document.getElementById('strava-configure-btn');
    
    if (statusData.connected) {
        // Update connection status
        if (connectionStatus) {
            connectionStatus.textContent = 'Connected';
            connectionStatus.className = 'connected';
        }
        
        // Show/hide buttons
        if (connectBtn) connectBtn.style.display = 'none';
        if (syncBtn) syncBtn.style.display = 'inline-block';
        if (configureBtn) configureBtn.style.display = 'inline-block';
        
        // Update last sync info if available
        if (statusData.last_sync) {
            const syncStatus = document.getElementById('strava-sync-status');
            if (syncStatus) {
                const lastSyncDate = new Date(statusData.last_sync).toLocaleString();
                syncStatus.textContent = `Last synced: ${lastSyncDate}`;
                syncStatus.className = 'sync-status success';
            }
        }
        
        // Check if token is expired
        if (statusData.token_expired) {
            const syncStatus = document.getElementById('strava-sync-status');
            if (syncStatus) {
                syncStatus.textContent = 'Token expired, please sync to refresh';
                syncStatus.className = 'sync-status error';
            }
        }
    } else {
        // Update connection status
        if (connectionStatus) {
            connectionStatus.textContent = 'Not Connected';
            connectionStatus.className = 'not-connected';
        }
        
        // Show/hide buttons
        if (connectBtn) connectBtn.style.display = 'inline-block';
        if (syncBtn) syncBtn.style.display = 'none';
        if (configureBtn) configureBtn.style.display = 'none';
        
        // Show no data message
        document.getElementById('no-activity-data').style.display = 'block';
        document.getElementById('no-activities-message').style.display = 'block';
    }
}

function loadStravaActivities() {
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    // Show loading indicators
    const activityContainer = document.getElementById('activity-data-container');
    const chartContainer = document.getElementById('activity-chart-container');
    const workoutContainer = document.getElementById('recent-workouts-container');
    
    if (activityContainer) {
        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'spinner';
        loadingSpinner.id = 'activity-spinner';
        activityContainer.appendChild(loadingSpinner);
    }
    
    if (chartContainer) {
        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'spinner';
        loadingSpinner.id = 'chart-spinner';
        chartContainer.appendChild(loadingSpinner);
    }
    
    fetch(`/api/strava/activities?user_id=${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove loading spinners
            const activitySpinner = document.getElementById('activity-spinner');
            const chartSpinner = document.getElementById('chart-spinner');
            if (activitySpinner) activitySpinner.remove();
            if (chartSpinner) chartSpinner.remove();
            
            if (data.success) {
                displayActivities(data.activities);
                updateActivityChart(data.activities);
                updateActivityStats(data.activities);
                
                // Hide no data messages if we have activities
                if (data.activities && data.activities.length > 0) {
                    const noActivityData = document.getElementById('no-activity-data');
                    const noActivitiesMessage = document.getElementById('no-activities-message');
                    if (noActivityData) noActivityData.style.display = 'none';
                    if (noActivitiesMessage) noActivitiesMessage.style.display = 'none';
                } else {
                    const noActivityData = document.getElementById('no-activity-data');
                    const noActivitiesMessage = document.getElementById('no-activities-message');
                    if (noActivityData) noActivityData.style.display = 'block';
                    if (noActivitiesMessage) noActivitiesMessage.style.display = 'block';
                }
            } else {
                console.error('Failed to load activities:', data.error);
                showNotification(`Failed to load activities: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            // Remove loading spinners
            const activitySpinner = document.getElementById('activity-spinner');
            const chartSpinner = document.getElementById('chart-spinner');
            if (activitySpinner) activitySpinner.remove();
            if (chartSpinner) chartSpinner.remove();
            
            console.error('Error loading activities:', error);
            showNotification(`Error loading activities: ${error.message}`, 'error');
        });
}

function displayActivities(activities) {
    const container = document.getElementById('activity-data-container');
    if (!container) return;
    
    // Clear existing content except the no-data message
    const noDataMessage = document.getElementById('no-activities-message');
    container.innerHTML = '';
    if (noDataMessage) {
        container.appendChild(noDataMessage);
    }
    
    // Check if we have activities
    if (!activities || activities.length === 0) {
        if (noDataMessage) {
            noDataMessage.style.display = 'block';
        }
        return;
    }
    
    // Hide no data message
    if (noDataMessage) {
        noDataMessage.style.display = 'none';
    }
    
    // Create activity cards
    activities.forEach(activity => {
        const card = createActivityCard(activity);
        container.appendChild(card);
    });
    
    // Also update recent workouts in dashboard
    updateRecentWorkouts(activities.slice(0, 3));
}

function createActivityCard(activity) {
    const card = document.createElement('div');
    card.className = 'card activity-card';
    
    const date = new Date(activity.start_date).toLocaleDateString();
    const duration = formatDuration(activity.elapsed_time);
    const distance = activity.distance ? (activity.distance / 1000).toFixed(2) + ' km' : 'N/A';
    
    card.innerHTML = `
        <h3>${activity.name || 'Unnamed Activity'}</h3>
        <div class="card-content">
            <div class="activity-details">
                <p><strong>Date:</strong> ${date}</p>
                <p><strong>Type:</strong> ${activity.type || 'Unknown'}</p>
                <p><strong>Distance:</strong> ${distance}</p>
                <p><strong>Duration:</strong> ${duration}</p>
                <p><strong>Elevation Gain:</strong> ${activity.total_elevation_gain || 0} m</p>
                ${activity.average_heartrate ? `<p><strong>Avg Heart Rate:</strong> ${activity.average_heartrate} bpm</p>` : ''}
                ${activity.max_heartrate ? `<p><strong>Max Heart Rate:</strong> ${activity.max_heartrate} bpm</p>` : ''}
            </div>
        </div>
    `;
    
    return card;
}

function updateRecentWorkouts(activities) {
    const container = document.getElementById('workout-list');
    const noWorkoutMessage = document.getElementById('no-workout-data');
    
    if (!container) return;
    
    // Clear existing content
    container.innerHTML = '';
    
    // Check if we have activities
    if (!activities || activities.length === 0) {
        if (noWorkoutMessage) {
            noWorkoutMessage.style.display = 'block';
        }
        return;
    }
    
    // Hide no data message
    if (noWorkoutMessage) {
        noWorkoutMessage.style.display = 'none';
    }
    
    // Create workout items
    activities.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'workout-item';
        
        const date = new Date(activity.start_date).toLocaleDateString();
        const duration = formatDuration(activity.elapsed_time);
        
        item.innerHTML = `
            <div class="workout-title">${activity.name || 'Unnamed Activity'}</div>
            <div class="workout-details">
                <span>${activity.type || 'Unknown'}</span>
                <span>${date}</span>
                <span>${duration}</span>
            </div>
        `;
        
        container.appendChild(item);
    });
}

function updateActivityChart(activities) {
    const chartContainer = document.getElementById('activity-chart');
    if (!chartContainer) return;
    
    // Check if we have activities
    if (!activities || activities.length === 0) {
        return;
    }
    
    // Sort activities by date
    activities.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    
    // Limit to last 7 activities for readability
    const recentActivities = activities.slice(-7);
    
    // Extract data for chart
    const labels = recentActivities.map(a => new Date(a.start_date).toLocaleDateString());
    const distances = recentActivities.map(a => a.distance ? (a.distance / 1000).toFixed(2) : 0); // km
    const heartRates = recentActivities.map(a => a.average_heartrate || 0); // bpm
    
    // Create chart data
    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Distance (km)',
                data: distances,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                yAxisID: 'y'
            },
            {
                label: 'Heart Rate (bpm)',
                data: heartRates,
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                yAxisID: 'y1'
            }
        ]
    };
    
    // Check if chart already exists and destroy it
    if (window.activityChart) {
        window.activityChart.destroy();
    }
    
    // Create new chart
    const ctx = chartContainer.getContext('2d');
    window.activityChart = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Distance (km)'
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Heart Rate (bpm)'
                    }
                }
            }
        }
    });
}

function updateActivityStats(activities) {
    if (!activities || activities.length === 0) return;
    
    // Calculate total distance
    const totalDistance = activities.reduce((sum, activity) => {
        return sum + (activity.distance || 0);
    }, 0) / 1000; // Convert to km
    
    // Calculate average heart rate
    let totalHeartRate = 0;
    let heartRateCount = 0;
    activities.forEach(activity => {
        if (activity.average_heartrate) {
            totalHeartRate += activity.average_heartrate;
            heartRateCount++;
        }
    });
    const avgHeartRate = heartRateCount > 0 ? Math.round(totalHeartRate / heartRateCount) : 0;
    
    // Update stats in UI
    const totalDistanceEl = document.getElementById('total-distance');
    const avgHeartRateEl = document.getElementById('avg-heart-rate');
    const activityCountEl = document.getElementById('activity-count');
    
    if (totalDistanceEl) totalDistanceEl.textContent = `${totalDistance.toFixed(2)} km`;
    if (avgHeartRateEl) avgHeartRateEl.textContent = `${avgHeartRate} bpm`;
    if (activityCountEl) activityCountEl.textContent = activities.length;
}

function formatDuration(seconds) {
    if (!seconds) return 'N/A';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function showNotification(message, type = 'info') {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        document.body.appendChild(notification);
        
        // Add styles
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '10px 20px';
        notification.style.borderRadius = '4px';
        notification.style.color = 'white';
        notification.style.fontWeight = 'bold';
        notification.style.zIndex = '1000';
        notification.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
        notification.style.transition = 'opacity 0.3s ease-in-out';
    }
    
    // Set type-specific styles
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#4CAF50';
            break;
        case 'error':
            notification.style.backgroundColor = '#F44336';
            break;
        case 'warning':
            notification.style.backgroundColor = '#FF9800';
            break;
        default:
            notification.style.backgroundColor = '#2196F3';
    }
    
    // Set message
    notification.textContent = message;
    
    // Show notification
    notification.style.opacity = '1';
    
    // Hide after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}
