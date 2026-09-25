"""Normalize Garmin activity records while preserving source provenance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


SPORT_MAP = {
    "running": "run",
    "run": "run",
    "cycling": "cycling",
    "bike": "cycling",
    "pool_swimming": "pool_swim",
    "lap_swimming": "pool_swim",
    "pool_swim": "pool_swim",
}


def normalize_activity(
    source_values: Mapping[str, Any],
    source: str,
    parser_version: str,
    imported_at_utc: str | None = None,
) -> dict[str, Any]:
    """Return canonical values plus the untouched source payload."""
    duration = _number(source_values.get("duration_seconds"), "duration_seconds")
    distance = _number(source_values.get("distance_meters"), "distance_meters")
    sport_value = str(source_values.get("sport") or source_values.get("activity_type") or "unknown").lower()
    sport = SPORT_MAP.get(sport_value, "unknown")
    normalized: dict[str, Any] = {
        "garmin_activity_id": source_values.get("garmin_activity_id"),
        "sport": sport,
        "duration_seconds": duration,
        "distance_meters": distance,
        "start_time_utc": source_values.get("start_time_utc"),
        "source_values": dict(source_values),
        "provenance": {
            "source": source,
            "parser_version": parser_version,
            "imported_at_utc": imported_at_utc or datetime.now(timezone.utc).isoformat(),
            "raw_file_path": source_values.get("raw_file_path"),
        },
    }
    if sport == "run" and duration is not None and distance:
        normalized["pace_seconds_per_kilometer"] = duration / (distance / 1000)
    if sport == "cycling":
        speed_mps = source_values.get("average_speed_mps")
        if speed_mps is None and source_values.get("average_speed_kmh") is not None:
            speed_mps = float(source_values["average_speed_kmh"]) / 3.6
        normalized["speed_meters_per_second"] = speed_mps
    if sport == "pool_swim" and duration is not None and distance:
        normalized["pace_seconds_per_100m"] = duration / (distance / 100)
    return normalized


def _number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    number = float(value)
    if number < 0:
        raise ValueError(f"{field} must not be negative")
    return number