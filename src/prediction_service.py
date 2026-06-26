"""Conservative, transparent championship projection from completed results."""
import math
from championship_service import driver_standings
from constructor_service import constructor_standings
from session_loader import get_events


def _probabilities(rows):
    if len(rows) < 2:
        return None
    # A transparent strength score, not a fabricated model confidence.
    scores = [max(0.01, row["points"] + row["wins"] * 8 + row["podiums"] * 2) for row in rows]
    total = sum(scores)
    return [{**row, "championship_probability": round(score / total * 100, 1)} for row, score in zip(rows, scores)]


def build_predictions(year: int):
    drivers = driver_standings(year)
    constructors = constructor_standings(year)
    total_rounds = len(get_events(year))
    # A normalised points score is not a championship probability. Keep this
    # deliberately unavailable until a validated result-based model exists.
    return {"available": False, "reason": "Predictions are hidden until a validated result-based model is available.", "races_completed": drivers["races_completed"]}
