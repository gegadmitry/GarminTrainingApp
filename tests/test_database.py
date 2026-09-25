from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from garmin_training.database import connect


class DatabaseMigrationTests(unittest.TestCase):
    def test_empty_database_receives_schema_and_is_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "training.sqlite3"
            connection = connect(database_path)
            first_tables = self._table_names(connection)
            connection.close()

            connection = connect(database_path)
            self.assertEqual(first_tables, self._table_names(connection))
            self.assertEqual(
                [("001_initial.sql",), ("002_validation_messages.sql",)],
                connection.execute("SELECT version FROM schema_migrations").fetchall(),
            )
            connection.close()

    def test_activity_id_is_unique_and_utc_fields_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "training.sqlite3")
            connection.execute(
                "INSERT INTO activities(garmin_activity_id, sport, start_time_utc, duration_seconds) "
                "VALUES (?, ?, ?, ?)",
                ("activity-1", "run", "2026-09-25T08:00:00Z", 1800),
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO activities(garmin_activity_id, sport, start_time_utc, duration_seconds) "
                    "VALUES (?, ?, ?, ?)",
                    ("activity-1", "cycling", "2026-09-25T09:00:00Z", 1200),
                )
            connection.commit()
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(activities)")
            }
            self.assertIn("start_time_utc", columns)
            self.assertIn("imported_at_utc", columns)
            connection.close()

    def test_sport_specific_tables_do_not_require_other_sports_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "training.sqlite3")
            connection.execute(
                "INSERT INTO activities(garmin_activity_id, sport, start_time_utc, duration_seconds) "
                "VALUES (?, ?, ?, ?)",
                ("pool-1", "pool_swim", "2026-09-25T08:00:00Z", 900),
            )
            connection.execute(
                "INSERT INTO pool_swimming_metrics(activity_id, pool_length_meters, lengths) "
                "VALUES (last_insert_rowid(), ?, ?)",
                (25, 36),
            )
            connection.commit()
            self.assertEqual(
                (25.0, 36),
                connection.execute(
                    "SELECT pool_length_meters, lengths FROM pool_swimming_metrics"
                ).fetchone(),
            )
            connection.close()

    @staticmethod
    def _table_names(connection: sqlite3.Connection) -> set[str]:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }


if __name__ == "__main__":
    unittest.main()