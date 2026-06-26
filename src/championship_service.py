"""Result-backed season standings.

FastF1 is intentionally queried race-by-race and only for races that have
actually happened.  This avoids presenting schedule entries as results and
makes an empty/incomplete season an explicit data condition.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from datetime import date

import pandas as pd

from session_loader import get_events, load_session

# Used only when a timing provider did not expose its official Points column.
# The FastF1 result remains the primary source for positions, teams and status.
RACE_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}


def _value(row, name, default=None):
    value = row.get(name, default)
    return default if pd.isna(value) else value


def _position(row):
    value = _value(row, "Position", _value(row, "ClassifiedPosition"))
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _result_rows(session):
    results = session.results
    if results is None or results.empty:
        return []
    fastest_code = None
    try:
        valid_laps = session.laps.dropna(subset=["LapTime"])
        if not valid_laps.empty:
            fastest_code = str(valid_laps.loc[valid_laps["LapTime"].idxmin(), "Driver"])
    except Exception:
        pass
    output = []
    for _, row in results.iterrows():
        position = _position(row)
        code = str(_value(row, "Abbreviation", _value(row, "DriverNumber", "Unknown")))
        name = str(_value(row, "FullName", code))
        team = str(_value(row, "TeamName", "Unknown team"))
        points = _value(row, "Points", None)
        grid = _value(row, "GridPosition", None)
        try:
            grid = int(float(grid)) if int(float(grid)) > 0 else None
        except (TypeError, ValueError):
            grid = None
        laps = session.laps.pick_drivers(code)
        lap_times = laps["LapTime"].dt.total_seconds().dropna()
        if not lap_times.empty:
            median = lap_times.median()
            representative = lap_times[(lap_times > median * .8) & (lap_times < median * 1.25)]
            race_pace = float(representative.mean()) if not representative.empty else None
        else:
            race_pace = None
        try:
            points = float(points) if points is not None else float(RACE_POINTS.get(position, 0))
        except (TypeError, ValueError):
            points = float(RACE_POINTS.get(position, 0))
        output.append({"code": code, "name": name, "team": team, "position": position, "grid": grid, "race_pace": race_pace, "points": points,
                       "fastest_lap": code == fastest_code})
    return output


@lru_cache(maxsize=6)
def season_results(year: int):
    """Load completed race results available from FastF1 for one season."""
    completed = []
    for event in get_events(year):
        event_date = event.get("date")
        if event_date and event_date > date.today().isoformat():
            continue
        try:
            session = load_session(year, event["name"], "R", False)
            rows = _result_rows(session)
            if rows:
                winner = next((row for row in rows if row["position"] == 1), None)
                pole = next((row for row in rows if row["grid"] == 1), None)
                fastest = next((row for row in rows if row["fastest_lap"]), None)
                completed.append({"round": event["round"], "name": event["name"], "location": event.get("location"), "date": event.get("date"), "winner": winner["name"] if winner else None, "pole_position": pole["name"] if pole else None, "fastest_lap": fastest["name"] if fastest else None, "results": rows})
        except Exception:
            # A future race or temporarily unavailable timing data is not a
            # zero-point result, so it is deliberately omitted.
            continue
    return completed


@lru_cache(maxsize=6)
def driver_standings(year: int):
    totals = defaultdict(lambda: {"name": "", "team": "", "points": 0.0, "wins": 0, "podiums": 0, "fastest_laps": 0})
    races = season_results(year)
    for race in races:
        for row in race["results"]:
            item = totals[row["code"]]
            item.update(name=row["name"], team=row["team"])
            item["points"] += row["points"]
            item["wins"] += row["position"] == 1
            item["podiums"] += row["position"] is not None and row["position"] <= 3
            item["fastest_laps"] += row["fastest_lap"]
    standings = [{"code": code, **values, "points": round(values["points"], 1)} for code, values in totals.items()]
    standings.sort(key=lambda row: (-row["points"], -row["wins"], -row["podiums"], row["name"]))
    for position, row in enumerate(standings, 1): row["position"] = position
    return {"year": year, "races_completed": len(races), "drivers": standings}
