"""Pydantic v2 schemas for API and internal contracts."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Action(BaseModel):
    name: str
    kind: str
    command: str | None = None
    rationale: str = ""


class Evidence(BaseModel):
    id: str
    source: str
    kind: str
    summary: str
    data: dict[str, Any] | None = None


class Hypothesis(BaseModel):
    id: str
    statement: str
    status: Literal["proposed", "confirmed", "rejected"] = "proposed"
    score: float = 0.0
    refuted_by: str | None = None


class RootCauseAnalysis(BaseModel):
    incident_id: str
    observations: list[str]
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]
    rejected_hypotheses: list[Hypothesis]
    root_cause: str
    confidence: float
    recommended_actions: list[Action]


class RegressionOut(BaseModel):
    kind: str
    severity: str
    source: str = ""
    destination: str = ""
    message: str
    detail: dict[str, Any] = {}


class IntentResultOut(BaseModel):
    name: str
    itype: str
    passed: bool
    detail: str


class RiskAssessment(BaseModel):
    score: float
    band: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    components: dict[str, float]
    confidence: float


class ValidationReport(BaseModel):
    change_id: int
    run_id: int
    verdict: Literal["PASS", "FAIL"]
    risk: RiskAssessment
    regressions: list[RegressionOut] = Field(default_factory=list)
    intents: list[IntentResultOut] = Field(default_factory=list)
    intent_compliance_pct: float = 100.0
    matrix_diff_summary: dict[str, Any] = Field(default_factory=dict)
    routing_changes: list[dict[str, Any]] = Field(default_factory=list)
    topology_findings: list[dict[str, Any]] = Field(default_factory=list)
    blast_radius_devices: list[str] = Field(default_factory=list)
    rca: RootCauseAnalysis | None = None
    proposed_fix_diff: str | None = None
    fix_validated: bool = False
    duration_ms: int = 0
    narration: str = ""
    stages: list[dict[str, Any]] = Field(default_factory=list)
    investigations: list[dict[str, Any]] = Field(default_factory=list)
    evidence_count: int = 0
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)


class ChangeCreate(BaseModel):
    title: str
    config_diff: str
    requested_by: str = "netops"
    description: str = ""


class ChangeOut(BaseModel):
    id: int
    title: str
    status: str
    risk_score: float
    risk_band: str
    requested_by: str
    fix_validated: bool
    fault_name: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    approver: str
    comment: str = ""
    justification: str = ""


class RejectRequest(BaseModel):
    actor: str
    reason: str = ""


class SnapshotSeedRequest(BaseModel):
    payload: dict[str, Any] | None = None
    reset_intents: bool = False


class FaultSubmitRequest(BaseModel):
    requested_by: str = "netops"


class TopologyNode(BaseModel):
    name: str
    role: str
    zone: str
    enabled: bool = True


class TopologyEdge(BaseModel):
    source: str
    target: str
    subnet: str
    kind: str = "segment"


class TopologyOut(BaseModel):
    version: str
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    subnets: list[dict[str, Any]] = []
    services: list[dict[str, Any]] = []


class ReachabilityRow(BaseModel):
    src: str
    dst: str
    proto: str
    port: int
    status: str
    reason: str | None = None
    path: list[str] = []
    asymmetric: bool = False


class ReachabilityOut(BaseModel):
    version: str
    rows: list[ReachabilityRow]
    summary: dict[str, Any] = {}
