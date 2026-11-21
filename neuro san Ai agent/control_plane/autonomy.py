"""Autonomy engine (M15): earned trust with deterministic thresholds.

Levels: L0 observe-only, L1 recommend-only, L2 human approval required,
L3 auto-execute approved, L4 autonomous execute+verify+rollback.
New entities start L1. Promotion/demotion read live metrics only —
no LLM participates. Thresholds are constants below (tune in one place).

Promotion ladder (all conditions must hold):
  L1→L2: >=2 human approvals for the entity.
  L2→L3: >=10 runs, success>=95%, rollback<=5%, reopen<=5%, zero DENY decisions.
  L3→L4: >=50 runs, success>=98%, rollback<=2%, reopen<=2%, zero DENY,
          rollback_available=1.
Demotion (safety first, evaluated before promotion):
  >=3 failures in the last 10 runs → L2 (human approval again).
  Any DENY decision while L3+ → L2.
Entities: scripts (remediation_runs) and workflows (workflow_runs) share
metric column names, so one code path serves both via table/column config.
"""

from __future__ import annotations

import sqlite3
from typing import Any

LEVELS = ("L0", "L1", "L2", "L3", "L4")

L1_TO_L2_APPROVALS = 2
L2_TO_L3_RUNS = 10
L2_TO_L3_SUCCESS = 95.0
L2_TO_L3_ROLLBACK = 5.0
L2_TO_L3_REOPEN = 5.0
L3_TO_L4_RUNS = 50
L3_TO_L4_SUCCESS = 98.0
L3_TO_L4_ROLLBACK = 2.0
L3_TO_L4_REOPEN = 2.0
RECENT_WINDOW = 10
RECENT_FAILURES_DEMOTE = 3

_ENTITY = {
    "script": {"table": "scripts", "id_col": "script_id",
               "runs_table": "remediation_runs", "runs_id_col": "script_id"},
    "workflow": {"table": "workflows", "id_col": "workflow_id",
                 "runs_table": "workflow_runs", "runs_id_col": "workflow_id"},
}


def _row(conn: sqlite3.Connection, entity: str, entity_id: str) -> dict[str, Any] | None:
    cfg = _ENTITY[entity]
    row = conn.execute(f"SELECT * FROM {cfg['table']} WHERE {cfg['id_col']}=?",
                       (entity_id,)).fetchone()
    return dict(row) if row else None


def _recent_failures(conn: sqlite3.Connection, entity: str, entity_id: str) -> int:
    cfg = _ENTITY[entity]
    rows = conn.execute(
        f"SELECT success FROM {cfg['runs_table']} WHERE {cfg['runs_id_col']}=? "
        f"ORDER BY rowid DESC LIMIT {RECENT_WINDOW}", (entity_id,)).fetchall()
    return sum(1 for r in rows if not r["success"])


def _approvals(conn: sqlite3.Connection, entity_id: str) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM approvals WHERE script_id=? "
                        "AND state='APPROVED'", (entity_id,)).fetchone()["n"]


def _deny_count(conn: sqlite3.Connection, entity_id: str) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM policy_decisions WHERE script_id=? "
                        "AND decision='DENY'", (entity_id,)).fetchone()["n"]


def _pct(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def evaluate_autonomy(conn: sqlite3.Connection, entity: str,
                      entity_id: str) -> dict[str, Any]:
    """Return {current, recommended, reasons[]}. Never raises on missing rows."""
    if entity not in _ENTITY:
        raise ValueError(f"unknown entity {entity}")
    row = _row(conn, entity, entity_id)
    if row is None:
        return {"current": "L1", "recommended": "L1",
                "reasons": ["unknown entity starts at L1"]}
    current = str(row.get("autonomy_level", "L1"))
    if current not in LEVELS:
        current = "L1"
    reasons = [f"current={current}"]
    if current == "L0":
        return {"current": current, "recommended": "L0",
                "reasons": reasons + ["L0 is terminal (deny-listed class)"]}
    if _recent_failures(conn, entity, entity_id) >= RECENT_FAILURES_DEMOTE:
        return {"current": current, "recommended": "L2",
                "reasons": reasons + [f">={RECENT_FAILURES_DEMOTE} failures in last "
                                       f"{RECENT_WINDOW} runs"]}
    if current in ("L3", "L4") and _deny_count(conn, entity_id) > 0:
        return {"current": current, "recommended": "L2",
                "reasons": reasons + ["policy DENY recorded at high autonomy"]}
    runs = int(row.get("execution_count", 0) or 0)
    wins = int(row.get("success_count", 0) or 0)
    rollbacks = int(row.get("rollback_count", 0) or 0)
    reopens = int(row.get("reopen_count", 0) or 0)
    success, rollback_rate = _pct(wins, runs), _pct(rollbacks, runs)
    reopen_rate = _pct(reopens, runs)
    denies = _deny_count(conn, entity_id)
    rollback_ok = bool(row.get("rollback_available", 0))

    def ladder_ok(min_runs: float, min_success: float, max_rb: float, max_ro: float,
                  need_rollback: bool = False) -> bool:
        return (runs >= min_runs and success >= min_success
                and rollback_rate <= max_rb and reopen_rate <= max_ro
                and denies == 0 and (rollback_ok or not need_rollback))

    if current == "L1":
        if _approvals(conn, entity_id) >= L1_TO_L2_APPROVALS:
            return {"current": current, "recommended": "L2",
                    "reasons": reasons + [f">={L1_TO_L2_APPROVALS} approvals"]}
        return {"current": current, "recommended": "L1",
                "reasons": reasons + ["needs human approvals first"]}
    if current == "L2":
        if ladder_ok(L2_TO_L3_RUNS, L2_TO_L3_SUCCESS, L2_TO_L3_ROLLBACK, L2_TO_L3_REOPEN):
            return {"current": current, "recommended": "L3",
                    "reasons": reasons + [f"{runs} runs at {success}%"]}
        return {"current": current, "recommended": "L2",
                "reasons": reasons + [f"needs {L2_TO_L3_RUNS}+ runs at "
                                       f">={L2_TO_L3_SUCCESS}% (now {runs}/{success}%)"]}
    if ladder_ok(L3_TO_L4_RUNS, L3_TO_L4_SUCCESS, L3_TO_L4_ROLLBACK, L3_TO_L4_REOPEN,
                 need_rollback=True):
        return {"current": current, "recommended": "L4",
                "reasons": reasons + [f"{runs} runs at {success}% with rollback"]}
    return {"current": current, "recommended": current,
            "reasons": reasons + ["holds: L4 bar not met, no demotion signal"]}


def apply_autonomy(conn: sqlite3.Connection, entity: str,
                   entity_id: str) -> dict[str, Any]:
    """Write the engine recommendation (deterministic, auditable)."""
    cfg = _ENTITY.get(entity)
    if cfg is None:
        raise ValueError(f"unknown entity {entity}")
    outcome = evaluate_autonomy(conn, entity, entity_id)
    if outcome["recommended"] != outcome["current"] and _row(conn, entity, entity_id):
        conn.execute(f"UPDATE {cfg['table']} SET autonomy_level=? WHERE {cfg['id_col']}=?",
                     (outcome["recommended"], entity_id))
        conn.commit()
    return outcome
