"""Deterministic weekly multisport load and recovery summaries."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import sqlite3
from typing import Any, Mapping, Sequence


SPORTS = ("run", "cycling", "pool_swim")


def weekly_summary(
    activities: Sequence[Mapping[str, Any]],
    health: Mapping[str, Any] | None = None,
    week_start: date | None = None,
    previous: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected_start = week_start or _monday_for(activities)
    selected_end = selected_start + timedelta(days=7)
    selected = [
        activity
        for activity in activities
        if selected_start <= _activity_date(activity) < selected_end
    ]
    by_sport = {
        sport: {
            "duration_seconds": sum(
                float(activity.get("duration_seconds") or 0)
                for activity in selected
                if activity.get("sport") == sport
            ),
            "load": sum(
                float(activity.get("load_value") or 0)
                for activity in selected
                if activity.get("sport") == sport
            ),
        }
        for sport in SPORTS
    }
    total_load = sum(values["load"] for values in by_sport.values())
    completed_dates = {_activity_date(activity) for activity in selected}
    report: dict[str, Any] = {
        "week_start_utc": selected_start.isoformat(),
        "sports": by_sport,
        "completed_sessions": len(selected),
        "hard_sessions": sum(1 for activity in selected if _is_hard(activity)),
        "recovery_days": 7 - len(completed_dates),
        "total_load": total_load,
    }
    if health:
        report["health"] = {
            key: health[key]
            for key in ("sleep_seconds", "hrv", "body_battery", "readiness")
            if health.get(key) is not None
        }
    if previous:
        report["week_over_week"] = {
            "load_change": total_load - float(previous.get("total_load") or 0),
            "session_change": report["completed_sessions"]
            - int(previous.get("completed_sessions") or 0),
        }
    return report


def persist_weekly_summary(connection: sqlite3.Connection, report: Mapping[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO weekly_reports(week_start_utc, summary_json)
        VALUES (?, ?)
        ON CONFLICT(week_start_utc) DO UPDATE SET summary_json = excluded.summary_json
        """,
        (report["week_start_utc"], json.dumps(report, sort_keys=True)),
    )


def _activity_date(activity: Mapping[str, Any]) -> date:
    timestamp = str(activity["start_time_utc"]).replace("Z", "+00:00")
    return datetime.fromisoformat(timestamp).date()


def _monday_for(activities: Sequence[Mapping[str, Any]]) -> date:
    if not activities:
        return datetime.now(timezone.utc).date() - timedelta(days=datetime.now(timezone.utc).weekday())
    activity_date = _activity_date(activities[0])
    return activity_date - timedelta(days=activity_date.weekday())


def _is_hard(activity: Mapping[str, Any]) -> bool:
    return float(activity.get("training_effect_aerobic") or 0) >= 3 or float(
        activity.get("load_value") or 0
    ) >= 100