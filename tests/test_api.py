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

    def test_activity_detail_includes_provenance_and_quality(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "training.sqlite3"
            connection = connect(database_path)
            connection.execute(
                "INSERT INTO activities(garmin_activity_id, sport, start_time_utc, "
                "duration_seconds, data_quality_status, validation_messages) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("run-1", "run", "2026-09-25T08:00:00Z", 600, "partial", "distance missing"),
            )
            activity_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            connection.execute(
                "INSERT INTO activity_provenance(activity_id, source, parser_version, "
                "imported_at_utc, raw_file_path, raw_file_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (activity_id, "garmin_mcp", "1.0", "2026-09-25T09:00:00Z", "raw/run.json", "abc123"),
            )
            connection.commit()
            connection.close()

            response = TestClient(create_app(database_path)).get(f"/activities/{activity_id}")

            self.assertEqual(200, response.status_code)
            self.assertEqual("garmin_mcp", response.json()["provenance_source"])
            self.assertEqual("partial", response.json()["data_quality_status"])
            self.assertEqual("distance missing", response.json()["validation_messages"])

    def test_activity_detail_returns_not_found_for_unknown_activity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            response = TestClient(create_app(Path(directory) / "training.sqlite3")).get("/activities/99")

            self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()