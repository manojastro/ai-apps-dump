"""Policy-as-Code engine (M12): deterministic ALLOW / DENY / REQUIRE_APPROVAL.

Pure function of (PolicyInput, registry rows). No LLM, no network, no clock
except the caller-supplied at_hour — same inputs always yield same decision.
Precedence: any DENY wins; else any REQUIRE_APPROVAL; else ALLOW.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any

from control_plane import registry as script_registry

ALLOW = "ALLOW"
DENY = "DENY"
REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

DENY_LIST = frozenset({
    "SCR-DISABLE-PROTECTION",  # endpoint protection off — never allowed
    "SCR-FIREWALL-DISABLE",
})

ALLOWED_DEVICE_GROUPS = frozenset({
    "corporate-laptop", "corporate-desktop", "lab-device",
})

KNOWN_ROLES = frozenset({
    "employee", "manager", "it", "support", "finance", "hr",
    "security", "payroll_admin", "admin",
})

BUSINESS_HOURS = range(8, 18)  # UTC; deterministic via at_hour


@dataclass(frozen=True)
class PolicyInput:
    user_id: str = ""
    user_role: str = "employee"
    device_id: str = ""
    device_group: str = "corporate-laptop"
    device_compliant: bool = True
    action_id: str = ""
    script_hash: str = ""
    environment: str = "prod"
    at_hour: int = 10


@dataclass
class CheckResult:
    name: str
    passed: bool  # hard pass/fail
    detail: str = ""
    approval_gate: bool = False  # True → soft fail = REQUIRE_APPROVAL, not DENY


@dataclass
class PolicyResult:
    decision: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def reasons(self) -> list[str]:
        return [f"{c.name}: {'PASS' if c.passed else 'FAIL'} {c.detail}".strip()
                for c in self.checks]


def evaluate(conn: sqlite3.Connection, policy: PolicyInput) -> PolicyResult:
    """Run the full gate in fixed order. Deterministic. No side effects."""
    checks: list[CheckResult] = []
    script = script_registry.lookup_script(conn, policy.action_id) if policy.action_id else None

    checks.append(CheckResult(
        "user authorized",
        policy.user_role in KNOWN_ROLES and bool(policy.user_id),
        f"role={policy.user_role}"))
    checks.append(CheckResult(
        "allowed device group",
        policy.device_group in ALLOWED_DEVICE_GROUPS,
        f"group={policy.device_group}"))
    checks.append(CheckResult(
        "device compliant", policy.device_compliant,
        "compliant" if policy.device_compliant else "NON-COMPLIANT"))
    checks.append(CheckResult(
        "approved script", script_registry.is_approved(script),
        f"action={policy.action_id}"))
    checks.append(CheckResult(
        "hash valid",
        script_registry.verify_hash(script or {}, policy.script_hash) if script else False,
        "match" if policy.script_hash else "registry-trusted"))
    checks.append(CheckResult(
        "deny-list", policy.action_id not in DENY_LIST,
        "CLEAR" if policy.action_id not in DENY_LIST else "LISTED"))

    risk = str((script or {}).get("risk", "UNKNOWN"))
    autonomy = str((script or {}).get("autonomy_level", "L1"))
    rollback = bool((script or {}).get("rollback_available", 0))
    checks.append(CheckResult("risk", risk not in ("CRITICAL", "UNKNOWN"), f"risk={risk}",
                              approval_gate=risk == "HIGH"))
    checks.append(CheckResult("autonomy", autonomy in ("L3", "L4"), f"autonomy={autonomy}",
                              approval_gate=autonomy in ("L1", "L2")))
    checks.append(CheckResult(
        "business hours", policy.at_hour in BUSINESS_HOURS or risk == "LOW",
        f"hour={policy.at_hour}",
        approval_gate=(policy.at_hour not in BUSINESS_HOURS and risk != "LOW")))
    checks.append(CheckResult(
        "rollback support", rollback or risk == "LOW",
        "available" if rollback else "none",
        approval_gate=(not rollback and risk not in ("LOW", "UNKNOWN"))))

    if any(not c.passed and not c.approval_gate for c in checks):
        decision = DENY
    elif any(not c.passed and c.approval_gate for c in checks):
        decision = REQUIRE_APPROVAL
    else:
        decision = ALLOW
    return PolicyResult(decision, checks)


def record_decision(conn: sqlite3.Connection, case_id: str,
                    policy: PolicyInput, result: PolicyResult) -> str:
    """Append the decision to policy_decisions (audit trail foundation, M19)."""
    decision_id = f"POL-{case_id}-{int(time.time() * 1000) % 100000:05d}" if case_id else \
        f"POL-LOCAL-{int(time.time() * 1000) % 100000:05d}"
    conn.execute(
        "INSERT INTO policy_decisions(decision_id, case_id, script_id, device_id, "
        "user_id, checks, decision) VALUES (?,?,?,?,?,?,?)",
        (decision_id, case_id, policy.action_id, policy.device_id, policy.user_id,
         json.dumps([{"name": c.name, "passed": c.passed, "detail": c.detail}
                     for c in result.checks]),
         result.decision))
    conn.commit()
    return decision_id
