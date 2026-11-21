from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field, field_validator


class RiskTier(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class IncidentStatus(StrEnum):
    DETECTED = "DETECTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    EXECUTING = "EXECUTING"
    RESOLVED = "RESOLVED"
    ROLLED_BACK = "ROLLED_BACK"
    ESCALATED = "ESCALATED"


class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class IncidentCreate(BaseModel):
    scenario: str = Field(min_length=2, max_length=80)
    force_verification_failure: bool = False


class ApprovalRequest(BaseModel):
    decision: ApprovalDecision
    comment: str = Field(default="", max_length=500)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str) -> str:
        return value.strip()


class Scenario(BaseModel):
    id: str
    title: str
    signal: dict[str, str]
    diagnosis: str
    runbook_id: str
    action: str
    resource_kind: str
    resource: str
    parameters: dict[str, Any]
    expected_risk: RiskTier
    recovery_criterion: str
    allowed: bool = True


class PolicyDecision(BaseModel):
    allowed: bool
    risk_tier: RiskTier
    approval_required: bool
    reasons: list[str]


class WorkflowState(TypedDict, total=False):
    incident_id: str
    scenario: dict[str, Any]
    status: str
    evidence: list[dict[str, Any]]
    runbook: dict[str, Any]
    hypotheses: list[dict[str, Any]]
    plan: dict[str, Any]
    policy: dict[str, Any]
    approval: dict[str, Any] | None
    execution: dict[str, Any] | None
    verification: dict[str, Any] | None
    rollback: dict[str, Any] | None
    trace: list[str]
    outcome: str
    error: str | None


class AuthPrincipal(BaseModel):
    subject: str
    role: Literal["viewer", "operator", "admin"]

