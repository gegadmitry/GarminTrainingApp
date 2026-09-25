"""Localhost-only FastAPI application shell."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from .database import connect


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application: str
    database: str


class SyncStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None
    updated_at_utc: str | None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    garmin_activity_id: str
    sport: str
    start_time_utc: str
    duration_seconds: float
    distance_meters: float | None
    data_quality_status: str


class ActivityDetailResponse(ActivityResponse):
    model_config = ConfigDict(extra="forbid")

    calories: float | None
    average_heart_rate: int | None
    max_heart_rate: int | None
    elevation_gain_meters: float | None
    validation_messages: str
    provenance_source: str | None
    parser_version: str | None
    raw_file_path: str | None
    raw_file_hash: str | None


def create_app(database_path: str | Path | None = None) -> FastAPI:
    configured_path = Path(database_path or os.environ.get("GARMIN_DATABASE_PATH", "data/training.sqlite3"))
    application = FastAPI(title="Garmin Training API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
    )

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        try:
            connection = connect(configured_path)
            connection.execute("SELECT 1")
            connection.close()
        except sqlite3.Error as error:
            raise HTTPException(status_code=503, detail="database unavailable") from error
        return HealthResponse(application="ok", database="ok")

    @application.get("/sync/status", response_model=SyncStatusResponse)
    def sync_status() -> SyncStatusResponse:
        connection = connect(configured_path)
        row = connection.execute(
            "SELECT value, updated_at_utc FROM sync_state WHERE key = 'status'"
        ).fetchone()
        connection.close()
        return SyncStatusResponse(status=row[0] if row else None, updated_at_utc=row[1] if row else None)

    @application.get("/activities", response_model=list[ActivityResponse])
    def activities(
        sport: str | None = Query(default=None),
        start: datetime | None = Query(default=None),
        end: datetime | None = Query(default=None),
    ) -> list[ActivityResponse]:
        connection = connect(configured_path)
        query = (
            "SELECT id, garmin_activity_id, sport, start_time_utc, duration_seconds, "
            "distance_meters, data_quality_status FROM activities WHERE 1 = 1"
        )
        parameters: list[Any] = []
        if sport:
            query += " AND sport = ?"
            parameters.append(sport)
        if start:
            query += " AND start_time_utc >= ?"
            parameters.append(start.isoformat().replace("+00:00", "Z"))
        if end:
            query += " AND start_time_utc <= ?"
            parameters.append(end.isoformat().replace("+00:00", "Z"))
        query += " ORDER BY start_time_utc DESC"
        rows = connection.execute(query, parameters).fetchall()
        connection.close()
        return [ActivityResponse(**dict(zip(ActivityResponse.model_fields, row))) for row in rows]

    @application.get("/activities/{activity_id}", response_model=ActivityDetailResponse)
    def activity_detail(activity_id: int) -> ActivityDetailResponse:
        connection = connect(configured_path)
        row = connection.execute(
            "SELECT a.id, a.garmin_activity_id, a.sport, a.start_time_utc, "
            "a.duration_seconds, a.distance_meters, a.data_quality_status, "
            "a.calories, a.average_heart_rate, a.max_heart_rate, "
            "a.elevation_gain_meters, a.validation_messages, p.source, "
            "p.parser_version, p.raw_file_path, p.raw_file_hash "
            "FROM activities AS a LEFT JOIN activity_provenance AS p "
            "ON p.activity_id = a.id WHERE a.id = ?",
            (activity_id,),
        ).fetchone()
        connection.close()
        if row is None:
            raise HTTPException(status_code=404, detail="activity not found")
        values = dict(zip(ActivityDetailResponse.model_fields, row))
        return ActivityDetailResponse(**values)

    return application


app = create_app()