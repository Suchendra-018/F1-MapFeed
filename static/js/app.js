// F1 MapFeed Dashboard - Frontend Logic

let currentSession = null;
let currentDrivers = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('intelligenceApp')) return;
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
        
        currentDrivers = drivers;
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
            <input class="form-check-input" type="checkbox" value="${driver.code}"
id="driver_${driver.code}">
            <label class="form-check-label" for="driver_${driver.code}">
                ${driver.name}
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

// Integrated performance intelligence dashboard (keeps legacy analysis endpoints intact).
(() => {
    const $ = id => document.getElementById(id);
    let state = { event: null, drivers: [] };
    const fetchJson = async (url, options) => { const response = await fetch(url, options); const data = await response.json(); if (!response.ok || data.error) throw new Error(data.error || 'Request failed'); return data; };
    const option = (value, text) => `<option value="${value}">${text}</option>`;
    const pace = value => value == null ? '—' : `${value.toFixed(3)}s`;
    const status = (text, loading = false) => { $('intelStatus').textContent = text; $('intelStatus').classList.toggle('loading', loading); };
    const payload = () => ({ year: +$('intelYear').value, race: state.event.name, session: $('intelType').value });

    async function years() {
        try { const data = await fetchJson('/api/years'); $('intelYear').innerHTML = '<option value="">Season</option>' + data.reverse().map(y => option(y, y)).join(''); $('intelYear').value = data[0]; events(); } catch (error) { status(error.message); }
    }
    async function events() {
        const year = $('intelYear').value; $('intelEvent').disabled = !year; $('intelType').disabled = true; $('intelLoad').disabled = true; $('intelEvent').innerHTML = '<option>Loading calendar…</option>';
        if (!year) return;
        try { const data = await fetchJson(`/api/events/${year}`); $('intelEvent').innerHTML = '<option value="">Grand Prix</option>' + data.map(e => option(e.round, `${e.round}. ${e.name}`)).join(''); } catch (error) { status(error.message); }
    }
    async function sessionTypes() {
        const year = $('intelYear').value, round = $('intelEvent').value; $('intelType').disabled = !round; $('intelLoad').disabled = true;
        if (!round) return;
        try { const data = await fetchJson(`/api/sessions/${year}/${round}`); state.event = data.event; $('intelType').innerHTML = data.sessions.map(s => option(s.code, s.name)).join(''); $('intelLoad').disabled = false; } catch (error) { status(error.message); }
    }
    function kpis(summary) { const items = [['FASTEST DRIVER',summary.fastest_driver,pace(summary.fastest_lap)],['HIGHEST SPEED',summary.highest_speed_driver,summary.highest_speed ? `${summary.highest_speed} km/h` : '—'],['MOST CONSISTENT',summary.most_consistent_driver,summary.consistency ? `${summary.consistency}/100` : '—'],['DRIVERS ANALYSED',summary.drivers_analysed,'representative laps'],['TEAMS ANALYSED',summary.teams_analysed,summary.best_team || '—']]; $('intelKpis').innerHTML = items.map(x => `<article class="intel-kpi"><small>${x[0]}</small><strong>${x[1]}</strong><span>${x[2]}</span></article>`).join(''); }
    function render(data) {
        kpis(data.summary); $('intelLeaderboard').innerHTML = data.drivers.map(d => `<tr><td>${d.rank}</td><td><b>${d.code}</b><small>${d.name} · #${d.number}</small></td><td>${d.team}</td><td>${d.max_speed ? d.max_speed+' km/h' : '—'}</td><td>${d.avg_speed ? d.avg_speed+' km/h' : '—'}</td><td class="intel-score">${d.consistency ?? '—'}</td></tr>`).join('');
        $('intelSectors').innerHTML = data.sectors.map(s => `<div class="intel-card-row"><div><small>${s.sector}</small><strong>${s.driver}</strong></div><span>${pace(s.time)}</span></div>`).join('');
        $('intelTeams').innerHTML = data.teams.map(t => `<div class="intel-card-row"><div><strong>${t.team}</strong><small>${t.best_driver} · ${t.drivers} drivers</small></div><span>${pace(t.average_pace)}</span></div>`).join('');
        $('intelDrivers').innerHTML = data.drivers.map(d => `<label class="intel-driver"><input type="checkbox" value="${d.code}"><span><b>${d.code} — ${d.name}</b><small>${d.team} · #${d.number}</small></span></label>`).join('');
        $('intelDrivers').querySelectorAll('input').forEach(input => input.addEventListener('change', () => { $('intelCompare').disabled = $('intelDrivers').querySelectorAll(':checked').length < 2; if (input.checked) analysis(input.value); }));
    }
    async function load() {
        status('Loading FastF1 timing, lap and telemetry data… this can take a moment on the first request.', true); $('intelDashboard').hidden = true;
        try { const data = await fetchJson('/api/session-overview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())}); state.drivers=data.drivers; render(data); $('intelMeta').textContent = `${state.event.name} · ${$('intelType').selectedOptions[0].text}`; $('intelSessionLabel').textContent = `${$('intelYear').value} · ${state.event.name.toUpperCase()}`; $('intelDashboard').hidden=false; status('Session intelligence loaded. Choose drivers for a focused comparison.'); } catch(error) { status(`Could not load this session: ${error.message}`); }
    }
    async function compare() { const drivers=[...$('intelDrivers').querySelectorAll(':checked')].map(i=>i.value); status('Comparing selected drivers…',true); try { const data=await fetchJson('/api/compare-drivers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload(),drivers})}); $('intelComparison').innerHTML=`<div class="intel-table"><table><thead><tr><th>DRIVER</th><th>TOP SPEED</th><th>AVG SPEED</th><th>AVG PACE</th><th>FASTEST LAP</th></tr></thead><tbody>${drivers.map(d=>`<tr><td>${d}</td><td>${data.speed_comparison[d]?.max_speed ?? '—'} km/h</td><td>${data.speed_comparison[d]?.avg_speed ?? '—'} km/h</td><td>${data.race_pace[d]?.avg_pace ?? '—'}s</td><td>${data.race_pace[d]?.fastest_lap ?? '—'}s</td></tr>`).join('')}</tbody></table></div><div class="intel-plots"><figure><img src="/plots/${data.plots.comparison}?t=${Date.now()}" alt="Driver comparison telemetry plot"></figure></div>`; status('Comparison ready.'); }catch(error){status(error.message)} }
    async function analysis(driver) { $('intelAnalysis').innerHTML='Loading fastest-lap telemetry…'; try { const data=await fetchJson('/api/driver-analysis',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload(),driver})}); $('intelAnalysis').innerHTML=`<div class="intel-metrics">${[['MAX SPEED',data.stats.max_speed+' km/h'],['AVG SPEED',data.stats.avg_speed+' km/h'],['AVG THROTTLE',data.stats.avg_throttle+'%'],['MAX RPM',data.stats.max_rpm]].map(m=>`<div class="intel-metric"><small>${m[0]}</small><b>${m[1]}</b></div>`).join('')}</div><div class="intel-plots"><figure><img src="/plots/${data.plots.speed_graph}?t=${Date.now()}" alt="Speed graph"></figure><figure><img src="/plots/${data.plots.speed_heatmap}?t=${Date.now()}" alt="Speed heatmap"></figure><figure><img src="/plots/${data.plots.track_map}?t=${Date.now()}" alt="Track map"></figure></div>`; }catch(error){$('intelAnalysis').textContent=error.message} }
    document.addEventListener('DOMContentLoaded',()=>{ years(); $('intelYear').addEventListener('change',events); $('intelEvent').addEventListener('change',sessionTypes); $('intelLoad').addEventListener('click',load); $('intelCompare').addEventListener('click',compare); });
})();
