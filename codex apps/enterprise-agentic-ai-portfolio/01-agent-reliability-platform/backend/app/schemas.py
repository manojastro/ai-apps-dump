from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RiskLevel(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StepKind(str, Enum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    MCP_CALL = "mcp_call"
    RETRIEVAL = "retrieval"
    FINAL_OUTPUT = "final_output"


class TraceStep(StrictModel):
    sequence: int = Field(ge=1)
    kind: StepKind
    name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    latency_ms: int = Field(ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    error: str | None = Field(default=None, max_length=500)


class ExpectedOutcome(StrictModel):
    artifact_type: str
    required: dict[str, Any]
    deadline: str


class ClaimedOutcome(StrictModel):
    success: bool
    summary: str = Field(max_length=500)
    attributes: dict[str, Any] = Field(default_factory=dict)


class VerifiedOutcome(StrictModel):
    success: bool
    checks: dict[str, bool]
    observed: dict[str, Any]
    mismatch_reasons: list[str] = Field(default_factory=list)
    verified_at: str = Field(default_factory=utc_now)


class AgentTrace(StrictModel):
    run_id: str
    agent_id: str
    agent_version: str
    scenario: str
    task: str
    started_at: str
    completed_at: str
    steps: list[TraceStep]
    claimed_outcome: ClaimedOutcome
    expected_outcome: ExpectedOutcome
    external_state: dict[str, Any]
    total_cost_usd: float = Field(ge=0)
    context_tokens: int = Field(ge=0)
    retry_count: int = Field(ge=0)


class Detection(StrictModel):
    code: str
    title: str
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    explanation: str
    evidence_sequences: list[int] = Field(default_factory=list)


class Evidence(StrictModel):
    evidence_id: str
    source: str
    fact: str
    value: Any
    observed_at: str


class Hypothesis(StrictModel):
    cause: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    supporting_reason: str


class RCAResult(StrictModel):
    incident_id: str
    probable_root_cause: str
    confidence: float = Field(ge=0, le=1)
    hypotheses: list[Hypothesis]
    evidence: list[Evidence]
    summary: str


class ProposedAction(StrictModel):
    action_id: str
    incident_id: str
    action_type: str
    description: str
    risk: RiskLevel
    blast_radius: str
    reversibility: str
    expected_benefit: str
    confidence: float = Field(ge=0, le=1)
    required_approval: bool
    rollback_plan: str
    allowed_tool: str
    payload_version: int = Field(default=1, ge=1)
    status: str = "PROPOSED"


class ValidationResult(StrictModel):
    validation_id: str
    incident_id: str
    stage: str
    passed: bool
    checks: dict[str, bool]
    details: str
    created_at: str = Field(default_factory=utc_now)


class RunRequest(StrictModel):
    scenario: str = "hallucinated_success"
    agent_version: str = Field(default="1.0.0", min_length=1, max_length=40)

    @field_validator("scenario")
    @classmethod
    def valid_scenario(cls, value: str) -> str:
        allowed = {
            "reliable",
            "looping",
            "expensive",
            "wrong_tool",
            "hallucinated_success",
            "partial_completion",
            "slow",
            "unsafe_action",
            "retrieval_failure",
        }
        if value not in allowed:
            raise ValueError(f"scenario must be one of: {', '.join(sorted(allowed))}")
        return value


class ApprovalRequest(StrictModel):
    approver: str = Field(min_length=2, max_length=100)
    decision: str
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("decision")
    @classmethod
    def valid_decision(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"APPROVED", "REJECTED"}:
            raise ValueError("decision must be APPROVED or REJECTED")
        return normalized


class RegressionRequest(StrictModel):
    current_version: str = "1.0.0"
    candidate_version: str = "1.1.0-safe"


class WorkflowResult(StrictModel):
    run_id: str
    incident_id: str | None
    trace: AgentTrace
    detections: list[Detection]
    verified_outcome: VerifiedOutcome
    rca: RCAResult | None
    proposed_action: ProposedAction | None
    validation: ValidationResult
