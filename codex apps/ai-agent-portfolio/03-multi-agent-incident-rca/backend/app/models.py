from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class Role(str, Enum):
    viewer = "viewer"
    investigator = "investigator"
    admin = "admin"


class IncidentStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    complete = "complete"
    failed = "failed"


class EvidenceSource(str, Enum):
    metrics = "metrics"
    logs = "logs"
    changes = "changes"
    tickets = "tickets"


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    service: str = Field(min_length=2, max_length=80)
    scenario: str = Field(default="bad-deployment", max_length=80)
    severity: str = Field(default="SEV-2", pattern=r"^SEV-[1-4]$")
    alert_summary: str = Field(default="Synthetic alert", max_length=500)


class Incident(BaseModel):
    id: str
    title: str
    service: str
    scenario: str
    severity: str
    alert_summary: str
    status: IncidentStatus = IncidentStatus.open
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Evidence(BaseModel):
    """An immutable, content-addressed observation returned by a read-only tool."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^EV-[A-F0-9]{12}$")
    incident_id: str
    source: EvidenceSource
    source_ref: str
    observed_at: datetime
    service: str
    summary: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    redacted: bool = False


class TimelineEvent(BaseModel):
    timestamp: datetime
    title: str
    detail: str
    evidence_ids: list[str] = Field(min_length=1)


class Hypothesis(BaseModel):
    id: str
    rank: int = Field(ge=1)
    category: str
    component: str
    statement: str
    confidence: float = Field(ge=0, le=1)
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    rationale: str
    rejected: bool = False


class CriticResult(BaseModel):
    challenged_hypothesis_id: str
    challenge: str
    evidence_ids: list[str]
    overturned: bool
    replacement_hypothesis_id: str | None = None


class CitedClaim(BaseModel):
    text: str = Field(min_length=2, max_length=1000)
    evidence_ids: list[str] = Field(min_length=1)

    @field_validator("evidence_ids")
    @classmethod
    def unique_evidence_ids(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("duplicate evidence IDs are not allowed")
        return value


class RCASection(BaseModel):
    title: str
    claims: list[CitedClaim]


class RCA(BaseModel):
    incident_id: str
    sections: list[RCASection]
    confidence: float = Field(ge=0, le=1)
    unresolved_questions: list[str]
    generated_at: datetime = Field(default_factory=utc_now)
    markdown: str


class WorkerRun(BaseModel):
    worker: str
    tool: str
    status: str
    latency_ms: float
    evidence_count: int
    error: str | None = None


class Investigation(BaseModel):
    incident: Incident
    plan: list[str]
    worker_runs: list[WorkerRun]
    evidence: list[Evidence]
    timeline: list[TimelineEvent]
    hypotheses: list[Hypothesis]
    critic: CriticResult
    rca: RCA
    duration_ms: float
    token_usage: int
    estimated_cost_usd: float


class EvaluationSummary(BaseModel):
    total_cases: int
    exact_root_cause_accuracy: float
    category_accuracy: float
    evidence_citation_coverage: float
    unsupported_claim_rate: float
    critic_overturn_rate: float
    average_duration_ms: float
    accuracy_by_category: dict[str, float]
    passed: bool

