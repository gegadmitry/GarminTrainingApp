from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
import tempfile
import unittest
from pathlib import Path

from garmin_training.database import connect
from garmin_training.raw_payloads import RawPayloadStore, record_provenance


class RawPayloadStoreTests(unittest.TestCase):
    def test_duplicate_payloads_reuse_hashed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RawPayloadStore(Path(directory) / "raw")
            recorded_at = datetime(2026, 9, 25, tzinfo=timezone.utc)
            first = store.store("activity", "garmin/123", {"distance": 100}, recorded_at)
            second = store.store("activity", "another-id", {"distance": 100}, recorded_at)

            self.assertEqual(first, second)
            self.assertEqual(1, len(list(store.root.iterdir())))
            self.assertEqual(0o600, first.path.stat().st_mode & 0o777)
            self.assertIn("activity-garmin-123-20260925T000000Z", first.path.name)

    def test_provenance_records_external_path_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            database_path = Path(directory) / "training.sqlite3"
            store = RawPayloadStore(root)
            payload = store.store("activity", "123", b"raw-data")
            connection = connect(database_path)
            connection.execute(
                "INSERT INTO activities(garmin_activity_id, sport, start_time_utc, duration_seconds) "
                "VALUES (?, ?, ?, ?)",
                ("123", "run", "2026-09-25T00:00:00Z", 60),
            )
            record_provenance(
                connection,
                1,
                payload,
                "garmin",
                "parser-1",
                "2026-09-25T00:01:00Z",
            )
            connection.commit()
            row = connection.execute(
                "SELECT raw_file_path, raw_file_hash FROM activity_provenance"
            ).fetchone()

            self.assertEqual((str(payload.path), payload.content_hash), row)
            self.assertTrue(Path(row[0]).is_relative_to(root))
            connection.close()

    def test_raw_store_rejects_repository_path(self) -> None:
        with self.assertRaises(ValueError):
            RawPayloadStore(Path.cwd() / "data")


if __name__ == "__main__":
    unittest.main()