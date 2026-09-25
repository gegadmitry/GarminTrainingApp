from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from garmin_training.database import connect
from garmin_training.validation import upsert_activity, validate_activity


class ActivityValidationTests(unittest.TestCase):
    def test_negative_values_are_rejected(self) -> None:
        result = validate_activity(self._record(duration_seconds=-1))

        self.assertEqual("invalid", result.status)
        self.assertIn("duration_seconds", " ".join(result.messages))
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "training.sqlite3")
            with self.assertRaises(ValueError):
                upsert_activity(connection, self._record(duration_seconds=-1))

    def test_duplicate_activity_updates_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "training.sqlite3")
            upsert_activity(connection, self._record(duration_seconds=60))
            upsert_activity(connection, self._record(duration_seconds=120))
            row = connection.execute(
                "SELECT COUNT(*), duration_seconds FROM activities WHERE garmin_activity_id = ?",
                ("activity-1",),
            ).fetchone()

            self.assertEqual((1, 120.0), row)

    def test_missing_pool_sensor_data_is_partial_and_unavailable(self) -> None:
        result = validate_activity(self._record(sport="pool_swim"))

        self.assertEqual("partial", result.status)
        self.assertTrue(any("unavailable" in message for message in result.messages))

    @staticmethod
    def _record(**overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "garmin_activity_id": "activity-1",
            "sport": "run",
            "start_time_utc": "2026-09-25T00:00:00Z",
            "duration_seconds": 600,
            "distance_meters": 2000,
        }
        record.update(overrides)
        return record


if __name__ == "__main__":
    unittest.main()