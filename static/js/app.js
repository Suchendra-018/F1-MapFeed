// F1 MapFeed Dashboard - Frontend Logic

let currentSession = null;
let currentDrivers = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSessions();
    setupEventListeners();
});

// Load available sessions
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const sessions = await response.json();
        
        const sessionSelect = document.getElementById('sessionSelect');
        sessionSelect.innerHTML = '<option value="">Select a session...</option>';
        
        sessions.forEach(session => {
            const option = document.createElement('option');
            option.value = JSON.stringify({
                year: session.year,
                race: session.race,
                session: session.session
            });
            option.textContent = session.display;
            sessionSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading sessions:', error);
        alert('Failed to load sessions');
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('sessionSelect').addEventListener('change', onSessionSelected);
    document.getElementById('analyzeBtn').addEventListener('click', onAnalyzeDriver);
    document.getElementById('doCompareBtn').addEventListener('click', onCompareDrivers);
}

// Session selection changed
async function onSessionSelected(e) {
    const value = e.target.value;
    const driverSelect = document.getElementById('driverSelect');
    
    if (!value) {
        driverSelect.disabled = true;
        driverSelect.innerHTML = '<option value="">Select session first</option>';
        return;
    }
    
    currentSession = JSON.parse(value);
    driverSelect.disabled = false;
    driverSelect.innerHTML = '<option value="">Loading drivers...</option>';
    
    try {
        const response = await fetch(
            `/api/drivers/${currentSession.year}/${currentSession.race}/${currentSession.session}`
        );
        const drivers = await response.json();
        
        driverSelect.innerHTML = '<option value="">Select a driver...</option>';
        drivers.forEach(driver => {
            const option = document.createElement('option');
            option.value = driver.code;
            option.textContent = `${driver.code} - ${driver.name}`;
            driverSelect.appendChild(option);
        });
        
        currentDrivers = drivers.map(d => d.code);
        updateCompareModal();
    } catch (error) {
        console.error('Error loading drivers:', error);
        driverSelect.innerHTML = '<option value="">Error loading drivers</option>';
    }
}

// Analyze single driver
async function onAnalyzeDriver() {
    const driverCode = document.getElementById('driverSelect').value;
    
    if (!currentSession || !driverCode) {
        alert('Please select both session and driver');
        return;
    }
    
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = '<div class="loading"><div class="spinner-border loading-spinner"></div><p>Analyzing driver telemetry...</p></div>';
    
    try {
        const response = await fetch('/api/driver-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                year: currentSession.year,
                race: currentSession.race,
                session: currentSession.session,
                driver: driverCode
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            mainContent.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            return;
        }
        
        displayAnalysis(driverCode, data);
    } catch (error) {
        console.error('Error analyzing driver:', error);
        mainContent.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// Display analysis results
function displayAnalysis(driver, data) {
    const mainContent = document.getElementById('mainContent');
    
    let html = `
        <h3 class="mb-4">Driver Analysis: ${driver}</h3>
        
        <h5 class="section-title">Performance Statistics</h5>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Max Speed</div>
                <div class="stat-value">${data.stats.max_speed}</div>
                <small>km/h</small>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average Speed</div>
                <div class="stat-value">${data.stats.avg_speed}</div>
                <small>km/h</small>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Throttle</div>
                <div class="stat-value">${data.stats.avg_throttle}</div>
                <small>%</small>
            </div>
            <div class="stat-card">
                <div class="stat-label">Max RPM</div>
                <div class="stat-value">${data.stats.max_rpm}</div>
                <small>rpm</small>
            </div>
        </div>
        
        <h5 class="section-title">Sector Times</h5>
        <div class="row">
    `;
    
    Object.entries(data.sectors).forEach(([sector, time]) => {
        html += `
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-label">${sector}</div>
                    <div class="stat-value">${time}</div>
                </div>
            </div>
        `;
    });
    
    html += `
        </div>
        
        <h5 class="section-title">Throttle & Brake Analysis</h5>
        <div class="row">
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-label">Full Throttle Points</div>
                    <div class="stat-value">${data.throttle_brake.full_throttle_points}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-label">Full Brake Points</div>
                    <div class="stat-value">${data.throttle_brake.full_brake_points}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-label">Throttle % of Lap</div>
                    <div class="stat-value">${data.throttle_brake.throttle_percentage}</div>
                    <small>%</small>
                </div>
            </div>
        </div>
        
        <h5 class="section-title">Visualizations</h5>
        <div class="row">
            <div class="col-lg-6">
                <div class="plot-container">
                    <h6>Speed vs Distance</h6>
                    <img src="/plots/${data.plots.speed_graph}?t=${Date.now()}" alt="Speed Graph">
                </div>
            </div>
            <div class="col-lg-6">
                <div class="plot-container">
                    <h6>Speed Heatmap</h6>
                    <img src="/plots/${data.plots.speed_heatmap}?t=${Date.now()}" alt="Speed Heatmap">
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-lg-12">
                <div class="plot-container">
                    <h6>Circuit Layout</h6>
                    <img src="/plots/${data.plots.track_map}?t=${Date.now()}" alt="Track Map">
                </div>
            </div>
        </div>
    `;
    
    mainContent.innerHTML = html;
}

// Update compare modal with driver checkboxes
function updateCompareModal() {
    const checkboxContainer = document.getElementById('driverCheckboxes');
    checkboxContainer.innerHTML = '';
    
    if (currentDrivers.length === 0) return;
    
    currentDrivers.forEach(driver => {
        const div = document.createElement('div');
        div.className = 'form-check';
        div.innerHTML = `
            <input class="form-check-input" type="checkbox" value="${driver}" id="driver_${driver}">
            <label class="form-check-label" for="driver_${driver}">
                ${driver}
            </label>
        `;
        checkboxContainer.appendChild(div);
    });
}

// Compare multiple drivers
async function onCompareDrivers() {
    const checkboxes = document.querySelectorAll('#driverCheckboxes input[type="checkbox"]:checked');
    const selectedDrivers = Array.from(checkboxes).map(cb => cb.value);
    
    if (selectedDrivers.length < 2) {
        alert('Please select at least 2 drivers to compare');
        return;
    }
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('compareModal'));
    modal.hide();
    
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = '<div class="loading"><div class="spinner-border loading-spinner"></div><p>Comparing drivers...</p></div>';
    
    try {
        const response = await fetch('/api/compare-drivers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                year: currentSession.year,
                race: currentSession.race,
                session: currentSession.session,
                drivers: selectedDrivers
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            mainContent.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            return;
        }
        
        displayComparison(selectedDrivers, data);
    } catch (error) {
        console.error('Error comparing drivers:', error);
        mainContent.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// Display comparison results
function displayComparison(drivers, data) {
    const mainContent = document.getElementById('mainContent');
    
    let html = `
        <h3 class="mb-4">Driver Comparison: ${drivers.join(' vs ')}</h3>
        
        <h5 class="section-title">Speed Profile</h5>
        <div class="comparison-table">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Driver</th>
                        <th>Max Speed (km/h)</th>
                        <th>Avg Speed (km/h)</th>
                        <th>Consistency (Std Dev)</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    Object.entries(data.speed_comparison).forEach(([driver, stats]) => {
        html += `
            <tr>
                <td><strong>${driver}</strong></td>
                <td>${stats.max_speed}</td>
                <td>${stats.avg_speed}</td>
                <td>${stats.consistency}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        
        <h5 class="section-title">Race Pace</h5>
        <div class="comparison-table">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Driver</th>
                        <th>Avg Pace (s)</th>
                        <th>Fastest Lap (s)</th>
                        <th>Consistency (Std Dev)</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    Object.entries(data.race_pace).forEach(([driver, stats]) => {
        html += `
            <tr>
                <td><strong>${driver}</strong></td>
                <td>${stats.avg_pace}</td>
                <td>${stats.fastest_lap}</td>
                <td>${stats.consistency}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
        
        <h5 class="section-title">Comparison Visualization</h5>
        <div class="plot-container">
            <img src="/plots/${data.plots.comparison}?t=${Date.now()}" alt="Driver Comparison">
        </div>
    `;
    
    mainContent.innerHTML = html;
}
