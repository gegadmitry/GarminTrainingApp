"""SQLite database setup and migrations for normalized Garmin records."""

from __future__ import annotations

import sqlite3
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Apply every pending SQL migration in filename order."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """
    )
    applied_versions = {
        row[0] for row in connection.execute("SELECT version FROM schema_migrations")
    }
    for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if migration_path.name in applied_versions:
            continue
        with connection:
            connection.executescript(migration_path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO schema_migrations(version) VALUES (?)", (migration_path.name,)
            )


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Open a foreign-key-enforced database and apply pending migrations."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    apply_migrations(connection)
    return connection