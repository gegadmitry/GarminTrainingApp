"""Validation and retry-safe persistence for normalized Garmin activities."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Mapping


SUPPORTED_SPORTS = {"run", "cycling", "pool_swim", "unknown"}


@dataclass(frozen=True)
class ValidationResult:
    status: str
    messages: tuple[str, ...]


def validate_activity(record: Mapping[str, Any]) -> ValidationResult:
    messages: list[str] = []
    for field in ("garmin_activity_id", "sport", "start_time_utc", "duration_seconds"):
        if record.get(field) in (None, ""):
            messages.append(f"missing required field: {field}")

    sport = record.get("sport")
    if sport not in SUPPORTED_SPORTS:
        messages.append(f"unsupported sport: {sport}")

    for field in ("duration_seconds", "distance_meters"):
        value = record.get(field)
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            messages.append(f"invalid non-negative value: {field}")

    if sport == "pool_swim":
        if record.get("pool_length_meters") is None:
            messages.append("unavailable sport-specific field: pool_length_meters")
        if record.get("lengths") is None:
            messages.append("unavailable sport-specific field: lengths")

    invalid_messages = [message for message in messages if message.startswith(("missing", "unsupported", "invalid"))]
    status = "invalid" if invalid_messages else "partial" if messages else "valid"
    return ValidationResult(status, tuple(messages))


def upsert_activity(connection: sqlite3.Connection, record: Mapping[str, Any]) -> ValidationResult:
    """Validate and insert or update an activity by its Garmin ID."""
    result = validate_activity(record)
    if result.status == "invalid":
        raise ValueError("activity validation failed: " + "; ".join(result.messages))

    connection.execute(
        """
        INSERT INTO activities(
            garmin_activity_id, sport, start_time_utc, duration_seconds,
            distance_meters, calories, average_heart_rate, max_heart_rate,
            elevation_gain_meters, data_quality_status, validation_messages
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(garmin_activity_id) DO UPDATE SET
            sport = excluded.sport,
            start_time_utc = excluded.start_time_utc,
            duration_seconds = excluded.duration_seconds,
            distance_meters = excluded.distance_meters,
            calories = excluded.calories,
            average_heart_rate = excluded.average_heart_rate,
            max_heart_rate = excluded.max_heart_rate,
            elevation_gain_meters = excluded.elevation_gain_meters,
            data_quality_status = excluded.data_quality_status,
            validation_messages = excluded.validation_messages
        """,
        (
            record["garmin_activity_id"],
            record["sport"],
            record["start_time_utc"],
            record["duration_seconds"],
            record.get("distance_meters"),
            record.get("calories"),
            record.get("average_heart_rate"),
            record.get("max_heart_rate"),
            record.get("elevation_gain_meters"),
            result.status,
            json.dumps(result.messages),
        ),
    )
    return result