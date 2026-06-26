from functools import lru_cache
import os

import fastf1

from calendar_fallback import offline_events

# Avoid a known-invalid local proxy while preserving real user proxy settings.
for proxy_name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    if "127.0.0.1:9" in os.environ.get(proxy_name, ""):
        os.environ.pop(proxy_name, None)

# Create cache directory if it doesn't exist
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

SUPPORTED_YEARS = (2024, 2025)


@lru_cache(maxsize=1)
def get_available_years():
    """The two stable, supported seasons for the Race Intelligence app."""
    return list(SUPPORTED_YEARS)


@lru_cache(maxsize=16)
def load_session(year, race, session_type, telemetry=False):
    """Load a cached FastF1 session, enabling telemetry only when requested."""
    if year not in SUPPORTED_YEARS:
        raise ValueError("Only the 2024 and 2025 seasons are supported.")
    if session_type not in {"Q", "R"}:
        raise ValueError("Only Qualifying and Race sessions are supported.")

    session = fastf1.get_session(year, race, session_type)

    session.load(telemetry=telemetry, weather=False, messages=False)

    return session


@lru_cache(maxsize=8)
def get_events(year):
    """Return the official schedule, with an offline fallback when available."""
    if year not in SUPPORTED_YEARS:
        raise ValueError("Only the 2024 and 2025 seasons are supported.")
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except ValueError:
        fallback = offline_events(year)
        if fallback:
            return fallback
        raise
    events = []
    for _, event in schedule.iterrows():
        if int(event["RoundNumber"]) <= 0:
            continue
        events.append(
            {
                "round": int(event["RoundNumber"]),
                "name": str(event["EventName"]),
                "location": str(event["Location"]),
                "date": event["EventDate"].date().isoformat() if hasattr(event["EventDate"], "date") else None,
            }
        )
    return events
