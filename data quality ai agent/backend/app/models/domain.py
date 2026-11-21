from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def now() -> str:
    return datetime.now(UTC).isoformat()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Scenario(StrEnum):
    SCHEMA_DRIFT = "schema_drift"
    NULL_SPIKE = "null_spike"
    DUPLICATES = "duplicates"
    TRANSFORMATION = "transformation_regression"
    DEPENDENCY = "dependency_failure"


class Status(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING_FOR_HUMAN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class Risk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Operation(StrEnum):
    MAP_CUSTOMER = "map_customer_id"
    RESTORE_CUSTOMER = "restore_customer_from_master"
    DEDUPLICATE = "deduplicate_transactions"
    CORRECT_AMOUNT = "correct_amount_units"
    RETRY_DEPENDENCY = "bounded_dependency_retry"
    CONFIGURATION = "change_configuration"
    SCHEMA = "schema_mutation"
    DELETE = "delete_data"
    REWRITE = "rewrite_history"


class IncidentInput(Contract):
    scenario: Scenario = Scenario.SCHEMA_DRIFT
    pipeline_id: Literal["orders_daily"] = "orders_daily"
    environment: Literal["local", "staging"] = "local"
    title: str = Field(default="Pipeline recovery investigation", min_length=1, max_length=160)
    triggered_by: str = Field(default="local-monitor", min_length=1, max_length=80)
    demo_force_first_fix_fail: bool | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=10)


class Incident(IncidentInput):
    id: str
    created_at: str = Field(default_factory=now)
    severity: Literal["critical", "warning"] = "critical"


class Evidence(Contract):
    id: str
    branch: str
    summary: str
    facts: dict[str, Any]
    source: str
    observed_at: str = Field(default_factory=now)


class Hypothesis(Contract):
    cause: str
    summary: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    contradicting_evidence: list[str] = Field(default_factory=list)


class Candidate(Contract):
    summary: str = Field(min_length=1, max_length=1000)
    operations: list[Operation] = Field(default_factory=list, max_length=8)
    amount_divisor: Literal[1, 100] | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class ReplayResult(Contract):
    rows: list[dict[str, Any]]
    completed: bool
    errors: list[str] = Field(default_factory=list)
    dependency_calls: int = 0
    applied_operations: list[Operation] = Field(default_factory=list)


class ValidationResult(Contract):
    validator: str
    status: Literal["PASS", "FAIL"]
    expected: Any
    actual: Any
    evidence: str
    severity: Literal["critical", "warning"] = "critical"


class Verification(Contract):
    decision: Literal["APPROVE", "REJECT", "NEEDS_HUMAN"]
    confidence: float = Field(ge=0, le=1)
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_checks: list[str] = Field(default_factory=list)
    risk_findings: list[str] = Field(default_factory=list)
    reason_summary: str


class ApprovalInput(Contract):
    actor: str = Field(min_length=1, max_length=80)
    comment: str = Field(min_length=1, max_length=2000)


class Approval(ApprovalInput):
    approved: bool


class Attempt(Contract):
    number: int
    candidate: Candidate
    validations: list[ValidationResult]
    status: Literal["PASSED", "REJECTED"]
    feedback: list[str]


class KnowledgeDocument(Contract):
    id: str
    title: str
    content: str
    pipeline_id: str = "orders_daily"
    source_type: str = "runbook"
    environment: str = "local"
    service: str = "orders"
    document_type: str = "procedure"
    version: str = "1"
    created_at: str = "2026-09-01T00:00:00+00:00"
    score: float = 0
