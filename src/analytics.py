def get_driver_stats(telemetry):
    """Calculate basic telemetry statistics for one fastest lap."""
    stats = {
        "max_speed": telemetry["Speed"].max(),
        "avg_speed": telemetry["Speed"].mean(),
        "avg_throttle": telemetry["Throttle"].mean(),
        "max_rpm": telemetry["RPM"].max()
    }

    return stats


def get_sector_analysis(lap):
    """Return the sector times FastF1 recorded for a lap."""
    sectors = {
        "Sector 1": {"time": lap.Sector1Time, "speed": None},
        "Sector 2": {"time": lap.Sector2Time, "speed": None},
        "Sector 3": {"time": lap.Sector3Time, "speed": None},
    }
    
    return sectors


def get_throttle_brake_zones(telemetry):
    """Summarise full-throttle and braking samples for a telemetry lap."""
    high_throttle = (telemetry["Throttle"] > 90).sum()
    high_brake = (telemetry["Brake"] > 90).sum() if "Brake" in telemetry.columns else 0
    
    throttle_zones = {
        "full_throttle_points": high_throttle,
        "full_brake_points": high_brake,
        "throttle_percentage": (high_throttle / len(telemetry)) * 100
    }
    
    return throttle_zones
