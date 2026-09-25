"""Deterministic summaries shared across supported sports."""

from __future__ import annotations

from typing import Any, Mapping

from .running import format_pace
from .swimming import analyze_pool_swim


COMMON_FIELDS = (
    "duration_seconds",
    "moving_time_seconds",
    "distance_meters",
    "calories",
    "average_heart_rate",
    "max_heart_rate",
    "elevation_gain_meters",
    "training_effect_aerobic",
    "training_effect_anaerobic",
    "load_value",
    "recovery_seconds",
)


def summarize_activity(activity: Mapping[str, Any]) -> dict[str, Any]:
    """Return reproducible common metrics and sport-specific derived units."""
    summary: dict[str, Any] = {"sport": activity["sport"]}
    for field in COMMON_FIELDS:
        if activity.get(field) is not None:
            summary[field] = activity[field]

    if activity["sport"] == "run" and activity.get("distance_meters"):
        summary["pace"] = format_pace(
            float(activity["duration_seconds"]), float(activity["distance_meters"])
        )
    elif activity["sport"] == "cycling" and activity.get("distance_meters"):
        summary["speed_kmh"] = (
            float(activity["distance_meters"])
            / float(activity["duration_seconds"])
            * 3.6
        )
    elif activity["sport"] == "pool_swim":
        summary.update(analyze_pool_swim(activity))
    return summary