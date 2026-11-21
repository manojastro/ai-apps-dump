from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentStatus(str, Enum):
    detected = "DETECTED"
    awaiting_approval = "AWAITING_APPROVAL"
    approved = "APPROVED"
    rejected = "REJECTED"
    executing = "EXECUTING"
    execution_failed = "EXECUTION_FAILED"
    remediated = "REMEDIATED"
    validated = "VALIDATED"
    validation_failed = "VALIDATION_FAILED"


class RiskLevel(str, Enum):
    info = "INFO"
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


class Evidence(BaseModel):
    evidence_id: str
    kind: str
    source: str
    claim: str
    value: Any
    observed_at: datetime = Field(default_factory=utc_now)


class Hypothesis(BaseModel):
    cause: str
    confidence: float = Field(ge=0, le=1)
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str] = Field(default_factory=list)


class ActionProposal(BaseModel):
    action_id: str
    action_type: str
    summary: str
    parameters: dict[str, Any]
    risk: RiskLevel
    blast_radius: str
    reversibility: str
    expected_benefit: str
    confidence: float = Field(ge=0, le=1)
    required_approval: bool = True
    rollback_plan: str


class RCAResult(BaseModel):
    incident_id: str
    scenario: str
    probable_root_cause: str
    confidence: float = Field(ge=0, le=1)
    hypotheses: list[Hypothesis]
    evidence: list[Evidence]
    recommended_actions: list[ActionProposal]
    reasoning_mode: str = "deterministic-mock"


class ValidationResult(BaseModel):
    incident_id: str
    passed: bool
    checks: dict[str, bool]
    before: dict[str, float | int | str]
    after: dict[str, float | int | str]
    summary: str
    validated_at: datetime = Field(default_factory=utc_now)


class ApprovalRequest(BaseModel):
    approved: bool
    approved_by: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=3, max_length=500)


class ScenarioInfo(BaseModel):
    name: str
    description: str
    ground_truth_root_cause: str


class IncidentSummary(BaseModel):
    incident_id: str
    scenario: str
    status: IncidentStatus
    root_cause: str
    confidence: float
    created_at: datetime


class EvaluationSummary(BaseModel):
    total: int
    correct: int
    rca_accuracy: float
    mean_confidence: float
    mean_diagnosis_ms: float
    consumer_lag_detection_rate: float
    mean_mttd_ms: float
    mean_mttr_ms: float
