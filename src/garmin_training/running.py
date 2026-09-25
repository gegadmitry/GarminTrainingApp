"""Deterministic running pace analysis in canonical seconds per kilometer."""

from __future__ import annotations

from statistics import pstdev
from typing import Any, Mapping, Sequence


def pace_seconds_per_kilometer(duration_seconds: float, distance_meters: float) -> float:
    if duration_seconds < 0:
        raise ValueError("duration must not be negative")
    if distance_meters <= 0:
        raise ValueError("distance must be greater than zero")
    return duration_seconds / (distance_meters / 1000)


def format_pace(duration_seconds: float, distance_meters: float) -> str:
    pace_seconds = round(pace_seconds_per_kilometer(duration_seconds, distance_meters))
    minutes, seconds = divmod(pace_seconds, 60)
    return f"{minutes}:{seconds:02d} min/km"


def analyze_running(
    activity: Mapping[str, Any],
    laps: Sequence[Mapping[str, Any]] = (),
    samples: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    duration = float(activity["duration_seconds"])
    distance = float(activity["distance_meters"])
    result: dict[str, Any] = {
        "average_pace_seconds_per_kilometer": pace_seconds_per_kilometer(duration, distance),
        "average_pace": format_pace(duration, distance),
    }
    for field in ("average_heart_rate", "max_heart_rate", "cadence", "elevation_gain_meters"):
        if activity.get(field) is not None:
            result[field] = activity[field]
    if activity.get("heart_rate_zones") is not None:
        result["heart_rate_zones"] = activity["heart_rate_zones"]

    lap_paces = [
        pace_seconds_per_kilometer(float(lap["duration_seconds"]), float(lap["distance_meters"]))
        for lap in laps
        if lap.get("distance_meters", 0) > 0
    ]
    if lap_paces:
        result["best_pace_seconds_per_kilometer"] = min(lap_paces)
        result["lap_paces_seconds_per_kilometer"] = lap_paces
        result["pace_consistency_seconds"] = pstdev(lap_paces) if len(lap_paces) > 1 else 0.0

    if len(samples) >= 2:
        midpoint = len(samples) // 2
        first_half = samples[:midpoint]
        second_half = samples[midpoint:]
        first_hr = _average(first_half, "heart_rate")
        second_hr = _average(second_half, "heart_rate")
        first_pace = _average(first_half, "pace_seconds_per_kilometer")
        second_pace = _average(second_half, "pace_seconds_per_kilometer")
        if first_hr and second_hr and first_pace and second_pace:
            first_efficiency = first_hr / first_pace
            second_efficiency = second_hr / second_pace
            result["pace_hr_drift_percent"] = (second_efficiency / first_efficiency - 1) * 100
    return result


def _average(samples: Sequence[Mapping[str, Any]], field: str) -> float | None:
    values = [float(sample[field]) for sample in samples if sample.get(field) is not None]
    return sum(values) / len(values) if values else None