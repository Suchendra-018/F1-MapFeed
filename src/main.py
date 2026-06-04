from session_loader import load_session
from telemetry import (
    get_fastest_lap_telemetry,
    get_fastest_lap
)

from analytics import (
    get_driver_stats,
    get_sector_analysis,
    get_throttle_brake_zones
)
from plotter import plot_speed_graph
from trackmap import (
    create_track_map,
    create_speed_heatmap
)
from comparison import (
    get_multiple_drivers_telemetry,
    compare_driver_speeds,
    plot_driver_comparison,
    get_race_pace_analysis
)


session = load_session(
    2025,
    "Monaco Grand Prix",
    "R"
)

telemetry = get_fastest_lap_telemetry(
    session,
    "VER"
)

lap = get_fastest_lap(
    session,
    "VER"
)

stats = get_driver_stats(
    telemetry
)

print("\nDriver Statistics\n")

for key, value in stats.items():
    print(
        key,
        ":",
        round(value, 2)
    )

# Get sector analysis
sectors = get_sector_analysis(lap)
print("\n\nSector Times\n")
for sector, data in sectors.items():
    sector_time = data["time"]
    if sector_time:
        print(f"{sector}: {sector_time}")

# Get throttle and brake analysis
throttle_brake = get_throttle_brake_zones(telemetry)
print("\n\nThrottle & Brake Analysis\n")
print(f"Full Throttle Points: {throttle_brake['full_throttle_points']}")
print(f"Full Brake Points: {throttle_brake['full_brake_points']}")
print(f"Throttle % of Lap: {throttle_brake['throttle_percentage']:.1f}%")

# Generate all visualizations
plot_speed_graph(
    telemetry
)

create_track_map(
    lap
)

create_speed_heatmap(
    lap,
    telemetry
)

print("\n✓ Speed Graph generated")
print("✓ Circuit Layout generated")
print("✓ Speed Heatmap generated")


# ========== DRIVER COMPARISON ==========
print("\n\n" + "="*50)
print("MULTI-DRIVER ANALYSIS")
print("="*50)

# Compare VER vs other top drivers
comparison_drivers = ["VER", "LEC", "SAI"]  # Verstappen, Leclerc, Sainz
telemetry_dict = get_multiple_drivers_telemetry(session, comparison_drivers)

if len(telemetry_dict) > 1:
    # Speed comparison stats
    speed_comparison = compare_driver_speeds(telemetry_dict)
    print("\n\nSpeed Profile Comparison\n")
    print(f"{'Driver':<10} {'Max Speed':<12} {'Avg Speed':<12} {'Consistency':<12}")
    print("-" * 46)
    for driver, stats in speed_comparison.items():
        print(
            f"{driver:<10} "
            f"{stats['max_speed']:<12.1f} "
            f"{stats['avg_speed']:<12.1f} "
            f"{stats['speed_std']:<12.2f}"
        )
    
    # Generate comparison plots
    plot_driver_comparison(telemetry_dict)
    print("\n✓ Driver Comparison plot generated")

# Race pace analysis
race_pace = get_race_pace_analysis(session, comparison_drivers)
print("\n\nRace Pace Analysis\n")
print(f"{'Driver':<10} {'Avg Pace':<12} {'Fastest Lap':<12} {'Consistency':<12}")
print("-" * 46)
for driver, stats in race_pace.items():
    print(
        f"{driver:<10} "
        f"{stats['avg_pace']:<12.2f}s "
        f"{stats['fastest_lap']:<12.2f}s "
        f"{stats['consistency']:<12.2f}"
    )