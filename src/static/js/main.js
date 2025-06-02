// Main JavaScript for Health Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI
    initializeUI();
    
    // Check Strava connection status
    checkStravaStatus();
    
    // Set up event listeners
    setupEventListeners();
});

function initializeUI() {
    // Navigation
    const navLinks = document.querySelectorAll('nav a');
    const sections = document.querySelectorAll('main section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            
            // Update active nav link
            navLinks.forEach(link => link.classList.remove('active'));
            this.classList.add('active');
            
            // Show target section, hide others
            sections.forEach(section => {
                if (section.id === targetId) {
                    section.classList.add('active-section');
                } else {
                    section.classList.remove('active-section');
                }
            });
        });
    });
    
    // Initialize Strava connect button
    const stravaConnectBtn = document.getElementById('strava-connect-btn');
    if (stravaConnectBtn) {
        stravaConnectBtn.addEventListener('click', connectStrava);
    }
    
    // Initialize Strava configure button
    const stravaConfigureBtn = document.getElementById('strava-configure-btn');
    if (stravaConfigureBtn) {
        stravaConfigureBtn.addEventListener('click', configureStrava);
    }
    
    // Initialize chat
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input-field');
    
    if (chatSendBtn && chatInput) {
        chatSendBtn.addEventListener('click', function() {
            sendChatMessage(chatInput.value);
            chatInput.value = '';
        });
        
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage(this.value);
                this.value = '';
            }
        });
    }
}

function setupEventListeners() {
    // Activity filter button
    const activityFilterBtn = document.getElementById('activity-filter-btn');
    if (activityFilterBtn) {
        activityFilterBtn.addEventListener('click', filterActivities);
    }
}

function checkStravaStatus() {
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    fetch(`/api/strava/status?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            updateStravaUI(data);
        })
        .catch(error => {
            console.error('Error checking Strava status:', error);
        });
}

function updateStravaUI(statusData) {
    const connectionStatus = document.getElementById('strava-connection-status');
    const connectBtn = document.getElementById('strava-connect-btn');
    const syncBtn = document.querySelector('.strava-sync-btn');
    const configureBtn = document.getElementById('strava-configure-btn');
    
    if (statusData.connected) {
        // Update connection status
        connectionStatus.textContent = 'Connected';
        connectionStatus.className = 'connected';
        
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
        
        // Load activities
        loadStravaActivities();
    } else {
        // Update connection status
        connectionStatus.textContent = 'Not Connected';
        connectionStatus.className = 'not-connected';
        
        // Show/hide buttons
        if (connectBtn) connectBtn.style.display = 'inline-block';
        if (syncBtn) syncBtn.style.display = 'none';
        if (configureBtn) configureBtn.style.display = 'none';
        
        // Show no data message
        document.getElementById('no-activity-data').style.display = 'block';
        document.getElementById('no-activities-message').style.display = 'block';
    }
}

function connectStrava() {
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    fetch(`/api/strava/auth?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                console.error('Failed to get Strava auth URL');
            }
        })
        .catch(error => {
            console.error('Error connecting to Strava:', error);
        });
}

function configureStrava() {
    // This would open Strava configuration options
    alert('Strava configuration options would appear here.');
}

function loadStravaActivities() {
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    fetch(`/api/strava/activities?user_id=${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayActivities(data.activities);
                updateActivityChart(data.activities);
                
                // Hide no data messages if we have activities
                if (data.activities && data.activities.length > 0) {
                    document.getElementById('no-activity-data').style.display = 'none';
                    document.getElementById('no-activities-message').style.display = 'none';
                } else {
                    document.getElementById('no-activity-data').style.display = 'block';
                    document.getElementById('no-activities-message').style.display = 'block';
                }
            } else {
                console.error('Failed to load activities:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading activities:', error);
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
        <div class="activity-details">
            <p><strong>Date:</strong> ${date}</p>
            <p><strong>Type:</strong> ${activity.type || 'Unknown'}</p>
            <p><strong>Distance:</strong> ${distance}</p>
            <p><strong>Duration:</strong> ${duration}</p>
            <p><strong>Elevation Gain:</strong> ${activity.total_elevation_gain || 0} m</p>
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
    const durations = recentActivities.map(a => a.elapsed_time ? Math.round(a.elapsed_time / 60) : 0); // minutes
    
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
                label: 'Duration (min)',
                data: durations,
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
                        text: 'Duration (min)'
                    }
                }
            }
        }
    });
}

function filterActivities() {
    const typeFilter = document.getElementById('activity-type-filter').value;
    const dateFilter = document.getElementById('activity-date-filter').value;
    
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    // Build query parameters
    let queryParams = `user_id=${userId}`;
    if (typeFilter && typeFilter !== 'all') {
        queryParams += `&type=${typeFilter}`;
    }
    if (dateFilter) {
        queryParams += `&date=${dateFilter}`;
    }
    
    fetch(`/api/strava/activities?${queryParams}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayActivities(data.activities);
            } else {
                console.error('Failed to filter activities:', data.error);
            }
        })
        .catch(error => {
            console.error('Error filtering activities:', error);
        });
}

function formatDuration(seconds) {
    if (!seconds) return 'N/A';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function sendChatMessage(message) {
    if (!message.trim()) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Get current user ID (in a real app, this would be from auth)
    const userId = 1; // Placeholder
    
    // Send message to backend
    fetch('/api/chat/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            query: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add response to chat
            addMessageToChat('system', data.response);
        } else {
            // Add error message
            addMessageToChat('system', 'Sorry, I encountered an error processing your request.');
            console.error('Chat error:', data.error);
        }
    })
    .catch(error => {
        // Add error message
        addMessageToChat('system', 'Sorry, I encountered an error processing your request.');
        console.error('Error sending chat message:', error);
    });
}

function addMessageToChat(sender, content) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<p>${content}</p>`;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
