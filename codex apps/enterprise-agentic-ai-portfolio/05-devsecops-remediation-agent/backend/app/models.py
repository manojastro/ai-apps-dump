from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Severity(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


class WorkflowStatus(str, Enum):
    awaiting_approval = "AWAITING_APPROVAL"
    reapproval_required = "REAPPROVAL_REQUIRED"
    approved = "APPROVED"
    rejected = "REJECTED"
    fixed = "FIXED"
    validated = "VALIDATED"
    validation_failed = "VALIDATION_FAILED"


class Evidence(BaseModel):
    evidence_id: str
    source: str
    claim: str
    value: Any
    line: int | None = None


class SecurityFinding(BaseModel):
    finding_id: str
    rule_id: str
    cwe: str
    title: str
    severity: Severity
    file: str
    line: int
    evidence: list[Evidence]


class ExploitabilityAssessment(BaseModel):
    classification: str
    score: float = Field(ge=0, le=1)
    reachable: bool
    attacker_controlled_input: bool
    preconditions: list[str]
    rationale: str
    evidence_ids: list[str]


class RemediationPlan(BaseModel):
    action_id: str
    summary: str
    patch_preview: str
    patch_sha256: str
    fixed_source_sha256: str
    risk: Severity
    blast_radius: str
    reversibility: str
    expected_benefit: str
    confidence: float = Field(ge=0, le=1)
    required_approval: bool = True
    rollback_plan: str


class ReleaseRisk(BaseModel):
    score: int = Field(ge=0, le=100)
    decision: str
    reasons: list[str]


class InvestigationResult(BaseModel):
    incident_id: str
    scenario: str
    probable_root_cause: str
    confidence: float = Field(ge=0, le=1)
    finding: SecurityFinding
    exploitability: ExploitabilityAssessment
    remediation: RemediationPlan
    release_risk_before: ReleaseRisk
    reasoning_mode: str = "deterministic-mock"


class ValidationResult(BaseModel):
    incident_id: str
    passed: bool
    checks: dict[str, bool]
    findings_before: int
    findings_after: int
    source_hash_before: str
    source_hash_after: str
    release_risk_after: ReleaseRisk
    summary: str
    validated_at: datetime = Field(default_factory=utc_now)


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    reason: str = Field(min_length=3, max_length=500)


class ScenarioInfo(BaseModel):
    name: str
    title: str
    cwe: str
    description: str


class EvaluationSummary(BaseModel):
    investigations: int
    true_findings: int
    finding_validity: float
    exploitability_accuracy: float
    attempted_remediations: int
    successful_remediations: int
    remediation_success_rate: float
    security_regressions: int
    test_regressions: int


class AgentDefinition(BaseModel):
    name: str
    responsibility: str
    inputs: list[str]
    outputs: list[str]
    tools: list[str]
    permission_boundary: str
    failure_behavior: str
