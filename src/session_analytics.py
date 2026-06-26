"""Session-level metrics used by the F1 MapFeed intelligence dashboard."""

import math
from numbers import Real

import pandas as pd


def json_safe(value):
    """Convert non-finite numeric values into JSON-compatible ``None`` values."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, Real) and not isinstance(value, bool):
        return float(value) if not math.isfinite(value) else value
    return value


def _seconds(value):
    """Return a FastF1 timedelta as seconds, or None when unavailable."""
    if pd.isna(value):
        return None
    return float(value.total_seconds())


def _valid_laps(laps):
    times = laps["LapTime"].dt.total_seconds().dropna()
    if times.empty:
        return times
    # Pit laps and red-flag laps are not representative of race pace.
    median = times.median()
    return times[(times > median * 0.80) & (times < median * 1.25)]


def consistency_score(lap_times):
    """0-100 score: lower lap-time variation produces a higher score."""
    if len(lap_times) < 2:
        return None
    mean = float(lap_times.mean())
    if not mean:
        return None
    coefficient_of_variation = float(lap_times.std(ddof=0)) / mean
    return round(max(0, min(100, 100 - coefficient_of_variation * 1000)), 1)


def driver_directory(session):
    drivers = []
    for driver_number in session.drivers:
        info = session.get_driver(driver_number)
        drivers.append({
            "code": str(info.get("Abbreviation", driver_number)),
            "name": str(info.get("FullName", "Unknown driver")),
            "team": str(info.get("TeamName", "Unknown team")),
            "team_color": str(info.get("TeamColor", "")) or None,
            "number": str(info.get("DriverNumber", driver_number)),
        })
    return sorted(drivers, key=lambda driver: driver["code"])


def build_session_overview(session):
    """Build leaderboard, team rollup, sector leaders and top-line session KPIs."""
    driver_info = {item["code"]: item for item in driver_directory(session)}
    rows = []

    try:
        circuit_length_km = float(
            session.get_circuit_info().corners.iloc[-1]["Distance"]
        ) / 1000
        if not math.isfinite(circuit_length_km) or circuit_length_km <= 0:
            circuit_length_km = None
    except Exception:
        circuit_length_km = None

    for code, info in driver_info.items():
        laps = session.laps.pick_drivers(code)
        valid_laps = _valid_laps(laps)
        if valid_laps.empty:
            continue
        fastest = laps.pick_fastest()
        # Session lap data is already loaded. Avoid extracting full car telemetry for
        # every driver here: it turns a dashboard overview into 20 heavy downloads.
        speed_trap = laps["SpeedST"].dropna() if "SpeedST" in laps else pd.Series(dtype=float)
        max_speed = float(speed_trap.max()) if not speed_trap.empty else None
        fastest_seconds = float(valid_laps.min())
        avg_speed = (circuit_length_km / fastest_seconds * 3600) if circuit_length_km else None
        rows.append({
            **info,
            "max_speed": round(max_speed, 1) if max_speed is not None else None,
            "avg_speed": round(avg_speed, 1) if avg_speed is not None else None,
            "average_pace": round(float(valid_laps.mean()), 3),
            "fastest_lap": round(fastest_seconds, 3),
            "consistency": consistency_score(valid_laps),
            "lap_count": int(len(valid_laps)),
            "sector_1": _seconds(fastest.Sector1Time),
            "sector_2": _seconds(fastest.Sector2Time),
            "sector_3": _seconds(fastest.Sector3Time),
        })

    if not rows:
        raise ValueError("No representative timed laps were available for this session.")

    rows.sort(key=lambda row: row["fastest_lap"])
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    teams = []
    for team, members in pd.DataFrame(rows).groupby("team"):
        members = members.dropna(subset=["average_pace"])
        if members.empty:
            continue
        best = min(members.to_dict("records"), key=lambda row: row["fastest_lap"])
        teams.append({
            "team": team,
            "average_pace": round(float(members["average_pace"].mean()), 3),
            "average_speed": round(float(members["avg_speed"].dropna().mean()), 1) if members["avg_speed"].notna().any() else None,
            "consistency": round(float(members["consistency"].dropna().mean()), 1) if members["consistency"].notna().any() else None,
            "best_driver": best["code"],
            "team_color": best.get("team_color"),
            "drivers": int(len(members)),
        })
    teams.sort(key=lambda row: row["average_pace"])

    sectors = []
    for key, label in (("sector_1", "Sector 1"), ("sector_2", "Sector 2"), ("sector_3", "Sector 3")):
        candidates = [row for row in rows if row[key] is not None]
        if candidates:
            winner = min(candidates, key=lambda row: row[key])
            sectors.append({"sector": label, "driver": winner["code"], "team": winner["team"], "time": round(winner[key], 3)})

    fastest = rows[0]
    speed_rows = [row for row in rows if row["max_speed"] is not None]
    top_speed = max(speed_rows, key=lambda row: row["max_speed"]) if speed_rows else fastest
    consistency_rows = [row for row in rows if row["consistency"] is not None]
    most_consistent = max(consistency_rows, key=lambda row: row["consistency"]) if consistency_rows else fastest
    best_team = teams[0] if teams else None
    winner = None
    try:
        result_rows = session.results
        first = result_rows[result_rows["Position"].astype(str) == "1"]
        if not first.empty:
            winner_value = first.iloc[0].get("FullName")
            if pd.isna(winner_value):
                winner_value = first.iloc[0].get("Abbreviation")
            winner = str(winner_value)
    except Exception:
        pass
    return json_safe({
        "drivers": rows,
        "teams": teams,
        "sectors": sectors,
        "summary": {
            "fastest_driver": fastest["code"],
            "fastest_lap": fastest["fastest_lap"],
            "highest_speed_driver": top_speed["code"],
            "highest_speed": top_speed["max_speed"],
            "most_consistent_driver": most_consistent["code"],
            "consistency": most_consistent["consistency"],
            "best_team": best_team["team"] if best_team else None,
            "drivers_analysed": len(rows),
            "teams_analysed": len(teams),
            "winner": winner,
        },
    })
