// Strava Charts JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listener for Show Charts button
    const showChartsBtn = document.getElementById('strava-show-charts-btn');
    if (showChartsBtn) {
        showChartsBtn.addEventListener('click', fetchAndDisplayStravaCharts);
    }
});

function fetchAndDisplayStravaCharts() {
    // Show loading state
    const showChartsBtn = document.getElementById('strava-show-charts-btn');
    if (showChartsBtn) {
        showChartsBtn.textContent = 'Loading...';
        showChartsBtn.disabled = true;
    }
    
    // Create modal for displaying charts
    createChartsModal();
    
    // Fetch chart data from backend
    fetch('/api/strava-direct/chart-data')
        .then(response => response.json())
        .then(data => {
            // Reset button state
            if (showChartsBtn) {
                showChartsBtn.textContent = 'Show Charts';
                showChartsBtn.disabled = false;
            }
            
            if (data.success) {
                renderCharts(data);
            } else {
                displayChartErrorMessage(data.error || 'Failed to fetch Strava chart data');
            }
        })
        .catch(error => {
            // Reset button state
            if (showChartsBtn) {
                showChartsBtn.textContent = 'Show Charts';
                showChartsBtn.disabled = false;
            }
            
            console.error('Error fetching Strava chart data:', error);
            displayChartErrorMessage('Error fetching Strava chart data. Please try again.');
        });
}

function createChartsModal() {
    // Remove existing modal if any
    const existingModal = document.getElementById('strava-charts-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal container
    const modal = document.createElement('div');
    modal.id = 'strava-charts-modal';
    modal.className = 'modal charts-modal';
    
    // Create modal content
    modal.innerHTML = `
        <div class="modal-content charts-modal-content">
            <div class="modal-header">
                <h3>Strava Activity Insights</h3>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                <div id="strava-charts-loading">Loading Strava chart data...</div>
                <div id="strava-charts-error" style="display: none;"></div>
                <div id="strava-charts-container" style="display: none;">
                    <div class="charts-grid">
                        <div class="chart-container">
                            <h4>Heart Rate Over Time</h4>
                            <canvas id="heart-rate-chart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h4>Speed Over Time</h4>
                            <canvas id="speed-chart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h4>Distance Over Time</h4>
                            <canvas id="distance-chart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h4>Duration Over Time</h4>
                            <canvas id="duration-chart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h4>Elevation Gain Over Time</h4>
                            <canvas id="elevation-chart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h4>Activity Type Distribution</h4>
                            <canvas id="activity-distribution-chart"></canvas>
                        </div>
                    </div>
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

function renderCharts(data) {
    const loadingElement = document.getElementById('strava-charts-loading');
    const errorElement = document.getElementById('strava-charts-error');
    const chartsContainer = document.getElementById('strava-charts-container');
    
    // Hide loading and error messages
    if (loadingElement) loadingElement.style.display = 'none';
    if (errorElement) errorElement.style.display = 'none';
    
    // Show charts container
    if (chartsContainer) chartsContainer.style.display = 'block';
    
    // Check if we have data
    if (!data) {
        if (chartsContainer) chartsContainer.style.display = 'none';
        if (errorElement) {
            errorElement.textContent = 'No activity data found.';
            errorElement.style.display = 'block';
        }
        return;
    }
    
    // Common chart options
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false,
            }
        },
        scales: {
            x: {
                ticks: {
                    maxRotation: 45,
                    minRotation: 45
                }
            }
        }
    };
    
    // Render Heart Rate Chart
    if (data.heart_rate) {
        const ctx = document.getElementById('heart-rate-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: data.heart_rate,
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Heart Rate (bpm)'
                        }
                    }
                }
            }
        });
    }
    
    // Render Speed Chart
    if (data.speed) {
        const ctx = document.getElementById('speed-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: data.speed,
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Speed (km/h)'
                        }
                    }
                }
            }
        });
    }
    
    // Render Distance Chart
    if (data.distance) {
        const ctx = document.getElementById('distance-chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: data.distance,
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Distance (km)'
                        }
                    }
                }
            }
        });
    }
    
    // Render Duration Chart
    if (data.duration) {
        const ctx = document.getElementById('duration-chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: data.duration,
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Duration (min)'
                        }
                    }
                }
            }
        });
    }
    
    // Render Elevation Chart
    if (data.elevation) {
        const ctx = document.getElementById('elevation-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: data.elevation,
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Elevation Gain (m)'
                        }
                    }
                }
            }
        });
    }
    
    // Render Activity Distribution Chart
    if (data.activity_distribution) {
        const ctx = document.getElementById('activity-distribution-chart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: data.activity_distribution,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}

function displayChartErrorMessage(message) {
    const loadingElement = document.getElementById('strava-charts-loading');
    const errorElement = document.getElementById('strava-charts-error');
    const chartsContainer = document.getElementById('strava-charts-container');
    
    // Hide loading and charts
    if (loadingElement) loadingElement.style.display = 'none';
    if (chartsContainer) chartsContainer.style.display = 'none';
    
    // Show error message
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}
