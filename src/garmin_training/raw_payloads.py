"""Store raw Garmin payloads outside the source tree with content hashes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Mapping, Any


DEFAULT_RAW_ROOT = Path.home() / ".local" / "share" / "garmin-training" / "raw"
SAFE_PART = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class RawPayload:
    path: Path
    content_hash: str


class RawPayloadStore:
    """Persist raw responses and reuse an existing file for duplicate content."""

    def __init__(self, root: str | Path | None = None) -> None:
        configured_root = root or os.environ.get("GARMIN_RAW_DATA_DIR") or DEFAULT_RAW_ROOT
        self.root = Path(configured_root).expanduser().resolve()
        repository = Path.cwd().resolve()
        if self.root == repository or repository in self.root.parents:
            raise ValueError("raw Garmin data must be stored outside the repository")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root.chmod(0o700)

    def store(
        self,
        source_type: str,
        garmin_id: str,
        payload: bytes | bytearray | Mapping[str, Any],
        recorded_at: datetime | None = None,
    ) -> RawPayload:
        content, suffix = self._serialize(payload)
        content_hash = hashlib.sha256(content).hexdigest()
        existing_path = self._find_by_hash(content_hash)
        if existing_path is not None:
            return RawPayload(existing_path, content_hash)

        timestamp = (recorded_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
        timestamp_text = timestamp.strftime("%Y%m%dT%H%M%SZ")
        filename = "-".join(
            [self._safe_part(source_type), self._safe_part(garmin_id), timestamp_text, content_hash]
        ) + suffix
        destination = self.root / filename
        destination.write_bytes(content)
        destination.chmod(0o600)
        return RawPayload(destination, content_hash)

    def _find_by_hash(self, content_hash: str) -> Path | None:
        for candidate in self.root.iterdir():
            if candidate.is_file() and content_hash in candidate.name:
                return candidate
        return None

    @staticmethod
    def _serialize(payload: bytes | bytearray | Mapping[str, Any]) -> tuple[bytes, str]:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload), ".bin"
        return json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8"), ".json"

    @staticmethod
    def _safe_part(value: str) -> str:
        sanitized = SAFE_PART.sub("-", value).strip("-.")
        if not sanitized:
            raise ValueError("source type and Garmin ID must contain a safe filename value")
        return sanitized


def record_provenance(
    connection: sqlite3.Connection,
    activity_id: int,
    raw_payload: RawPayload,
    source: str,
    parser_version: str,
    imported_at_utc: str,
) -> None:
    """Link an external raw payload to an activity in the normalized database."""
    connection.execute(
        """
        INSERT INTO activity_provenance(
            activity_id, source, parser_version, imported_at_utc, raw_file_path, raw_file_hash
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(activity_id) DO UPDATE SET
            source = excluded.source,
            parser_version = excluded.parser_version,
            imported_at_utc = excluded.imported_at_utc,
            raw_file_path = excluded.raw_file_path,
            raw_file_hash = excluded.raw_file_hash
        """,
        (
            activity_id,
            source,
            parser_version,
            imported_at_utc,
            str(raw_payload.path),
            raw_payload.content_hash,
        ),
    )