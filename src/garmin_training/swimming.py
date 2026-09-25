"""Reduced, pool-only swimming analysis."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def analyze_pool_swim(activity: Mapping[str, Any]) -> dict[str, Any]:
    if activity.get("sport") != "pool_swim":
        raise ValueError("pool analysis only accepts pool_swim activities")
    distance = _non_negative(activity.get("distance_meters"), "distance_meters")
    duration = _non_negative(activity.get("duration_seconds"), "duration_seconds")
    result: dict[str, Any] = {
        "distance_meters": distance,
        "duration_seconds": duration,
        "moving_time_seconds": activity.get("moving_time_seconds"),
        "pace_seconds_per_100m": duration / (distance / 100) if distance else None,
    }
    for field in (
        "pool_length_meters",
        "lengths",
        "average_stroke_count",
        "swolf",
        "rest_seconds",
        "stroke_type",
        "average_heart_rate",
    ):
        result[field] = activity.get(field)
    return result


def aggregate_weekly_pool(activities: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    pool_activities = [activity for activity in activities if activity.get("sport") == "pool_swim"]
    return {
        "distance_meters": sum(float(activity.get("distance_meters") or 0) for activity in pool_activities),
        "duration_seconds": sum(float(activity.get("duration_seconds") or 0) for activity in pool_activities),
    }


def _non_negative(value: Any, field: str) -> float:
    if value is None or float(value) < 0:
        raise ValueError(f"{field} must be non-negative")
    return float(value)