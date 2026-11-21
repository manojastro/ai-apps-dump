"""Tamper-evident audit trail: an append-only SQLite table with a SHA-256 hash chain.

Each entry's hash covers its sequence number, time, case, event, payload and the previous
entry's hash, so editing, deleting or reordering any row breaks every hash after it.
Triggers reject UPDATE and DELETE; `verify_chain` detects tampering that bypasses them
(for example, editing the database file directly).

Appends are idempotent per `event_key`: if a graph node re-runs after a crash, the same
event is not recorded twice.
"""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from invoiceflow.data.models import Frozen
from invoiceflow.observability.masking import mask

GENESIS = "0" * 64
SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    seq        INTEGER PRIMARY KEY,
    event_key  TEXT NOT NULL UNIQUE,
    ts         TEXT NOT NULL,
    case_id    TEXT NOT NULL,
    event      TEXT NOT NULL,
    payload    TEXT NOT NULL,
    prev_hash  TEXT NOT NULL,
    hash       TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""


class AuditEntry(Frozen):
    seq: int
    event_key: str
    ts: str
    case_id: str
    event: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str


class ChainCheck(Frozen):
    ok: bool
    entries: int
    first_bad_seq: int | None = None
    detail: str = ""


def entry_hash(seq: int, ts: str, case_id: str, event: str, payload: str, prev_hash: str) -> str:
    material = json.dumps([seq, ts, case_id, event, payload, prev_hash], ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.executescript(SCHEMA)

    def append(
        self, case_id: str, event: str, payload: dict[str, Any], event_key: str
    ) -> AuditEntry:
        existing = self._conn.execute(
            "SELECT * FROM audit_log WHERE event_key = ?", (event_key,)
        ).fetchone()
        if existing:
            return self._entry(existing)
        body = json.dumps(mask(payload), sort_keys=True, ensure_ascii=False, default=str)
        with self._conn:
            last = self._conn.execute(
                "SELECT seq, hash FROM audit_log ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            seq = (last[0] + 1) if last else 1
            prev = last[1] if last else GENESIS
            ts = datetime.now(UTC).isoformat(timespec="microseconds")
            digest = entry_hash(seq, ts, case_id, event, body, prev)
            self._conn.execute(
                "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (seq, event_key, ts, case_id, event, body, prev, digest),
            )
        return AuditEntry(
            seq=seq,
            event_key=event_key,
            ts=ts,
            case_id=case_id,
            event=event,
            payload=json.loads(body),
            prev_hash=prev,
            hash=digest,
        )

    @staticmethod
    def _entry(row: tuple[Any, ...]) -> AuditEntry:
        seq, key, ts, case_id, event, payload, prev, digest = row
        return AuditEntry(
            seq=seq,
            event_key=key,
            ts=ts,
            case_id=case_id,
            event=event,
            payload=json.loads(payload),
            prev_hash=prev,
            hash=digest,
        )

    def entries(self, case_id: str | None = None) -> list[AuditEntry]:
        if case_id:
            rows = self._conn.execute(
                "SELECT * FROM audit_log WHERE case_id = ? ORDER BY seq", (case_id,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM audit_log ORDER BY seq").fetchall()
        return [self._entry(row) for row in rows]

    def verify(self) -> ChainCheck:
        rows = self._conn.execute("SELECT * FROM audit_log ORDER BY seq").fetchall()
        prev = GENESIS
        for expected_seq, row in enumerate(rows, start=1):
            seq, _, ts, case_id, event, payload, prev_hash, digest = row
            if seq != expected_seq:
                return ChainCheck(
                    ok=False,
                    entries=len(rows),
                    first_bad_seq=expected_seq,
                    detail=f"sequence gap: expected {expected_seq}, found {seq}",
                )
            if prev_hash != prev:
                return ChainCheck(
                    ok=False,
                    entries=len(rows),
                    first_bad_seq=seq,
                    detail="previous-hash link broken",
                )
            if entry_hash(seq, ts, case_id, event, payload, prev_hash) != digest:
                return ChainCheck(
                    ok=False,
                    entries=len(rows),
                    first_bad_seq=seq,
                    detail="entry content does not match its hash",
                )
            prev = digest
        return ChainCheck(ok=True, entries=len(rows))

    def close(self) -> None:
        self._conn.close()


def verify_audit_chain(path: Path) -> ChainCheck:
    log = AuditLog(path)
    try:
        return log.verify()
    finally:
        log.close()
