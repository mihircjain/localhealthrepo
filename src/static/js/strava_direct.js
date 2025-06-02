// Strava Direct Data Fetch and Display

document.addEventListener('DOMContentLoaded', function() {
    // Set up event listener for Show Data button
    const showDataBtn = document.getElementById('strava-show-data-btn');
    if (showDataBtn) {
        showDataBtn.addEventListener('click', fetchAndDisplayStravaData);
    }
});

function fetchAndDisplayStravaData() {
    // Show loading state
    const showDataBtn = document.getElementById('strava-show-data-btn');
    if (showDataBtn) {
        showDataBtn.textContent = 'Loading...';
        showDataBtn.disabled = true;
    }
    
    // Create modal for displaying data
    createDataModal();
    
    // Fetch data from backend
    fetch('/api/strava-direct/fetch')
        .then(response => response.json())
        .then(data => {
            // Reset button state
            if (showDataBtn) {
                showDataBtn.textContent = 'Show Data';
                showDataBtn.disabled = false;
            }
            
            if (data.success) {
                displayActivitiesTable(data.activities);
            } else {
                displayErrorMessage(data.error || 'Failed to fetch Strava data');
            }
        })
        .catch(error => {
            // Reset button state
            if (showDataBtn) {
                showDataBtn.textContent = 'Show Data';
                showDataBtn.disabled = false;
            }
            
            console.error('Error fetching Strava data:', error);
            displayErrorMessage('Error fetching Strava data. Please try again.');
        });
}

function createDataModal() {
    // Remove existing modal if any
    const existingModal = document.getElementById('strava-data-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal container
    const modal = document.createElement('div');
    modal.id = 'strava-data-modal';
    modal.className = 'modal';
    
    // Create modal content
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Strava Activities (Last 20 Days)</h3>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                <div id="strava-data-loading">Loading Strava data...</div>
                <div id="strava-data-error" style="display: none;"></div>
                <div id="strava-data-table-container" style="display: none;">
                    <table id="strava-data-table" class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Activity</th>
                                <th>Type</th>
                                <th>Distance (km)</th>
                                <th>Duration (min)</th>
                                <th>Heart Rate</th>
                                <th>Elevation (m)</th>
                            </tr>
                        </thead>
                        <tbody id="strava-data-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to body
    document.body.appendChild(modal);
    
    // Show modal
    modal.style.display = 'block';
    
    // Add event listener to close button
    const closeBtn = modal.querySelector('.modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

function displayActivitiesTable(activities) {
    const loadingElement = document.getElementById('strava-data-loading');
    const errorElement = document.getElementById('strava-data-error');
    const tableContainer = document.getElementById('strava-data-table-container');
    const tableBody = document.getElementById('strava-data-tbody');
    
    if (!tableBody) return;
    
    // Hide loading and error messages
    if (loadingElement) loadingElement.style.display = 'none';
    if (errorElement) errorElement.style.display = 'none';
    
    // Show table container
    if (tableContainer) tableContainer.style.display = 'block';
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Check if we have activities
    if (!activities || activities.length === 0) {
        if (tableContainer) tableContainer.style.display = 'none';
        if (errorElement) {
            errorElement.textContent = 'No activities found in the last 20 days.';
            errorElement.style.display = 'block';
        }
        return;
    }
    
    // Add rows for each activity
    activities.forEach(activity => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${activity.date}</td>
            <td>${activity.name}</td>
            <td>${activity.type}</td>
            <td>${activity.distance}</td>
            <td>${activity.duration}</td>
            <td>${activity.heart_rate}</td>
            <td>${activity.elevation_gain}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function displayErrorMessage(message) {
    const loadingElement = document.getElementById('strava-data-loading');
    const errorElement = document.getElementById('strava-data-error');
    const tableContainer = document.getElementById('strava-data-table-container');
    
    // Hide loading and table
    if (loadingElement) loadingElement.style.display = 'none';
    if (tableContainer) tableContainer.style.display = 'none';
    
    // Show error message
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}
