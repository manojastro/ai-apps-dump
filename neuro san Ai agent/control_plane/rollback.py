"""Rollback controller + verify-and-recover composer (M17).

Failed verification → restore the before-snapshot → prove the restore →
otherwise escalate with the full trail (original state, action, failed
postconditions, rollback result, escalation target). Audit rows carry it all.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from audit.logger import log_event
from control_plane import registry as script_registry
from control_plane.verification import (capture_state, verification_json,
                                        verify_remediation)
from database.models import AuditEvent

VERIFIED = "verified"
ROLLED_BACK = "rolled_back"
ESCALATE = "escalate_required"


def rollback_action(estate: Any, device_id: str, before: dict[str, Any]) -> dict[str, Any]:
    """Restore snapshot keys. Returns what was restored."""
    device = estate.get(device_id)
    restored: dict[str, Any] = {}
    for key in ("cpu_pct", "ram_pct", "disk_pct"):
        if key in before:
            setattr(device, key, float(before[key]))
            restored[key] = float(before[key])
    if "teams_mb" in before:
        for proc in device.processes:
            if proc.name == "Teams":
                proc.mem_mb = float(before["teams_mb"])
        restored["teams_mb"] = float(before["teams_mb"])
    if "vpn_connected" in before:
        device.vpn_connected = bool(before["vpn_connected"])
        device.vpn_last_error = "" if device.vpn_connected else "restored pre-fix state"
        restored["vpn_connected"] = device.vpn_connected
    if "issues" in before:
        device.issues = sorted(before["issues"])
        restored["issues"] = device.issues
    return restored


def verify_rollback(estate: Any, device_id: str, before: dict[str, Any]) -> bool:
    """True when the live snapshot matches the before-snapshot on saved keys."""
    from simulator.actions import snapshot
    live = json.loads(snapshot(device_id, estate))
    return all(live.get(k) == before.get(k) for k in before if k in live)


def verify_and_recover(conn: sqlite3.Connection, estate: Any, run_id: str,
                       case_id: str = "", params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Verify fresh telemetry; roll back on failure; escalate when stuck."""
    row = conn.execute("SELECT * FROM remediation_runs WHERE run_id=?",
                       (run_id,)).fetchone()
    if row is None:
        raise LookupError(f"run {run_id} not found")
    run = dict(row)
    action_id, device_id = run["script_id"], run["device_id"]
    before = json.loads(run["before_state"] or "{}")
    after = capture_state(estate, device_id, action_id)
    verdict = verify_remediation(before, after, action_id, params)
    conn.execute("UPDATE remediation_runs SET verification_result=? WHERE run_id=?",
                 (verification_json(verdict), run_id))
    conn.commit()
    log_event(conn, AuditEvent(
        case_id=case_id or run["case_id"], agent="verification_controller",
        event_type="verification", tool="verify_remediation",
        sanitized_input=json.dumps({"run_id": run_id, "action_id": action_id}),
        sanitized_output=verification_json(verdict),
        action=action_id, success=1 if verdict.passed else 0))
    if verdict.passed:
        return {"outcome": VERIFIED, "run_id": run_id, "failed": []}

    script = script_registry.lookup_script(conn, action_id) or {}
    if not script.get("rollback_available"):
        return {"outcome": ESCALATE, "run_id": run_id, "failed": verdict.failed,
                "reason": "no rollback available; human escalation required",
                "escalation_target": "support-queue"}

    restored = rollback_action(estate, device_id, before)
    rollback_ok = verify_rollback(estate, device_id, before)
    rb_id = f"{run_id}-RB"
    conn.execute(
        "INSERT INTO remediation_runs(run_id, case_id, script_id, device_id, "
        "before_state, after_state, success) VALUES (?,?,?,?,?,?,?)",
        (rb_id, run["case_id"], action_id, device_id,
         json.dumps(after), json.dumps(before), 1 if rollback_ok else 0))
    conn.execute("UPDATE remediation_runs SET rollback_run_id=? WHERE run_id=?",
                 (rb_id, run_id))
    conn.commit()
    script_registry.record_execution(conn, action_id, False, rollback=True)
    log_event(conn, AuditEvent(
        case_id=case_id or run["case_id"], agent="rollback_controller",
        event_type="rollback", tool="rollback_action",
        sanitized_input=json.dumps({"run_id": run_id}),
        sanitized_output=json.dumps({"restored": restored, "verified": rollback_ok}),
        action=action_id, success=1 if rollback_ok else 0))
    if rollback_ok:
        return {"outcome": ROLLED_BACK, "run_id": run_id, "failed": verdict.failed,
                "rollback_run_id": rb_id}
    return {"outcome": ESCALATE, "run_id": run_id, "failed": verdict.failed,
            "reason": "rollback verification failed; human escalation required",
            "escalation_target": "support-queue"}
