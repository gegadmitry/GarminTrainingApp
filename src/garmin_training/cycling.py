"""Deterministic cycling analysis with optional power-meter support."""

from __future__ import annotations

from statistics import pstdev
from typing import Any, Mapping, Sequence


def analyze_cycling(
    activity: Mapping[str, Any],
    samples: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    duration = float(activity["duration_seconds"])
    distance = float(activity["distance_meters"])
    if duration <= 0 or distance < 0:
        raise ValueError("cycling duration must be positive and distance non-negative")
    speed_mps = activity.get("average_speed_mps", distance / duration)
    result: dict[str, Any] = {
        "duration_seconds": duration,
        "distance_meters": distance,
        "speed_meters_per_second": speed_mps,
        "speed_kmh": float(speed_mps) * 3.6,
    }
    for field in ("elevation_gain_meters", "cadence_rpm", "average_heart_rate", "heart_rate_zones"):
        if activity.get(field) is not None:
            result[field] = activity[field]

    speeds = [float(sample["speed_meters_per_second"]) for sample in samples if sample.get("speed_meters_per_second") is not None]
    if len(speeds) > 1:
        result["speed_consistency_mps"] = pstdev(speeds)

    power_values = [float(sample["power_watts"]) for sample in samples if sample.get("power_watts") is not None]
    if activity.get("average_power_watts") is not None:
        power_values.append(float(activity["average_power_watts"]))
    if power_values and all(value >= 0 for value in power_values):
        result["power_available"] = True
        result["average_power_watts"] = sum(power_values) / len(power_values)
        result["max_power_watts"] = max(power_values)
    else:
        result["power_available"] = False
    return result