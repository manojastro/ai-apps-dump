"""Pydantic request/response and tool IO schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RootCauseAnalysis(BaseModel):
    incident_id: str
    observations: list[str]
    evidence: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    rejected_hypotheses: list[dict[str, Any]]
    root_cause: str
    confidence: float
    recommended_actions: list[str]


class TrainBaselineRequest(BaseModel):
    seed: int = 42
    n_samples: int = Field(default=6000, ge=500, le=20000)


class TrainBaselineResponse(BaseModel):
    version: str
    status: str
    metrics: dict[str, float]
    thresholds: dict[str, Any]


class WindowCreateRequest(BaseModel):
    name: str = ""
    step: int | None = None
    n_samples: int = Field(default=4000, ge=100, le=20000)
    seed: int | None = None
    knobs: dict[str, Any] = Field(default_factory=dict)


class WindowCreatedResponse(BaseModel):
    id: int
    name: str
    n_samples: int
    seed: int
    knobs: dict[str, Any]


class DecideRequest(BaseModel):
    window_id: int


class CandidateTrainRequest(BaseModel):
    source_window_id: int | None = None
    seed: int = 7
    n_samples: int = Field(default=4000, ge=50, le=20000)
    inject_bad: bool = False
    bad_n_samples: int = 140
    bad_label_noise: float = 0.35


class CandidateEvaluateRequest(BaseModel):
    version: str


class ShadowRunRequest(BaseModel):
    version: str
    n_requests: int = Field(default=3000, ge=100, le=20000)
    seed: int = 555


class CanaryRequest(BaseModel):
    version: str
    n_requests: int = Field(default=2500, ge=100, le=20000)
    seed: int = 777


class PromotionCreateRequest(BaseModel):
    candidate_version: str


class ApprovalRequest(BaseModel):
    approver: str = "ml-ops-oncall"
    comment: str = ""


class RollbackRequest(BaseModel):
    reason: str = ""


class EvaluateWindowInput(BaseModel):
    window_id: int


class EvaluateWindowOutput(BaseModel):
    window_id: int
    alert: bool
    drift_count: int
    max_psi: float
    max_tv_delta: float
    quality_passed: bool
    fairness_ratio: float
    f1: float
    positive_rate_delta: float


class TrainCandidateInput(BaseModel):
    source_window_id: int | None = None
    seed: int = 7
    n_samples: int = Field(default=4000, ge=50, le=20000)
    inject_bad: bool = False
    bad_n_samples: int = 140
    bad_label_noise: float = 0.35


class TrainCandidateOutput(BaseModel):
    version: str
    kind: str
    algorithm: str
    n_samples: int
    metrics: dict[str, float]
    source_knobs: dict[str, Any]


class EvaluateCandidateInput(BaseModel):
    version: str


class EvaluateCandidateOutput(BaseModel):
    version: str
    verdict: str
    offline_metrics: dict[str, float]
    vs_thresholds: dict[str, bool]
    vs_champion: dict[str, float]
    fairness_ratio: float
    robustness_drop: float
    reasons: list[str]


class ShadowCompareInput(BaseModel):
    version: str
    n_requests: int = Field(default=3000, ge=100, le=20000)
    seed: int = 555


class ShadowCompareOutput(BaseModel):
    version: str
    n_requests: int
    disagreement_rate: float
    mean_abs_prob_diff: float
    per_segment: dict[str, float]


class CanaryEvalInput(BaseModel):
    version: str
    n_requests: int = Field(default=2500, ge=100, le=20000)
    seed: int = 777


class CanaryEvalOutput(BaseModel):
    version: str
    passed: bool
    slices: dict[str, Any]
    details: dict[str, Any]


class PromoteModelInput(BaseModel):
    promotion_id: int
    approver: str = "ml-ops-oncall"
    comment: str = ""


class PromoteModelOutput(BaseModel):
    promotion_id: int
    state: str
    champion_version: str


class RollbackModelInput(BaseModel):
    target_version: str
    reason: str = ""


class RollbackModelOutput(BaseModel):
    from_version: str
    to_version: str
    champion_version: str


class GateInputs(BaseModel):
    meaningful_drift: bool
    perf_degradation: bool
    high_risk_drift: bool
    sufficient_new_labeled_samples: bool
    projected_benefit: float
    min_projected_benefit: float
    n_labeled_samples: int
    min_labeled_samples: int


class DecisionOutput(BaseModel):
    window_id: int
    decision: str
    reasons: list[str]
    gate_inputs: GateInputs
    projected_benefit: float
    narration: str
