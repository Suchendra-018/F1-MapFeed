from functools import lru_cache
import os

import fastf1

from calendar_fallback import offline_events

# Some local development environments export a dead loopback proxy. FastF1
# inherits these variables through requests, so remove only that known-invalid
# value and leave genuine user-configured proxies untouched.
for proxy_name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    if "127.0.0.1:9" in os.environ.get(proxy_name, ""):
        os.environ.pop(proxy_name, None)

# FastF1 stores downloaded timing and telemetry here, allowing repeat loads to
# use local files instead of requesting the remote timing provider again.
fastf1.Cache.enable_cache("data")


@lru_cache(maxsize=16)
def load_session(year, race, session_type, telemetry=False):
    """Load only the data required for the requested workflow.

    Session dashboards need laps and results, while telemetry is only needed for
    a selected driver's detailed chart. Avoiding telemetry on the dashboard
    request cuts the initial data load substantially.
    """
    session = fastf1.get_session(year, race, session_type)

    session.load(telemetry=telemetry, weather=False, messages=False)

    return session


@lru_cache(maxsize=8)
def get_events(year):
    """Return the full official calendar, with an offline fallback for 2026."""
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
            }
        )
    return events
