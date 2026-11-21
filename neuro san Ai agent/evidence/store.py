"""Evidence store (M9): SQLite persistence with stable, idempotent ids.

PK scheme: f"{case_id}-E{seq:03d}" where seq is the record order within one
investigation batch. Re-running the same case REPLACES (idempotent —
deterministic reruns converge). Agents operate on these normalized rows
wherever possible (M9 contract).
"""

from __future__ import annotations

import sqlite3
from typing import Any

SPEC_FIELDS = ("evidence_id", "case_id", "source_system", "tool", "timestamp",
               "entity", "measurement", "value", "unit", "confidence",
               "raw_reference", "sanitized_summary")


def ensure_case(conn: sqlite3.Connection, case_id: str, user_id: str = "",
                device_id: str = "", request_text: str = "") -> None:
    """Create the parent case row if missing (evidence FK requires it)."""
    conn.execute(
        "INSERT OR IGNORE INTO cases(case_id, user_id, device_id, request_text) "
        "VALUES (?,?,?,?)", (case_id, user_id, device_id, request_text))
    conn.commit()


def save_evidence(conn: sqlite3.Connection, case_id: str,
                  records: list[dict[str, Any]]) -> list[str]:
    """Persist one investigation batch. Returns stable evidence ids."""
    if not case_id:
        raise ValueError("case_id is required to store evidence")
    ids: list[str] = []
    for seq, record in enumerate(records, start=1):
        evidence_id = f"{case_id}-E{seq:03d}"
        conn.execute(
            "INSERT OR REPLACE INTO evidence(evidence_id, case_id, source_system, "
            "tool, timestamp, entity, measurement, value, unit, confidence, "
            "raw_reference, sanitized_summary) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (evidence_id, case_id, record.get("source_system", ""),
             record.get("tool", ""), record.get("timestamp", ""),
             record.get("entity", ""), record.get("measurement", ""),
             str(record.get("value", "")), record.get("unit", ""),
             float(record.get("confidence", 0.0)),
             record.get("raw_reference", ""),
             record.get("sanitized_summary", "")))
        ids.append(evidence_id)
    conn.commit()
    return ids


def list_evidence(conn: sqlite3.Connection, case_id: str) -> list[dict[str, Any]]:
    """Normalized evidence for one case, in collection order."""
    cur = conn.execute(
        "SELECT * FROM evidence WHERE case_id=? ORDER BY evidence_id", (case_id,))
    return [dict(row) for row in cur.fetchall()]


def save_hypotheses(conn: sqlite3.Connection, case_id: str,
                    scored: list[dict[str, Any]]) -> list[str]:
    """Persist RCA-ranked hypotheses with stable ids (idempotent reruns)."""
    import json
    if not case_id:
        raise ValueError("case_id is required to store hypotheses")
    ids: list[str] = []
    for rank, hyp in enumerate(scored):
        hypothesis_id = f"{case_id}-H{rank + 1:02d}"
        conn.execute(
            "INSERT OR REPLACE INTO hypotheses(hypothesis_id, case_id, rank, title, "
            "evidence_ids, confidence, status) VALUES (?,?,?,?,?,?,?)",
            (hypothesis_id, case_id, rank, hyp.get("title", ""),
             json.dumps(hyp.get("evidence", hyp.get("supporting", []))),
             float(hyp.get("confidence", 0.0)), hyp.get("status", "")))
        ids.append(hypothesis_id)
    conn.commit()
    return ids


def list_hypotheses(conn: sqlite3.Connection, case_id: str) -> list[dict[str, Any]]:
    """Ranked hypotheses for one case (rank order)."""
    cur = conn.execute(
        "SELECT * FROM hypotheses WHERE case_id=? ORDER BY rank", (case_id,))
    return [dict(row) for row in cur.fetchall()]
