"""SQLAlchemy entity models for the drift and retraining platform."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelRegistry(Base):
    """Registered model version with lifecycle status."""

    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="challenger", index=True)
    kind: Mapped[str] = mapped_column(String(16), default="candidate")
    algorithm: Mapped[str] = mapped_column(String(64), default="")
    artifact_path: Mapped[str] = mapped_column(String(512), default="")
    thresholds: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TrainingRun(Base):
    """Record of one training execution."""

    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    algorithm: Mapped[str] = mapped_column(String(64), default="")
    n_samples: Mapped[int] = mapped_column(Integer, default=0)
    seed: Mapped[int] = mapped_column(Integer, default=0)
    source_window_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hyperparams: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MonitoringWindow(Base):
    """A submitted monitoring window of production traffic."""

    __tablename__ = "monitoring_windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n_samples: Mapped[int] = mapped_column(Integer, default=0)
    seed: Mapped[int] = mapped_column(Integer, default=0)
    knobs: Mapped[dict] = mapped_column(JSON, default=dict)
    data_path: Mapped[str] = mapped_column(String(512), default="")
    evaluated: Mapped[bool] = mapped_column(Boolean, default=False)
    alert: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DriftResult(Base):
    """Per-feature drift measurement for a window."""

    __tablename__ = "drift_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    feature: Mapped[str] = mapped_column(String(64))
    feature_type: Mapped[str] = mapped_column(String(16))
    psi: Mapped[float | None] = mapped_column(Float, nullable=True)
    ks_statistic: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    tv_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    missing_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_missing: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_missing: Mapped[float | None] = mapped_column(Float, nullable=True)
    drifted: Mapped[bool] = mapped_column(Boolean, default=False)
    severity: Mapped[str] = mapped_column(String(16), default="none")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PredictionStat(Base):
    """Aggregate prediction behaviour for a window."""

    __tablename__ = "prediction_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    n_predictions: Mapped[int] = mapped_column(Integer, default=0)
    positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    absolute_delta: Mapped[float] = mapped_column(Float, default=0.0)
    drifted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PerformanceResult(Base):
    """Champion performance measured against window ground truth."""

    __tablename__ = "performance_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    model_version: Mapped[str] = mapped_column(String(64))
    n_evaluated: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    precision: Mapped[float] = mapped_column(Float, default=0.0)
    recall: Mapped[float] = mapped_column(Float, default=0.0)
    f1: Mapped[float] = mapped_column(Float, default=0.0)
    roc_auc: Mapped[float] = mapped_column(Float, default=0.0)
    brier: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DataQualityCheck(Base):
    """Outcome of a single data quality rule on a window."""

    __tablename__ = "data_quality_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    check_name: Mapped[str] = mapped_column(String(64))
    passed: Mapped[bool] = mapped_column(Boolean, default=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FairnessResult(Base):
    """Segment parity measurement for a window."""

    __tablename__ = "fairness_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    segment_column: Mapped[str] = mapped_column(String(64))
    selection_rates: Mapped[dict] = mapped_column(JSON, default=dict)
    disparity_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    threshold: Mapped[float] = mapped_column(Float, default=0.8)
    passed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RetrainingDecision(Base):
    """Gate decision explaining whether retraining is justified."""

    __tablename__ = "retraining_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    decision: Mapped[str] = mapped_column(String(16))
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    gate_inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    projected_benefit: Mapped[float] = mapped_column(Float, default=0.0)
    narration: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Investigation(Base):
    """Root cause analysis record for a drift incident."""

    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    window_id: Mapped[int] = mapped_column(Integer, index=True)
    incident_id: Mapped[str] = mapped_column(String(32))
    root_cause: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    observations: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)
    narration: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvidenceItem(Base):
    """Evidence attached to an investigation."""

    __tablename__ = "investigation_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Hypothesis(Base):
    """Hypothesis considered during investigation."""

    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(Integer, index=True)
    statement: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="open")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RejectedHypothesis(Base):
    """Hypothesis explicitly rejected during investigation."""

    __tablename__ = "rejected_hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(Integer, index=True)
    statement: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CandidateEvaluation(Base):
    """Deployment gate evaluation of a candidate against thresholds and champion."""

    __tablename__ = "candidate_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    verdict: Mapped[str] = mapped_column(String(16))
    offline_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    vs_thresholds: Mapped[dict] = mapped_column(JSON, default=dict)
    vs_champion: Mapped[dict] = mapped_column(JSON, default=dict)
    fairness_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    robustness_drop: Mapped[float] = mapped_column(Float, default=0.0)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DeploymentRisk(Base):
    """Deterministic deployment risk assessment for a candidate."""

    __tablename__ = "deployment_risks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[str] = mapped_column(String(8))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ShadowComparison(Base):
    """Champion versus challenger replay comparison."""

    __tablename__ = "shadow_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    window_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n_requests: Mapped[int] = mapped_column(Integer, default=0)
    disagreement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    mean_abs_prob_diff: Mapped[float] = mapped_column(Float, default=0.0)
    per_segment: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CanaryResult(Base):
    """Per-slice canary evaluation before promotion."""

    __tablename__ = "canary_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    slices: Mapped[dict] = mapped_column(JSON, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Promotion(Base):
    """Approval state machine instance for promoting a candidate."""

    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_version: Mapped[str] = mapped_column(String(64))
    previous_champion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(24), default="PROPOSED", index=True)
    verification: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApprovalRecord(Base):
    """Human approval or rejection of a promotion."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(Integer, index=True)
    decision: Mapped[str] = mapped_column(String(16))
    approver: Mapped[str] = mapped_column(String(64), default="")
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RollbackRecord(Base):
    """History of champion rollbacks."""

    __tablename__ = "rollbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_version: Mapped[str] = mapped_column(String(64))
    to_version: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ToolCall(Base):
    """Audit trail entry for every tool invocation."""

    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(64), index=True)
    permission: Mapped[str] = mapped_column(String(16), default="safe")
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class KpiSnapshot(Base):
    """Point-in-time platform KPI capture."""

    __tablename__ = "kpi_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
