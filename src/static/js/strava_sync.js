// Strava Sync Functionality

document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to Strava sync buttons
    const syncButtons = document.querySelectorAll('.strava-sync-btn');
    syncButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            syncStravaData(userId);
        });
    });
});

function syncStravaData(userId) {
    // Show loading indicator
    const statusElement = document.getElementById('strava-sync-status');
    if (statusElement) {
        statusElement.textContent = 'Syncing...';
        statusElement.className = 'sync-status syncing';
    }
    
    // Disable sync button during sync
    const syncButton = document.querySelector('.strava-sync-btn');
    if (syncButton) {
        syncButton.disabled = true;
    }
    
    // Call the backend API to sync Strava data
    fetch('/api/strava/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        // Update status based on response
        if (statusElement) {
            if (data.success) {
                statusElement.textContent = 'Sync completed successfully!';
                statusElement.className = 'sync-status success';
                
                // Refresh the activity data display
                refreshActivityDisplay();
            } else {
                statusElement.textContent = 'Sync failed: ' + data.error;
                statusElement.className = 'sync-status error';
            }
        }
        
        // Re-enable sync button
        if (syncButton) {
            syncButton.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error syncing Strava data:', error);
        
        // Update status on error
        if (statusElement) {
            statusElement.textContent = 'Sync failed: Network error';
            statusElement.className = 'sync-status error';
        }
        
        // Re-enable sync button
        if (syncButton) {
            syncButton.disabled = false;
        }
    });
}

function refreshActivityDisplay() {
    // Fetch the latest activity data
    fetch('/api/strava/activities')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear any existing sample data
                const activityContainer = document.getElementById('activity-data-container');
                if (activityContainer) {
                    // Clear existing content
                    activityContainer.innerHTML = '';
                    
                    // Check if we have activities
                    if (data.activities && data.activities.length > 0) {
                        // Create activity cards for each activity
                        data.activities.forEach(activity => {
                            const activityCard = createActivityCard(activity);
                            activityContainer.appendChild(activityCard);
                        });
                    } else {
                        // No activities found
                        activityContainer.innerHTML = '<div class="no-data-message">No Strava activities found. Try syncing again or check your Strava account.</div>';
                    }
                }
                
                // Update activity chart if it exists
                updateActivityChart(data.activities || []);
            } else {
                console.error('Failed to fetch activities:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching activities:', error);
        });
}

function createActivityCard(activity) {
    const card = document.createElement('div');
    card.className = 'activity-card';
    
    const date = new Date(activity.start_date).toLocaleDateString();
    const duration = formatDuration(activity.elapsed_time);
    
    card.innerHTML = `
        <h3>${activity.name}</h3>
        <div class="activity-details">
            <p><strong>Date:</strong> ${date}</p>
            <p><strong>Type:</strong> ${activity.type}</p>
            <p><strong>Distance:</strong> ${(activity.distance / 1000).toFixed(2)} km</p>
            <p><strong>Duration:</strong> ${duration}</p>
            <p><strong>Elevation Gain:</strong> ${activity.total_elevation_gain} m</p>
        </div>
    `;
    
    return card;
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function updateActivityChart(activities) {
    const chartContainer = document.getElementById('activity-chart');
    if (!chartContainer) return;
    
    // Sort activities by date
    activities.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    
    // Extract data for chart
    const labels = activities.map(a => new Date(a.start_date).toLocaleDateString());
    const distances = activities.map(a => (a.distance / 1000).toFixed(2)); // km
    const elevations = activities.map(a => a.total_elevation_gain);
    
    // Create chart data
    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Distance (km)',
                data: distances,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            },
            {
                label: 'Elevation Gain (m)',
                data: elevations,
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
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
                    beginAtZero: true
                }
            }
        }
    });
}
