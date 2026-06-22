const dom = (id) => document.getElementById(id);
const state = { event: null };

async function request(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || "Request failed");
    return data;
}

function setStatus(message, loading = false) {
    const status = dom("intelStatus");
    status.textContent = message;
    status.classList.toggle("loading", loading);
}

function selectedSession() {
    return {
        year: Number(dom("intelYear").value),
        race: state.event.name,
        session: dom("intelType").value,
    };
}

function option(value, text) {
    return `<option value="${value}">${text}</option>`;
}

function pace(value) {
    return value == null ? "—" : `${value.toFixed(3)}s`;
}

async function loadYears() {
    try {
        const years = await request("/api/years");
        dom("intelYear").innerHTML = `<option value="">Season</option>${years
            .reverse()
            .map((year) => option(year, year))
            .join("")}`;
        // A completed season has data available immediately; 2026 remains selectable.
        dom("intelYear").value = years.includes(2025) ? 2025 : years[0];
        await loadEvents();
    } catch (error) {
        setStatus(error.message);
    }
}

async function loadEvents() {
    const year = dom("intelYear").value;
    dom("intelEvent").disabled = !year;
    dom("intelType").disabled = true;
    dom("intelLoad").disabled = true;
    if (!year) return;

    try {
        setStatus("Loading season calendar…", true);
        const events = await request(`/api/events/${year}`);
        dom("intelEvent").innerHTML = `<option value="">Grand Prix</option>${events
            .map((event) => option(event.round, `${event.round}. ${event.name}`))
            .join("")}`;
        setStatus("Choose a Grand Prix and session to load the dashboard.");
    } catch (error) {
        setStatus(`Calendar unavailable: ${error.message}`);
    }
}

async function loadSessionTypes() {
    const year = dom("intelYear").value;
    const round = dom("intelEvent").value;
    dom("intelType").disabled = !round;
    dom("intelLoad").disabled = true;
    if (!round) return;

    try {
        const data = await request(`/api/sessions/${year}/${round}`);
        state.event = data.event;
        dom("intelType").innerHTML = data.sessions
            .map((session) => option(session.code, session.name))
            .join("");
        dom("intelLoad").disabled = false;
        setStatus("Ready to load session intelligence.");
    } catch (error) {
        setStatus(error.message);
    }
}

function renderKpis(summary) {
    const cards = [
        ["Fastest driver", summary.fastest_driver, pace(summary.fastest_lap)],
        ["Highest speed", summary.highest_speed_driver, summary.highest_speed ? `${summary.highest_speed} km/h` : "—"],
        ["Most consistent", summary.most_consistent_driver, summary.consistency ? `${summary.consistency}/100` : "—"],
        ["Drivers analysed", summary.drivers_analysed, "representative laps"],
        ["Teams analysed", summary.teams_analysed, summary.best_team || "—"],
    ];
    dom("intelKpis").innerHTML = cards.map(([label, value, detail]) =>
        `<article class="intel-kpi"><small>${label}</small><strong>${value}</strong><span>${detail}</span></article>`
    ).join("");
}

function renderOverview(data) {
    renderKpis(data.summary);
    dom("intelLeaderboard").innerHTML = data.drivers.map((driver) => `
        <tr><td>${driver.rank}</td><td><b>${driver.code}</b><small>${driver.name} · #${driver.number}</small></td>
        <td>${driver.team}</td><td>${driver.max_speed ?? "—"} km/h</td>
        <td>${driver.avg_speed ?? "—"}${driver.avg_speed ? " km/h" : ""}</td>
        <td class="intel-score">${driver.consistency ?? "—"}</td></tr>`).join("");
    dom("intelSectors").innerHTML = data.sectors.map((sector) =>
        `<div class="intel-card-row"><div><small>${sector.sector}</small><strong>${sector.driver}</strong></div><span>${pace(sector.time)}</span></div>`
    ).join("");
    dom("intelTeams").innerHTML = data.teams.map((team) =>
        `<div class="intel-card-row"><div><strong>${team.team}</strong><small>${team.best_driver} · ${team.drivers} drivers</small></div><span>${pace(team.average_pace)}</span></div>`
    ).join("");
    dom("intelDrivers").innerHTML = data.drivers.map((driver) => `
        <label class="intel-driver"><input type="checkbox" value="${driver.code}"><span><b>${driver.code} — ${driver.name}</b>
        <small>${driver.team} · #${driver.number}</small></span></label>`).join("");
    dom("intelDrivers").querySelectorAll("input").forEach((input) => {
        input.addEventListener("change", () => {
            const count = dom("intelDrivers").querySelectorAll(":checked").length;
            dom("intelCompare").disabled = count < 2;
            if (input.checked) loadDriverAnalysis(input.value);
        });
    });
}

async function loadDashboard() {
    setStatus("Loading timing and lap data…", true);
    dom("intelDashboard").hidden = true;
    try {
        const data = await request("/api/session-overview", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(selectedSession()),
        });
        renderOverview(data);
        dom("intelMeta").textContent = `${state.event.name} · ${dom("intelType").selectedOptions[0].text}`;
        dom("intelSessionLabel").textContent = `${dom("intelYear").value} · ${state.event.name.toUpperCase()}`;
        dom("intelDashboard").hidden = false;
        setStatus("Session intelligence loaded.");
    } catch (error) {
        setStatus(`Dashboard unavailable: ${error.message}. Try a completed session or check the FastF1 cache.`);
    }
}

async function loadDriverAnalysis(driver) {
    dom("intelAnalysis").textContent = "Loading fastest-lap telemetry…";
    try {
        const data = await request("/api/driver-analysis", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...selectedSession(), driver }),
        });
        const stats = [["Max speed", `${data.stats.max_speed} km/h`], ["Average speed", `${data.stats.avg_speed} km/h`], ["Average throttle", `${data.stats.avg_throttle}%`], ["Max RPM", data.stats.max_rpm]];
        dom("intelAnalysis").innerHTML = `<div class="intel-metrics">${stats.map(([label, value]) => `<div class="intel-metric"><small>${label}</small><b>${value}</b></div>`).join("")}</div><div class="intel-plots">${Object.values(data.plots).map((plot) => `<figure><img src="/plots/${plot}?t=${Date.now()}" alt="${plot}"></figure>`).join("")}</div>`;
    } catch (error) {
        dom("intelAnalysis").textContent = error.message;
    }
}

async function compareSelectedDrivers() {
    const drivers = [...dom("intelDrivers").querySelectorAll(":checked")].map((item) => item.value);
    if (drivers.length < 2) return;
    setStatus("Comparing selected drivers…", true);
    try {
        const data = await request("/api/compare-drivers", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...selectedSession(), drivers }),
        });
        dom("intelComparison").innerHTML = `<div class="intel-table"><table><thead><tr><th>Driver</th><th>Top speed</th><th>Average speed</th><th>Average pace</th><th>Fastest lap</th></tr></thead><tbody>${drivers.map((driver) => `<tr><td>${driver}</td><td>${data.speed_comparison[driver]?.max_speed ?? "—"} km/h</td><td>${data.speed_comparison[driver]?.avg_speed ?? "—"} km/h</td><td>${data.race_pace[driver]?.avg_pace ?? "—"}s</td><td>${data.race_pace[driver]?.fastest_lap ?? "—"}s</td></tr>`).join("")}</tbody></table></div><div class="intel-plots"><figure><img src="/plots/${data.plots.comparison}?t=${Date.now()}" alt="Driver comparison"></figure></div>`;
        setStatus("Comparison ready.");
    } catch (error) {
        setStatus(error.message);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadYears();
    dom("intelYear").addEventListener("change", loadEvents);
    dom("intelEvent").addEventListener("change", loadSessionTypes);
    dom("intelLoad").addEventListener("click", loadDashboard);
    dom("intelCompare").addEventListener("click", compareSelectedDrivers);
});
