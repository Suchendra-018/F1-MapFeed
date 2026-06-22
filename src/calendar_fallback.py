"""Small offline calendar fallback for the currently selected season.

FastF1 remains the source of truth. This only keeps the selector usable when
the schedule provider cannot be reached (for example, when working offline).
"""

OFFLINE_EVENTS = {
    2026: [
        "Australian Grand Prix", "Chinese Grand Prix", "Japanese Grand Prix",
        "Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Miami Grand Prix",
        "Canadian Grand Prix", "Monaco Grand Prix", "Spanish Grand Prix",
        "Austrian Grand Prix", "British Grand Prix", "Belgian Grand Prix",
        "Hungarian Grand Prix", "Dutch Grand Prix", "Italian Grand Prix",
        "Azerbaijan Grand Prix", "Singapore Grand Prix", "United States Grand Prix",
        "Mexico City Grand Prix", "Sao Paulo Grand Prix", "Las Vegas Grand Prix",
        "Qatar Grand Prix", "Abu Dhabi Grand Prix",
    ]
}


def offline_events(year):
    return [
        {"round": number, "name": name, "location": "Schedule data unavailable offline"}
        for number, name in enumerate(OFFLINE_EVENTS.get(year, []), start=1)
    ]
