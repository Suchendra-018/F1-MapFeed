import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
import os

# Get project root for saving plots
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOTS_DIR = os.path.join(PROJECT_ROOT, 'plots')


def get_multiple_drivers_telemetry(session, driver_codes):
    """
    Extract telemetry for multiple drivers' fastest laps
    Returns dict of driver_code -> telemetry DataFrame
    """
    from telemetry import get_fastest_lap_telemetry
    
    telemetry_data = {}
    for driver_code in driver_codes:
        try:
            telemetry = get_fastest_lap_telemetry(session, driver_code)
            telemetry_data[driver_code] = telemetry
        except Exception as e:
            print(f"Could not load telemetry for {driver_code}: {e}")
    
    return telemetry_data


def compare_driver_speeds(telemetry_dict):
    """
    Compare speed profiles of multiple drivers
    Returns stats for each driver
    """
    comparison = {}
    
    for driver_code, telemetry in telemetry_dict.items():
        comparison[driver_code] = {
            "max_speed": telemetry["Speed"].max(),
            "avg_speed": telemetry["Speed"].mean(),
            "min_speed": telemetry["Speed"].min(),
            "throttle_avg": telemetry["Throttle"].mean(),
            "speed_std": telemetry["Speed"].std()  # Consistency
        }
    
    return comparison


def plot_driver_comparison(telemetry_dict, output_file=None):
    """
    Plot speed profiles for multiple drivers on same graph
    Helps visualize driving style differences
    """
    if output_file is None:
        output_file = os.path.join(PLOTS_DIR, "driver_comparison.png")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Speed vs Distance
    for driver_code, telemetry in telemetry_dict.items():
        ax1.plot(
            telemetry["Distance"],
            telemetry["Speed"],
            label=driver_code,
            linewidth=2,
            alpha=0.7
        )
    
    ax1.set_xlabel("Distance (m)", fontsize=12)
    ax1.set_ylabel("Speed (km/h)", fontsize=12)
    ax1.set_title("Driver Speed Comparison", fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Throttle vs Distance
    for driver_code, telemetry in telemetry_dict.items():
        ax2.plot(
            telemetry["Distance"],
            telemetry["Throttle"],
            label=driver_code,
            linewidth=2,
            alpha=0.7
        )
    
    ax2.set_xlabel("Distance (m)", fontsize=12)
    ax2.set_ylabel("Throttle (%)", fontsize=12)
    ax2.set_title("Driver Throttle Comparison", fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(output_file, dpi=150)
    plt.close()


def get_race_pace_analysis(session, driver_codes):
    """
    Analyze race pace progression - lap times throughout the race
    Shows if driver is managing tyres, pushing hard, or falling back
    """
    pace_data = {}
    
    for driver_code in driver_codes:
        try:
            driver_laps = session.laps.pick_drivers(driver_code)
            # Get lap times (filter out slow outliers like pit stops)
            lap_times = driver_laps["LapTime"].dt.total_seconds()
            if lap_times.empty:
                continue
            median = lap_times.median()
            valid_laps = lap_times[(lap_times > median * .8) & (lap_times < median * 1.25)]
            
            pace_data[driver_code] = {
                "avg_pace": valid_laps.mean(),
                "fastest_lap": valid_laps.min(),
                "slowest_lap": valid_laps.max(),
                "consistency": valid_laps.std(),
                "total_laps": len(valid_laps)
            }
        except Exception as e:
            print(f"Could not analyze pace for {driver_code}: {e}")
    
    return pace_data


def build_comparison(session, driver_codes):
    """Two-driver, session-backed comparison with an interactive speed trace."""
    telemetry = get_multiple_drivers_telemetry(session, driver_codes[:2])
    pace = get_race_pace_analysis(session, driver_codes[:2])
    rows, traces = [], []
    for code, data in telemetry.items():
        fastest = session.laps.pick_drivers(code).pick_fastest()
        sector_values = [getattr(fastest, f"Sector{i}Time", None) for i in range(1, 4)]
        sector_seconds = [float(value.total_seconds()) if pd.notna(value) else None for value in sector_values]
        driver_pace = pace.get(code, {})
        brake = data["Brake"] if "Brake" in data else pd.Series(dtype=float)
        rows.append({"driver": code, "top_speed": round(float(data["Speed"].max()), 1),
                     "average_speed": round(float(data["Speed"].mean()), 1),
                     "fastest_lap": round(float(driver_pace.get("fastest_lap")), 3) if driver_pace.get("fastest_lap") else None,
                     "race_pace": round(float(driver_pace.get("avg_pace")), 3) if driver_pace.get("avg_pace") else None,
                     "consistency": round(float(driver_pace.get("consistency")), 3) if driver_pace.get("consistency") else None,
                     "sectors": sector_seconds, "throttle_usage": round(float(data["Throttle"].mean()), 1),
                     "brake_usage": round(float(brake.mean()), 1) if not brake.empty else None})
        traces.append({"x": data["Distance"].tolist(), "y": data["Speed"].tolist(), "type": "scatter", "mode": "lines", "name": code})
    if len(rows) < 2:
        raise ValueError("Telemetry is not available for at least two selected drivers.")
    # Lower lap time and variation are better. Scores are relative only to the
    # selected pair, preventing a synthetic global ranking.
    for metric, higher_better in (("top_speed", True), ("average_speed", True), ("fastest_lap", False), ("race_pace", False), ("consistency", False), ("throttle_usage", True)):
        values = [row[metric] for row in rows]
        if None in values or len(set(values)) == 1:
            continue
        winner = values.index(max(values) if higher_better else min(values))
        rows[winner].setdefault("_wins", 0); rows[winner]["_wins"] += 1
    for row in rows:
        row["score"] = round(50 + 50 * row.pop("_wins", 0) / 6)
    figure = {"data": traces, "layout": {"template": "plotly_dark", "title": "Speed trace", "xaxis": {"title": "Distance (m)"}, "yaxis": {"title": "Speed (km/h)"}, "margin": {"l": 35, "r": 20, "t": 50, "b": 35}, "legend": {"title": {"text": "Driver"}}}}
    rows.sort(key=lambda row: row["score"], reverse=True)
    return {"drivers": rows, "winner": rows[0]["driver"], "chart": figure}
