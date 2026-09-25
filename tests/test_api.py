from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from garmin_training.api import create_app
from garmin_training.database import connect


class ApiTests(unittest.TestCase):
    def test_health_and_activity_query_use_local_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "training.sqlite3"
            connection = connect(database_path)
            connection.execute(
                "INSERT INTO activities(garmin_activity_id, sport, start_time_utc, duration_seconds) "
                "VALUES (?, ?, ?, ?)",
                ("run-1", "run", "2026-09-25T08:00:00Z", 600),
            )
            connection.commit()
            connection.close()
            client = TestClient(create_app(database_path))

            self.assertEqual(200, client.get("/health").status_code)
            response = client.get("/activities", params={"sport": "run"})

            self.assertEqual(200, response.status_code)
            self.assertEqual("run-1", response.json()[0]["garmin_activity_id"])

    def test_sync_status_is_empty_without_a_sync(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(Path(directory) / "training.sqlite3"))

            response = client.get("/sync/status")

            self.assertEqual(200, response.status_code)
            self.assertEqual({"status": None, "updated_at_utc": None}, response.json())


if __name__ == "__main__":
    unittest.main()