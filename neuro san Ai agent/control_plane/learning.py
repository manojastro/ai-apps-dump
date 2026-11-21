"""Learning engine (M20): repeated resolutions → governed candidates.

Learning input is resolution snapshots (resolution_patterns), never chat
history. Candidates are FORCED to approval_state='candidate' — promotion
requires the M15 approval engine plus the M20 pipeline (simulate → security
→ policy → tests → human approval). AI never self-promotes.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from control_plane import registry as script_registry
from control_plane.policy import DENY_LIST

DEFAULT_MIN_OCCURRENCES = 3
DEFAULT_MIN_SUCCESS_RATE = 0.9


def record_resolution(conn: sqlite3.Connection, case_id: str, failure_signature: str,
                      evidence_pattern: list[str], root_cause: str, action_id: str,
                      policy_result: str = "", approval_state: str = "",
                      verification_passed: bool = False, success: bool = True,
                      reopen: bool = False, human_correction: str = "") -> str:
    """Snapshot one resolution for pattern detection. Returns pattern_id."""
    n = conn.execute("SELECT COUNT(*) AS n FROM resolution_patterns WHERE case_id=?",
                     (case_id,)).fetchone()["n"]
    pattern_id = f"PAT-{case_id}-{n + 1}"
    conn.execute(
        "INSERT INTO resolution_patterns(pattern_id, case_id, failure_signature, "
        "evidence_pattern, root_cause, action_id, script_id, policy_result, "
        "approval_state, verification, success, reopen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (pattern_id, case_id, failure_signature, json.dumps(evidence_pattern),
         root_cause, action_id, action_id, policy_result, approval_state,
         json.dumps({"passed": verification_passed}), int(success), int(reopen)))
    conn.commit()
    return pattern_id


def detect_candidates(conn: sqlite3.Connection, min_occurrences: int = DEFAULT_MIN_OCCURRENCES,
                      min_success_rate: float = DEFAULT_MIN_SUCCESS_RATE) -> list[dict[str, Any]]:
    """Signatures with repeated, successful, non-reopened, human-touched resolutions."""
    rows = conn.execute(
        "SELECT failure_signature, COUNT(*) AS total, "
        "SUM(CASE WHEN approval_state='APPROVED' THEN 1 ELSE 0 END) AS approved "
        "FROM resolution_patterns GROUP BY failure_signature").fetchall()
    candidates = []
    for row in rows:
        clean = conn.execute(
            "SELECT action_id, root_cause, COUNT(*) AS n FROM resolution_patterns "
            "WHERE failure_signature=? AND success=1 AND reopen=0 "
            "GROUP BY action_id, root_cause ORDER BY n DESC LIMIT 1",
            (row["failure_signature"],)).fetchone()
        if clean is None or clean["n"] < min_occurrences:
            continue
        rate = round(clean["n"] / row["total"], 3)
        if rate < min_success_rate or (row["approved"] or 0) < 1:
            continue
        candidates.append({"failure_signature": row["failure_signature"],
                           "occurrences": clean["n"], "success_rate": rate,
                           "action_id": clean["action_id"],
                           "root_cause": clean["root_cause"]})
    return candidates


def propose_candidate(conn: sqlite3.Connection, failure_signature: str, action_id: str,
                      root_cause: str = "", name: str = "",
                      workflow_id: str = "") -> dict[str, Any]:
    """Insert a candidate workflow. approval_state is ALWAYS 'candidate'."""
    if not workflow_id:
        n = conn.execute("SELECT COUNT(*) AS n FROM workflows WHERE workflow_id LIKE 'WF-CANDIDATE-%'").fetchone()["n"]
        workflow_id = f"WF-CANDIDATE-{n + 1:03d}"
    conn.execute(
        "INSERT OR IGNORE INTO workflows(workflow_id, name, failure_signature, root_cause_signature, "
        "action_id, autonomy_level, approval_state) VALUES (?,?,?,?,?,?,?)",
        (workflow_id, name or workflow_id, failure_signature, root_cause,
         action_id, "L1", "candidate"))
    conn.commit()
    row = conn.execute("SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,)).fetchone()
    return dict(row)


# action_id -> scratch demo device carrying a matching issue (deterministic).
_SIM_TARGET = {
    "SCR-018": "DEVICE_001", "SCR-CLEAR-TEMP": "DEVICE_001",
    "SCR-RESTART-APP": "DEVICE_001", "SCR-DISK-CLEANUP": "DEVICE_001",
    "SCR-VPN-RECONNECT": "DEVICE_002", "SCR-INSTALL": "DEVICE_003",
}


def promote_candidate(conn: sqlite3.Connection, workflow_id: str) -> dict[str, Any]:
    """Candidate → simulation → security → policy → tests → human approval → approved.

    First call requests human approval and raises awaiting-approval (never
    self-promotes). After a human approves, the second call runs the gauntlet
    and flips approval_state to approved at L1 (earned promotion via M15 later).
    """
    from control_plane import approvals
    from control_plane.policy import DENY, PolicyInput, evaluate

    row = conn.execute("SELECT * FROM workflows WHERE workflow_id=?",
                       (workflow_id,)).fetchone()
    if row is None:
        raise LookupError(f"workflow {workflow_id} not found")
    candidate = dict(row)
    if candidate["approval_state"] == "approved":
        return candidate
    if candidate["approval_state"] != "candidate":
        raise ValueError(f"workflow {workflow_id} is {candidate['approval_state']}")

    gate = approvals.latest_for(conn, "", workflow_id)
    if gate is None or gate["state"] != "APPROVED":
        approvals.request_approval(conn, "", workflow_id, "learning-agent")
        raise ValueError(f"awaiting human approval for {workflow_id} (never self-promotes)")

    action_id = candidate["action_id"]
    action = script_registry.get_approved_action(conn, action_id)
    if action is None:
        raise ValueError(f"action {action_id} not approved+intact; cannot promote")
    if action_id in DENY_LIST:
        raise ValueError(f"action {action_id} is deny-listed; cannot promote")

    # Simulation + workflow test: execute on a scratch device, verify fresh.
    from simulator.actions import apply_effect, snapshot
    from simulator.estate import generate_estate
    from control_plane.verification import capture_state, verify_remediation
    import json as _json
    scratch = generate_estate(seed=7, n=10)
    target = _SIM_TARGET.get(action_id, "DEVICE_003")
    before = _json.loads(snapshot(target, scratch))
    params = {"app": "Teams"} if action_id == "SCR-RESTART-APP" else (
        {"app": "VideoEditor"} if action_id == "SCR-INSTALL" else {})
    apply_effect(scratch, action_id, target, params)
    after = capture_state(scratch, target, action_id)
    verdict = verify_remediation(before, after, action_id, params)
    if not verdict.passed:
        raise ValueError(f"workflow test failed for {workflow_id}: {verdict.failed}")

    # Policy shape: the registered action must not DENY a compliant request.
    decision = evaluate(conn, PolicyInput(
        user_id="learning", user_role="it", device_group="corporate-laptop",
        device_compliant=True, action_id=action_id)).decision
    if decision == DENY:
        raise ValueError(f"policy DENYs {action_id}; cannot promote")

    from database.models import utcnow
    conn.execute("UPDATE workflows SET approval_state='approved', last_updated=? "
                 "WHERE workflow_id=?", (utcnow(), workflow_id))
    conn.commit()
    snapshot_version(conn, workflow_id)
    return dict(conn.execute("SELECT * FROM workflows WHERE workflow_id=?",
                             (workflow_id,)).fetchone())


def get_workflow(conn: sqlite3.Connection, workflow_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM workflows WHERE workflow_id=?",
                       (workflow_id,)).fetchone()
    if row is None:
        raise LookupError(f"workflow {workflow_id} not found")
    return dict(row)


def snapshot_version(conn: sqlite3.Connection, workflow_id: str) -> str:
    """Freeze the current definition into workflow_versions (audit of change)."""
    import json as _json
    from database.models import utcnow
    workflow = get_workflow(conn, workflow_id)
    n = conn.execute("SELECT COUNT(*) AS n FROM workflow_versions WHERE workflow_id=?",
                     (workflow_id,)).fetchone()["n"]
    version_id = f"{workflow_id}-v{n + 1}"
    conn.execute(
        "INSERT INTO workflow_versions(version_id, workflow_id, version, definition) "
        "VALUES (?,?,?,?)",
        (version_id, workflow_id, workflow.get("version", "1.0"),
         _json.dumps({"action_id": workflow.get("action_id"),
                      "autonomy_level": workflow.get("autonomy_level"),
                      "approval_state": workflow.get("approval_state"),
                      "failure_signature": workflow.get("failure_signature")})))
    conn.commit()
    return version_id


def record_workflow_run(conn: sqlite3.Connection, workflow_id: str, case_id: str,
                        policy_decision: str, approval_state: str,
                        success: bool) -> str:
    """Account one reuse + refresh registry counters/rate. Returns run_id."""
    from database.models import utcnow
    get_workflow(conn, workflow_id)  # raises on unknown
    n = conn.execute("SELECT COUNT(*) AS n FROM workflow_runs WHERE workflow_id=?",
                     (workflow_id,)).fetchone()["n"]
    run_id = f"WFR-{workflow_id}-{n + 1}"
    conn.execute(
        "INSERT INTO workflow_runs(run_id, workflow_id, case_id, policy_decision, "
        "approval_state, success) VALUES (?,?,?,?,?,?)",
        (run_id, workflow_id, case_id, policy_decision, approval_state, int(success)))
    workflow = get_workflow(conn, workflow_id)
    execs = int(workflow.get("execution_count", 0) or 0) + 1
    wins = int(workflow.get("success_count", 0) or 0) + (1 if success else 0)
    fails = int(workflow.get("failure_count", 0) or 0) + (0 if success else 1)
    rate = round(100 * wins / execs, 1)
    conn.execute("UPDATE workflows SET execution_count=?, success_count=?, "
                 "failure_count=?, success_rate=?, last_updated=? WHERE workflow_id=?",
                 (execs, wins, fails, rate, utcnow(), workflow_id))
    conn.commit()
    return run_id


def recheck_workflow(conn: sqlite3.Connection, workflow_id: str, user_id: str,
                     user_role: str = "employee", device_id: str = "",
                     device_group: str = "corporate-laptop",
                     device_compliant: bool = True, at_hour: int = 10):
    """Fresh policy verdict for the workflow's action on every reuse (M21 rule)."""
    from control_plane.policy import PolicyInput, evaluate
    workflow = get_workflow(conn, workflow_id)
    return evaluate(conn, PolicyInput(
        user_id=user_id, user_role=user_role, device_id=device_id,
        device_group=device_group, device_compliant=device_compliant,
        action_id=workflow.get("action_id", ""), at_hour=at_hour))


def sync_autonomy(conn: sqlite3.Connection, workflow_id: str) -> dict[str, Any]:
    """Apply the M15 engine to a workflow (promotion AND demotion)."""
    from control_plane.autonomy import apply_autonomy
    return apply_autonomy(conn, "workflow", workflow_id)
