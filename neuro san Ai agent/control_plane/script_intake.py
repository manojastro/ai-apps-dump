"""AI-generated script intake (M14): propose → validate → review → register.

Nothing proposed here can execute: registration requires every automated
stage to pass AND a human approval. Stage order mirrors the spec pipeline:
syntax → forbidden-command scan → secret detection → privilege analysis →
sandbox simulation → policy validation → risk classification → human review
→ version/hash → registry.
"""

from __future__ import annotations

import copy
import json
import re
import sqlite3
from typing import Any

from common.redaction import scan_prompt_for_secrets
from control_plane import registry as script_registry

# Primitive -> inherent risk. Only these may appear in proposals (allowlist).
PRIMITIVE_RISK = {
    "clear_teams_cache": "LOW", "restart_app": "LOW", "clear_temp": "LOW",
    "disk_cleanup": "LOW", "collect_logs": "LOW", "reconnect_vpn": "MEDIUM",
    "refresh_token": "MEDIUM", "install_app": "MEDIUM", "restart_device": "MEDIUM",
    "firewall_change": "HIGH", "disable_protection": "CRITICAL",
}

# Claimed risk must cover every primitive; autonomy capped per risk.
_RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
_MAX_AUTONOMY = {"LOW": "L3", "MEDIUM": "L2", "HIGH": "L1", "CRITICAL": "L0"}

_FORBIDDEN = (
    r"disable.{0,12}protect", r"firewall.{0,12}(disable|off)",
    r"mimikatz", r"pass.the.hash", r"reverse.?shell", r"exfiltrat",
    r"rm\s+-rf", r"format\s+[a-z]:", r"powershell\s+-(enc|e)\b",
    r"curl.{0,40}\|\s*(sh|bash)", r"invoke-expression", r"bloodhound",
)

_SCRIPT_ID_RE = re.compile(r"^SCR-[A-Z0-9-]{3,24}$")
_VERSION_RE = re.compile(r"^\d+\.\d+$")


def _finding(stage: str, passed: bool, detail: str = "") -> dict[str, Any]:
    return {"stage": stage, "passed": passed, "detail": detail}


def propose(conn: sqlite3.Connection, proposal_id: str, script_id: str, name: str,
            description: str = "", platform: str = "windows",
            primitives: list[str] | None = None, risk_claimed: str = "LOW",
            autonomy_claimed: str = "L3", rollback_available: bool = False,
            groups: list[str] | None = None, owner: str = "") -> dict[str, Any]:
    """Store a proposal. No validation yet (status=proposed). Never executes."""
    if script_registry.lookup_script(conn, script_id) is not None:
        raise ValueError(f"script_id {script_id} already registered")
    if not _SCRIPT_ID_RE.match(script_id):
        raise ValueError(f"script_id {script_id} must match SCR-XXXX")
    conn.execute(
        "INSERT INTO script_proposals(proposal_id, script_id, name, description, "
        "platform, primitives, risk_claimed, autonomy_claimed, rollback_available, "
        "supported_device_groups, owner) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (proposal_id, script_id, name, description, platform,
         json.dumps(primitives or []), risk_claimed, autonomy_claimed,
         1 if rollback_available else 0, json.dumps(groups or ["corporate-laptop"]),
         owner))
    conn.commit()
    return get_proposal(conn, proposal_id)


def get_proposal(conn: sqlite3.Connection, proposal_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM script_proposals WHERE proposal_id=?",
                       (proposal_id,)).fetchone()
    if row is None:
        raise LookupError(f"proposal {proposal_id} not found")
    return dict(row)


def _stage_syntax(proposal: dict[str, Any]) -> dict[str, Any]:
    problems = []
    if not proposal["name"].strip():
        problems.append("name required")
    try:
        primitives = json.loads(proposal["primitives"])
    except (TypeError, ValueError):
        return _finding("syntax", False, "primitives must be a JSON list")
    if not isinstance(primitives, list) or not primitives:
        problems.append("at least one primitive required")
    unknown = [p for p in primitives if p not in PRIMITIVE_RISK]
    if unknown:
        problems.append(f"unknown primitives: {sorted(unknown)}")
    try:
        groups = json.loads(proposal["supported_device_groups"])
    except (TypeError, ValueError):
        return _finding("syntax", False, "supported_device_groups must be JSON")
    if not isinstance(groups, list) or not groups:
        problems.append("at least one device group required")
    if proposal["risk_claimed"] not in _RISK_ORDER:
        problems.append(f"bad risk_claimed {proposal['risk_claimed']}")
    if proposal["autonomy_claimed"] not in ("L0", "L1", "L2", "L3", "L4"):
        problems.append(f"bad autonomy_claimed {proposal['autonomy_claimed']}")
    return _finding("syntax", not problems, "; ".join(problems))


def _stage_forbidden(proposal: dict[str, Any]) -> dict[str, Any]:
    blob = f"{proposal['name']} {proposal['description']} {' '.join(json.loads(proposal['primitives']))}"
    hits = sorted({pat for pat in _FORBIDDEN if re.search(pat, blob, re.IGNORECASE)})
    return _finding("forbidden-command scan", not hits,
                    f"matched: {hits}" if hits else "clear")


def _stage_secrets(proposal: dict[str, Any]) -> dict[str, Any]:
    blob = f"{proposal['name']} {proposal['description']}"
    hits = scan_prompt_for_secrets(blob)
    return _finding("secret detection", not hits,
                    f"secret shapes: {hits}" if hits else "clear")


def _stage_privilege(proposal: dict[str, Any]) -> dict[str, Any]:
    claimed, risk = proposal["autonomy_claimed"], proposal["risk_claimed"]
    if claimed == "L4":
        return _finding("privilege analysis", False, "L4 is earned (M15), never granted at intake")
    allowed = [f"L{i}" for i in range(int(_MAX_AUTONOMY[risk][1:]) + 1)]
    if claimed not in allowed:
        return _finding("privilege analysis", False,
                        f"{claimed} exceeds {risk} cap {_MAX_AUTONOMY[risk]}")
    return _finding("privilege analysis", True, f"{claimed} within {risk} cap")


def _stage_sandbox(proposal: dict[str, Any]) -> dict[str, Any]:
    """Dry-run primitives against a scratch estate-device copy (no mutation)."""
    from simulator.estate import EstateDevice, EstateProcess, EstateSoftware
    primitives = json.loads(proposal["primitives"])
    scratch = EstateDevice(
        device_id="SANDBOX", processes=[EstateProcess("Teams", 4500.0, 30.0)],
        software=[EstateSoftware("APP_TEAMS", "Teams", "3.8.4", False)])
    before = copy.deepcopy(scratch)
    effects = []
    for primitive in primitives:
        if primitive == "clear_teams_cache":
            for proc in scratch.processes:
                if proc.name == "Teams":
                    proc.mem_mb = 640.0
            effects.append("teams memory 4500->640MB (simulated)")
        elif primitive == "restart_app":
            effects.append("app restarted (simulated)")
        elif primitive in ("reconnect_vpn", "refresh_token", "install_app",
                           "restart_device", "clear_temp", "disk_cleanup",
                           "collect_logs", "firewall_change", "disable_protection"):
            effects.append(f"{primitive} acknowledged (simulated)")
        else:  # pragma: no cover - syntax stage rejects unknown first
            return _finding("sandbox simulation", False, f"unknown {primitive}")
    assert before.processes[0].mem_mb == 4500.0  # scratch only, source untouched
    return _finding("sandbox simulation", True, "; ".join(effects))


def _stage_policy(conn: sqlite3.Connection, proposal: dict[str, Any]) -> dict[str, Any]:
    """Stage the proposal as a transient registry row and run the real gate."""
    from control_plane.policy import DENY, PolicyInput, evaluate
    conn.execute("SAVEPOINT intake_policy")
    try:
        # Stage as post-approval state: review grants approval; this stage
        # tests the remaining gate shape (role/group/compliance/deny/risk/...).
        conn.execute(
            "INSERT INTO scripts(script_id, name, risk, autonomy_level, "
            "rollback_available, hash, approved) VALUES (?,?,?,?,?,?,?)",
            ("STAGING-INTAKE", proposal["name"], proposal["risk_claimed"],
             proposal["autonomy_claimed"], proposal["rollback_available"],
             "staging", 1))
        decision = evaluate(conn, PolicyInput(
            user_id="intake", user_role="it", device_group="corporate-laptop",
            device_compliant=True, action_id="STAGING-INTAKE")).decision
    finally:
        conn.execute("ROLLBACK TO SAVEPOINT intake_policy")
        conn.execute("RELEASE SAVEPOINT intake_policy")
    if decision == DENY:
        return _finding("policy validation", False, "gate returns DENY for staging row")
    return _finding("policy validation", True, f"gate returns {decision}")


def _stage_risk(proposal: dict[str, Any]) -> dict[str, Any]:
    primitives = json.loads(proposal["primitives"])
    computed = max((PRIMITIVE_RISK[p] for p in primitives),
                   key=_RISK_ORDER.index, default="LOW")
    if _RISK_ORDER.index(proposal["risk_claimed"]) < _RISK_ORDER.index(computed):
        return _finding("risk classification", False,
                        f"claimed {proposal['risk_claimed']} below computed {computed}")
    return _finding("risk classification", True, f"computed={computed}",
                    )


def validate_proposal(conn: sqlite3.Connection, proposal_id: str) -> dict[str, Any]:
    """Run all automated stages. status=validated (all pass) or denied."""
    proposal = get_proposal(conn, proposal_id)
    stages = [_stage_syntax(proposal)]
    if stages[0]["passed"]:
        stages += [_stage_forbidden(proposal), _stage_secrets(proposal),
                   _stage_privilege(proposal), _stage_sandbox(proposal),
                   _stage_policy(conn, proposal), _stage_risk(proposal)]
    else:
        stages += [_finding(s, False, "skipped: syntax failed")
                   for s in ("forbidden-command scan", "secret detection",
                             "privilege analysis", "sandbox simulation",
                             "policy validation", "risk classification")]
    passed = all(s["passed"] for s in stages)
    computed = next((s["detail"].split("=")[1] for s in stages
                     if s["stage"] == "risk classification" and s["passed"]), "")
    conn.execute(
        "UPDATE script_proposals SET findings=?, risk_computed=?, status=? "
        "WHERE proposal_id=?",
        (json.dumps(stages), computed, "validated" if passed else "denied",
         proposal_id))
    conn.commit()
    return get_proposal(conn, proposal_id)


def request_review(conn: sqlite3.Connection, proposal_id: str,
                   requested_by: str = "learning-agent") -> dict[str, Any]:
    """Validated proposals enter human review (approvals row PENDING)."""
    proposal = get_proposal(conn, proposal_id)
    if proposal["status"] != "validated":
        raise ValueError(f"proposal {proposal_id} is {proposal['status']}, not validated")
    approval_id = f"APR-{proposal_id}"
    conn.execute(
        "INSERT OR IGNORE INTO approvals(approval_id, case_id, script_id, requested_by) "
        "VALUES (?,?,?,?)", (approval_id, "", proposal["script_id"], requested_by))
    conn.execute("UPDATE script_proposals SET status='in_review' WHERE proposal_id=?",
                 (proposal_id,))
    conn.commit()
    return get_proposal(conn, proposal_id)


def approve_review(conn: sqlite3.Connection, proposal_id: str,
                   approver: str) -> dict[str, Any]:
    """Human approval → version/hash → registry. Only path to execution."""
    from database.models import utcnow
    proposal = get_proposal(conn, proposal_id)
    if proposal["status"] != "in_review":
        raise ValueError(f"proposal {proposal_id} is {proposal['status']}, not in_review")
    primitives = json.loads(proposal["primitives"])
    script_id, version = proposal["script_id"], "1.0"
    digest = script_registry.canonical_hash(script_id, version, proposal["platform"],
                                            proposal["name"])
    conn.execute(
        "INSERT INTO scripts(script_id, name, description, version, hash, owner, "
        "platform, supported_device_groups, risk, approved, approval_timestamp, "
        "approved_by, rollback_available, autonomy_level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (script_id, proposal["name"], proposal["description"], version, digest,
         proposal["owner"], proposal["platform"], proposal["supported_device_groups"],
         proposal["risk_claimed"], 1, utcnow(), approver,
         proposal["rollback_available"], proposal["autonomy_granted"]
         or proposal["autonomy_claimed"]))
    conn.execute(
        "INSERT INTO script_versions(version_id, script_id, version, hash, content_ref, "
        "approved_by) VALUES (?,?,?,?,?,?)",
        (f"{script_id}-v1", script_id, version, digest, json.dumps(primitives), approver))
    conn.execute(
        "UPDATE approvals SET state='APPROVED', approver=?, decided_at=? "
        "WHERE approval_id=?", (approver, utcnow(), f"APR-{proposal_id}"))
    conn.execute(
        "UPDATE script_proposals SET status='registered', decided_at=?, decided_by=? "
        "WHERE proposal_id=?", (utcnow(), approver, proposal_id))
    conn.commit()
    return get_proposal(conn, proposal_id)


def reject_review(conn: sqlite3.Connection, proposal_id: str,
                  approver: str, reason: str = "") -> dict[str, Any]:
    """Human rejection. The proposal can never execute."""
    from database.models import utcnow
    proposal = get_proposal(conn, proposal_id)
    if proposal["status"] != "in_review":
        raise ValueError(f"proposal {proposal_id} is {proposal['status']}, not in_review")
    conn.execute("UPDATE approvals SET state='DENIED', approver=?, decided_at=? "
                 "WHERE approval_id=?", (approver, utcnow(), f"APR-{proposal_id}"))
    conn.execute("UPDATE script_proposals SET status='denied', decided_at=?, decided_by=? "
                 "WHERE proposal_id=?", (utcnow(), f"{approver}: {reason}", proposal_id))
    conn.commit()
    return get_proposal(conn, proposal_id)
