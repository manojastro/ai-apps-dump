"""SIMULATED ERP storage with idempotency keys and a transactional outbox.

A write and its outbox event commit in the same transaction, so an event exists if and
only if the decision does. Re-sending a key with the same payload returns the original
decision ("replayed"); with a different payload it is a conflict.
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from invoiceflow.ports.erp import ErpConflictError, ErpResult


class ErpStore:
    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                idempotency_key TEXT PRIMARY KEY, decision_id TEXT UNIQUE, kind TEXT,
                invoice_id TEXT, action TEXT, payload TEXT, payload_sha TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id TEXT, event TEXT,
                payload TEXT, published INTEGER NOT NULL DEFAULT 0);
            """
        )

    def record(
        self, key: str, kind: str, invoice_id: str, action: str, payload: dict[str, Any]
    ) -> ErpResult:
        body = json.dumps(payload, sort_keys=True, default=str)
        sha = hashlib.sha256(f"{kind}|{invoice_id}|{action}|{body}".encode()).hexdigest()
        with self._conn:  # one transaction: decision + outbox event
            row = self._conn.execute(
                "SELECT decision_id, payload_sha, kind FROM decisions WHERE idempotency_key = ?",
                (key,),
            ).fetchone()
            if row:
                if row[1] != sha:
                    raise ErpConflictError(f"idempotency key {key} reused with a different payload")
                return ErpResult(
                    decision_id=row[0], idempotency_key=key, kind=row[2], replayed=True
                )
            decision_id = f"SIM-{uuid.uuid4().hex[:12]}"
            now = datetime.now(UTC).isoformat(timespec="seconds")
            self._conn.execute(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (key, decision_id, kind, invoice_id, action, body, sha, now),
            )
            self._conn.execute(
                "INSERT INTO outbox (decision_id, event, payload) VALUES (?, ?, ?)",
                (decision_id, f"{kind}.created", body),
            )
        return ErpResult(decision_id=decision_id, idempotency_key=key, kind=kind, replayed=False)

    def count(self, table: str = "decisions") -> int:
        if table not in {"decisions", "outbox"}:
            raise ValueError(table)
        return int(self._conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])  # noqa: S608

    def get(self, decision_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT decision_id, kind, invoice_id, action, payload, created_at FROM decisions "
            "WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "decision_id": row[0],
            "kind": row[1],
            "invoice_id": row[2],
            "action": row[3],
            "payload": json.loads(row[4]),
            "created_at": row[5],
            "simulated": True,
        }

    def outbox(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, decision_id, event, published FROM outbox ORDER BY id"
        ).fetchall()
        return [
            {"id": r[0], "decision_id": r[1], "event": r[2], "published": bool(r[3])} for r in rows
        ]
