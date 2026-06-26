"""Helpers for retrieving a selected driver's fastest-lap data."""


def get_fastest_lap_telemetry(session, driver_code):
    """Return car telemetry, including distance, for a driver's fastest lap."""
    return get_fastest_lap(session, driver_code).get_telemetry().add_distance()


def get_fastest_lap(session, driver_code):
    """Return a driver's fastest valid lap or raise a clear data error."""
    fastest_lap = session.laps.pick_drivers(driver_code).pick_fastest()

    if fastest_lap is None:
        raise ValueError(f"No valid timed lap is available for {driver_code}.")

    return fastest_lap
