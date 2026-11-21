"""Core domain models (M2). Boring dataclasses mirroring database/schema.sql.

IDs use aliases (USER_001, DEVICE_001) — never real hostnames/users (D006).
JSON-ish columns are TEXT holding JSON arrays/objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class User:
    user_id: str
    display_name: str = ""
    role: str = "employee"
    department: str = ""
    entitlements: str = "[]"


@dataclass(frozen=True)
class Device:
    device_id: str
    user_id: str = ""
    os: str = ""
    department: str = ""
    device_group: str = ""
    compliance_state: str = "unknown"
    risk_attributes: str = "{}"


@dataclass(frozen=True)
class Case:
    case_id: str
    user_id: str = ""
    device_id: str = ""
    request_text: str = ""
    request_type: str = "technical"
    status: str = "open"


@dataclass(frozen=True)
class Incident:
    incident_id: str
    case_id: str = ""
    state: str = "New"
    priority: str = "3"
    short_description: str = ""
    servicenow_sys_id: str = ""


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    case_id: str
    source_system: str = ""
    tool: str = ""
    entity: str = ""
    measurement: str = ""
    value: str = ""
    unit: str = ""
    confidence: float = 1.0
    raw_reference: str = ""
    sanitized_summary: str = ""
    timestamp: str = field(default_factory=utcnow)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    case_id: str
    title: str
    confidence: float = 0.0
    status: str = "INSUFFICIENT"  # SUPPORTED | REJECTED | INSUFFICIENT
    rank: int = 0
    evidence_ids: str = "[]"


@dataclass(frozen=True)
class Script:
    script_id: str
    name: str = ""
    version: str = "1.0"
    hash: str = ""
    risk: str = "LOW"
    approved: int = 0
    autonomy_level: str = "L2"
    rollback_available: int = 0
    success_rate: float = 0.0


@dataclass(frozen=True)
class PolicyDecision:
    decision_id: str
    case_id: str = ""
    decision: str = "DENY"  # ALLOW | DENY | REQUIRE_APPROVAL
    checks: str = "{}"


@dataclass(frozen=True)
class Approval:
    approval_id: str
    case_id: str = ""
    state: str = "PENDING"  # PENDING | APPROVED | DENIED | EXPIRED


@dataclass(frozen=True)
class RemediationRun:
    run_id: str
    case_id: str = ""
    script_id: str = ""
    device_id: str = ""
    success: int = 0


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    name: str = ""
    version: str = "1.0"
    failure_signature: str = ""
    action_id: str = ""
    autonomy_level: str = "L1"
    approval_state: str = "candidate"  # candidate | approved | demoted
    success_rate: float = 0.0


@dataclass(frozen=True)
class FleetMatch:
    match_id: str
    case_id: str = ""
    device_id: str = ""
    match_state: str = "AT_RISK"  # AFFECTED | EARLY | AT_RISK
    policy_decision: str = "DENY"
    verified: int = 0


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    domain: str = ""
    title: str = ""
    allowed_roles: str = "[]"


@dataclass(frozen=True)
class AuditEvent:
    case_id: str = ""
    agent: str = ""
    event_type: str = ""
    tool: str = ""
    sanitized_input: str = ""
    sanitized_output: str = ""
    evidence_ids: str = "[]"
    decision: str = ""
    policy_result: str = ""
    risk: str = ""
    approval: str = ""
    action: str = ""
    duration_ms: int = 0
    success: int = 1
    timestamp: str = field(default_factory=utcnow)
