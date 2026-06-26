"""Constructor standings and result-derived performance analytics."""
from collections import defaultdict
from functools import lru_cache

from championship_service import season_results


@lru_cache(maxsize=6)
def constructor_standings(year: int):
    teams = defaultdict(lambda: {"points": 0.0, "wins": 0, "podiums": 0, "finishes": [], "grids": [], "paces": [], "drivers": set(), "reliable": 0, "starts": 0})
    races = season_results(year)
    for race in races:
        for driver in race["results"]:
            team = teams[driver["team"]]
            team["points"] += driver["points"]
            team["wins"] += driver["position"] == 1
            team["podiums"] += driver["position"] is not None and driver["position"] <= 3
            team["starts"] += 1
            team["drivers"].add(driver["name"])
            if driver["grid"] is not None:
                team["grids"].append(driver["grid"])
            if driver["race_pace"] is not None:
                team["paces"].append(driver["race_pace"])
            if driver["position"] is not None:
                team["finishes"].append(driver["position"])
                team["reliable"] += 1
    standings = []
    for team, data in teams.items():
        finish = sum(data["finishes"]) / len(data["finishes"]) if data["finishes"] else None
        standings.append({"team": team, "points": round(data["points"], 1), "wins": data["wins"], "podiums": data["podiums"],
                          "average_finish": round(finish, 2) if finish else None,
                          "average_qualifying_position": round(sum(data["grids"]) / len(data["grids"]), 2) if data["grids"] else None,
                          "average_pace": round(sum(data["paces"]) / len(data["paces"]), 3) if data["paces"] else None,
                          "drivers": sorted(data["drivers"]),
                          "reliability": round(100 * data["reliable"] / data["starts"], 1) if data["starts"] else None})
    standings.sort(key=lambda row: (-row["points"], -row["wins"], -row["podiums"], row["team"]))
    for position, row in enumerate(standings, 1): row["position"] = position
    return {"year": year, "races_completed": len(races), "constructors": standings}
