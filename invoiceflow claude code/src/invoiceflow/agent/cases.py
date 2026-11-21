"""Case store: one row per invoice case, used by the approval inbox and the manual queue.

Statuses: RUNNING, AWAITING_APPROVAL, EXECUTED, MANUAL_QUEUE.
"""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from invoiceflow.data.models import Frozen


class Case(Frozen):
    case_id: str
    invoice_id: str
    status: str
    required_role: str | None
    preparer_id: str
    summary: dict[str, Any]
    reason: str
    updated_at: str


class CaseStore:
    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cases (case_id TEXT PRIMARY KEY, invoice_id TEXT, "
            "status TEXT, required_role TEXT, preparer_id TEXT, summary TEXT, reason TEXT, "
            "updated_at TEXT)"
        )

    def upsert(
        self,
        case_id: str,
        invoice_id: str,
        status: str,
        preparer_id: str,
        summary: dict[str, Any] | None = None,
        required_role: str | None = None,
        reason: str = "",
    ) -> None:
        now = datetime.now(UTC).isoformat(timespec="seconds")
        with self._conn:
            self._conn.execute(
                "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(case_id) DO UPDATE "
                "SET status=excluded.status, required_role=excluded.required_role, "
                "summary=excluded.summary, reason=excluded.reason, updated_at=excluded.updated_at",
                (
                    case_id,
                    invoice_id,
                    status,
                    required_role,
                    preparer_id,
                    json.dumps(summary or {}, default=str),
                    reason,
                    now,
                ),
            )

    def get(self, case_id: str) -> Case | None:
        row = self._conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        return self._case(row) if row else None

    def list(self, status: str | None = None) -> list[Case]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM cases WHERE status = ? ORDER BY case_id", (status,)
            )
        else:
            rows = self._conn.execute("SELECT * FROM cases ORDER BY case_id")
        return [self._case(r) for r in rows]

    @staticmethod
    def _case(row: tuple[Any, ...]) -> Case:
        case_id, invoice_id, status, role, preparer, summary, reason, updated = row
        return Case(
            case_id=case_id,
            invoice_id=invoice_id,
            status=status,
            required_role=role,
            preparer_id=preparer,
            summary=json.loads(summary),
            reason=reason,
            updated_at=updated,
        )
