"""Risk classification (M15): deterministic, no LLM.

Order of truth: registry risk when the action is known; else the maximum
primitive risk; unknown actions default HIGH (safe side, never LOW).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from control_plane.script_intake import PRIMITIVE_RISK

_RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def classify_action_risk(conn: sqlite3.Connection, action_id: str,
                         primitives: list[str] | None = None) -> dict[str, Any]:
    """Return {risk, basis}. Basis names the source for auditability."""
    row = conn.execute("SELECT risk FROM scripts WHERE script_id=?",
                       (action_id,)).fetchone()
    if row and row["risk"] in _RISK_ORDER:
        return {"risk": row["risk"], "basis": "registry"}
    if primitives:
        unknown = [p for p in primitives if p not in PRIMITIVE_RISK]
        if unknown:
            return {"risk": "HIGH", "basis": f"unknown primitives {sorted(unknown)}"}
        computed = max((PRIMITIVE_RISK[p] for p in primitives),
                       key=_RISK_ORDER.index)
        return {"risk": computed, "basis": "primitives-max"}
    return {"risk": "HIGH", "basis": "unknown action defaults HIGH"}
