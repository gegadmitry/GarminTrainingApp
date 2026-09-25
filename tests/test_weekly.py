from __future__ import annotations

from datetime import date
import json
import tempfile
import unittest
from pathlib import Path

from garmin_training.database import connect
from garmin_training.weekly import persist_weekly_summary, weekly_summary


class WeeklySummaryTests(unittest.TestCase):
    def test_sports_are_separated_and_missing_health_does_not_block(self) -> None:
        report = weekly_summary(
            [
                {
                    "sport": "run",
                    "start_time_utc": "2026-09-21T08:00:00Z",
                    "duration_seconds": 3600,
                    "load_value": 120,
                    "training_effect_aerobic": 3.2,
                },
                {
                    "sport": "cycling",
                    "start_time_utc": "2026-09-23T08:00:00Z",
                    "duration_seconds": 1800,
                    "load_value": 50,
                },
            ],
            week_start=date(2026, 9, 21),
        )

        self.assertEqual(3600.0, report["sports"]["run"]["duration_seconds"])
        self.assertEqual(1800.0, report["sports"]["cycling"]["duration_seconds"])
        self.assertEqual(1, report["hard_sessions"])
        self.assertNotIn("health", report)

    def test_health_and_week_over_week_values_are_optional(self) -> None:
        report = weekly_summary(
            [{"sport": "pool_swim", "start_time_utc": "2026-09-21T08:00:00Z", "load_value": 40}],
            health={"sleep_seconds": 28800, "hrv": None},
            week_start=date(2026, 9, 21),
            previous={"total_load": 20, "completed_sessions": 0},
        )

        self.assertEqual({"sleep_seconds": 28800}, report["health"])
        self.assertEqual(20.0, report["week_over_week"]["load_change"])

    def test_weekly_report_is_persisted_for_selected_week(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "training.sqlite3")
            report = weekly_summary([], week_start=date(2026, 9, 21))
            persist_weekly_summary(connection, report)
            connection.commit()
            stored = connection.execute(
                "SELECT summary_json FROM weekly_reports WHERE week_start_utc = ?",
                ("2026-09-21",),
            ).fetchone()

            self.assertEqual(report, json.loads(stored[0]))


if __name__ == "__main__":
    unittest.main()