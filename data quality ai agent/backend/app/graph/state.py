import operator
from typing import Annotated, Any, TypedDict

from app.models.domain import (
    Attempt,
    Candidate,
    Evidence,
    Hypothesis,
    Incident,
    KnowledgeDocument,
    ReplayResult,
    Risk,
    Status,
    ValidationResult,
    Verification,
)
from simulator.pipeline import Fixture


class RecoveryState(TypedDict, total=False):
    incident_id: str
    incident: Incident
    pipeline_metadata: dict[str, Any]
    fixture: Fixture
    retrieved_context: list[KnowledgeDocument]
    evidence: Annotated[list[Evidence], operator.add]
    aggregated_evidence: list[Evidence]
    root_cause_hypotheses: list[Hypothesis]
    selected_hypothesis: Hypothesis
    confidence: float
    evidence_round: int
    candidate_remediation: Candidate
    attempt_number: int
    max_attempts: int
    force_first_fail: bool
    attempt_history: Annotated[list[Attempt], operator.add]
    sandbox_result: Candidate
    replay_result: ReplayResult
    validation_results: list[ValidationResult]
    validation_feedback: list[str]
    verification_result: Verification
    risk_level: Risk
    approval_status: str
    human_decision: dict[str, Any]
    final_remediation: dict[str, Any]
    final_status: Status
    failure_reason: str
    cost_metrics: dict[str, Any]
    latency_metrics: Annotated[list[dict[str, Any]], operator.add]
    audit_events: Annotated[list[dict[str, Any]], operator.add]
