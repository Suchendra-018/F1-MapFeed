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
            valid_laps = lap_times[lap_times < 100]  # Assuming lap < 100 seconds
            
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
