from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import Incident, IncidentStatus, Investigation


SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS investigations (
    incident_id TEXT PRIMARY KEY REFERENCES incidents(id),
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    detail TEXT NOT NULL
);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS investigations (
    incident_id TEXT PRIMARY KEY REFERENCES incidents(id),
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    detail TEXT NOT NULL
);
"""


def database_path(database_url: str) -> str:
    if database_url in {"sqlite:///:memory:", ":memory:"}:
        return ":memory:"
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        return database_url[len(prefix) :]
    # Compose uses PostgreSQL; this POC degrades to a local durable cache if unavailable.
    return "./incident_rca.db"


class Repository:
    def __init__(self, database_url: str = "sqlite:///:memory:") -> None:
        self._lock = threading.RLock()
        self._postgres = database_url.startswith(("postgresql://", "postgres://"))
        if self._postgres:
            import psycopg
            from psycopg.rows import dict_row

            self._connection = psycopg.connect(database_url, row_factory=dict_row)
            with self._connection:
                for statement in POSTGRES_SCHEMA.split(";"):
                    if statement.strip():
                        self._connection.execute(statement)
        else:
            path = database_path(database_url)
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            with self._connection:
                self._connection.executescript(SCHEMA)

    def _sql(self, statement: str) -> str:
        return statement.replace("?", "%s") if self._postgres else statement

    def _execute(self, statement: str, parameters: tuple[Any, ...] = ()):
        return self._connection.execute(self._sql(statement), parameters)

    def save_incident(self, incident: Incident) -> Incident:
        payload = incident.model_dump_json()
        with self._lock, self._connection:
            self._execute(
                """INSERT INTO incidents(id,payload,created_at,updated_at) VALUES(?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
                (incident.id, payload, incident.created_at.isoformat(), incident.updated_at.isoformat()),
            )
        return incident

    def get_incident(self, incident_id: str) -> Incident | None:
        row = self._execute(
            "SELECT payload FROM incidents WHERE id=?", (incident_id,)
        ).fetchone()
        return Incident.model_validate_json(row["payload"]) if row else None

    def list_incidents(self) -> list[Incident]:
        rows = self._execute(
            "SELECT payload FROM incidents ORDER BY created_at DESC"
        ).fetchall()
        return [Incident.model_validate_json(row["payload"]) for row in rows]

    def update_status(self, incident: Incident, status: IncidentStatus) -> Incident:
        updated = incident.model_copy(
            update={"status": status, "updated_at": datetime.now(UTC)}
        )
        return self.save_incident(updated)

    def save_investigation(self, investigation: Investigation) -> None:
        with self._lock, self._connection:
            self._execute(
                """INSERT INTO investigations(incident_id,payload,created_at) VALUES(?,?,?)
                   ON CONFLICT(incident_id) DO UPDATE SET payload=excluded.payload,
                   created_at=excluded.created_at""",
                (
                    investigation.incident.id,
                    investigation.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def get_investigation(self, incident_id: str) -> Investigation | None:
        row = self._execute(
            "SELECT payload FROM investigations WHERE incident_id=?", (incident_id,)
        ).fetchone()
        return Investigation.model_validate_json(row["payload"]) if row else None

    def audit(self, actor: str, action: str, resource: str, detail: dict[str, Any]) -> None:
        with self._lock, self._connection:
            self._execute(
                "INSERT INTO audit_events(occurred_at,actor,action,resource,detail) VALUES(?,?,?,?,?)",
                (
                    datetime.now(UTC).isoformat(),
                    actor,
                    action,
                    resource,
                    json.dumps(detail, sort_keys=True),
                ),
            )

    def list_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._execute(
            "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {
                "id": row["id"],
                "occurred_at": row["occurred_at"],
                "actor": row["actor"],
                "action": row["action"],
                "resource": row["resource"],
                "detail": json.loads(row["detail"]),
            }
            for row in rows
        ]

    def clear(self) -> None:
        with self._lock, self._connection:
            if self._postgres:
                self._connection.execute(
                    "TRUNCATE investigations, incidents, audit_events RESTART IDENTITY CASCADE"
                )
            else:
                self._connection.executescript(
                    "DELETE FROM investigations; DELETE FROM incidents; DELETE FROM audit_events;"
                )
