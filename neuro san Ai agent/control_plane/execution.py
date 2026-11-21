"""Execution controller (M16): the ONLY path from proposal to endpoint effect.

Gate order per spec flow: approved+hash-intact action → policy → autonomy →
approval (when required) → execute → record. Anything else returns
refused/awaiting_approval WITHOUT touching the estate.

Execution success is recorded as executed-ok; RESOLUTION is decided by
verification (M17) on fresh telemetry — never assumed here.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from audit.logger import log_event
from control_plane import approvals
from control_plane import registry as script_registry
from control_plane.policy import DENY, REQUIRE_APPROVAL, PolicyInput, evaluate, record_decision
from database.models import AuditEvent

EXECUTED = "executed"
REFUSED = "refused"
AWAITING = "awaiting_approval"


@dataclass
class ExecutionResult:
    status: str  # executed | refused | awaiting_approval
    action_id: str = ""
    device_id: str = ""
    run_id: str = ""
    policy_decision: str = ""
    autonomy: str = ""
    approval_id: str = ""
    effect: dict[str, Any] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


def _refused(action_id: str, device_id: str, reasons: list[str], **extra: Any) -> ExecutionResult:
    return ExecutionResult(REFUSED, action_id, device_id, reasons=reasons, **extra)


def request_execution(conn: sqlite3.Connection, estate: Any, case_id: str,
                      action_id: str, device_id: str, user_id: str,
                      user_role: str = "employee", params: dict[str, Any] | None = None,
                      at_hour: int = 10) -> ExecutionResult:
    """Gate then execute. Estate mutates ONLY on the executed path."""
    from simulator.actions import apply_effect, snapshot

    action = script_registry.get_approved_action(conn, action_id)
    if action is None:
        return _refused(action_id, device_id, ["unknown, unapproved, or tampered action"])
    try:
        device = estate.get(device_id)
    except LookupError:
        return _refused(action_id, device_id, [f"unknown device {device_id}"])

    # Stored level governs execution; earned changes apply only via
    # apply_autonomy (explicit promotion pass, never implicitly per-run).
    policy_in = PolicyInput(user_id=user_id, user_role=user_role, device_id=device_id,
                            device_group=device.device_group,
                            device_compliant=device.compliance_state == "compliant",
                            action_id=action_id, at_hour=at_hour)
    gated = evaluate(conn, policy_in)
    if gated.decision == DENY:
        if case_id:
            record_decision(conn, case_id, policy_in, gated)
        return _refused(action_id, device_id,
                        [f"policy DENY: {[c.name for c in gated.checks if not c.passed]}"],
                        policy_decision=DENY)

    level = str(action.get("autonomy_level", "L2"))
    if level in ("L0", "L1"):
        if case_id:
            record_decision(conn, case_id, policy_in, gated)
        return _refused(action_id, device_id, [f"autonomy {level} never executes"],
                        policy_decision=gated.decision, autonomy=level)

    approval_id = ""
    if gated.decision == REQUIRE_APPROVAL or level == "L2":
        gate = approvals.latest_for(conn, case_id, action_id) if case_id else None
        if gate is None or gate["state"] == "EXPIRED":
            created = approvals.request_approval(conn, case_id, action_id, user_id or "commander")
            return ExecutionResult(AWAITING, action_id, device_id,
                                   policy_decision=gated.decision, autonomy=level,
                                   approval_id=created["approval_id"],
                                   reasons=["approval requested; execution paused"])
        if gate["state"] == "DENIED":
            return _refused(action_id, device_id, ["human denied the approval"],
                            policy_decision=gated.decision, autonomy=level,
                            approval_id=gate["approval_id"])
        if gate["state"] != "APPROVED":
            return ExecutionResult(AWAITING, action_id, device_id,
                                   policy_decision=gated.decision, autonomy=level,
                                   approval_id=gate["approval_id"],
                                   reasons=[f"approval {gate['state'].lower()}; paused"])
        approval_id = gate["approval_id"]

    before = snapshot(device_id, estate)
    try:
        effect = apply_effect(estate, action_id, device_id, params or {})
    except (ValueError, LookupError) as e:
        return _refused(action_id, device_id, [f"effect failed: {e}"],
                        policy_decision=gated.decision, autonomy=level,
                        approval_id=approval_id)
    after = snapshot(device_id, estate)

    count = conn.execute("SELECT COUNT(*) AS n FROM remediation_runs").fetchone()["n"]
    run_id = f"RUN-{case_id or 'LOCAL'}-{action_id}-{count + 1}"
    conn.execute(
        "INSERT INTO remediation_runs(run_id, case_id, script_id, device_id, "
        "before_state, after_state, success) VALUES (?,?,?,?,?,?,?)",
        (run_id, case_id, action_id, device_id, before, after, 1))
    conn.commit()
    script_registry.record_execution(conn, action_id, True)
    if case_id:
        record_decision(conn, case_id, policy_in, gated)
    log_event(conn, AuditEvent(
        case_id=case_id, agent="execution_controller", event_type="execution",
        tool="execute_remote_action",
        sanitized_input=json.dumps({"action_id": action_id, "device_id": device_id}),
        sanitized_output=json.dumps({"run_id": run_id, "effect": effect}),
        decision=gated.decision, approval=approval_id, action=action_id, success=1))
    return ExecutionResult(EXECUTED, action_id, device_id, run_id,
                           gated.decision, level, approval_id, effect,
                           [f"policy {gated.decision}", f"autonomy {level}"])
