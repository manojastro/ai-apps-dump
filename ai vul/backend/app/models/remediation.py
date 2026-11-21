"""Risk assessments, remediation plans and the approval ledger."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, JSONType
from app.core.types import UTCDateTime, new_id, utcnow


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id", ondelete="CASCADE"), index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    score: Mapped[int] = mapped_column(Integer)
    score_lower: Mapped[int] = mapped_column(Integer)
    score_upper: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(16))
    priority: Mapped[str] = mapped_column(String(4))
    business_impact: Mapped[str] = mapped_column(String(16))
    coverage: Mapped[float] = mapped_column(Float)
    policy_version: Mapped[str] = mapped_column(String(64))
    factors: Mapped[dict[str, Any]] = mapped_column(JSONType)
    missing_factors: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    requires_immediate_review: Mapped[bool] = mapped_column(Boolean, default=False)
    rationale: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    calculated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class RemediationPlan(Base):
    __tablename__ = "remediation_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id", ondelete="CASCADE"), index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    risk_assessment_id: Mapped[str | None] = mapped_column(ForeignKey("risk_assessments.id"), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(24), default="DRAFT", index=True)
    remediation_state: Mapped[str] = mapped_column(String(32), default="NOT_STARTED")
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    target_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prerequisites: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    implementation_steps: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    verification_steps: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    rollback_steps: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    testing_requirements: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    expected_impact: Mapped[str] = mapped_column(Text, default="")
    maintenance_window: Mapped[str] = mapped_column(Text, default="")
    required_approvers: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    evidence_refs: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    assumptions: Mapped[list[Any]] = mapped_column(JSONType, default=list)
    change_impact: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    validation: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    requires_expert_validation: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_by: Mapped[str] = mapped_column(String(128))  # provider/model or "analyst"
    content_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    edited_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)

    approvals: Mapped[list[ApprovalRequest]] = relationship(back_populates="plan", order_by="ApprovalRequest.created_at")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        # At most one open request per plan (partial unique index on both PostgreSQL and SQLite).
        Index(
            "uq_approval_one_pending_per_plan",
            "plan_id",
            unique=True,
            postgresql_where=text("state = 'PENDING'"),
            sqlite_where=text("state = 'PENDING'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(ForeignKey("remediation_plans.id", ondelete="CASCADE"), index=True)
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    assigned_approver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    state: Mapped[str] = mapped_column(String(24), default="PENDING", index=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payload_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONType)
    payload_hash: Mapped[str] = mapped_column(String(64))
    policy_version: Mapped[str] = mapped_column(String(64))
    separation_of_duties: Mapped[bool] = mapped_column(Boolean, default=True)
    request_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    plan: Mapped[RemediationPlan] = relationship(back_populates="approvals")
    decisions: Mapped[list[ApprovalDecision]] = relationship(order_by="ApprovalDecision.created_at")


class ApprovalDecision(Base):
    """Append-only decision history (including denied attempts)."""

    __tablename__ = "approval_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    approval_request_id: Mapped[str] = mapped_column(ForeignKey("approval_requests.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(24))
    outcome: Mapped[str] = mapped_column(String(16))  # accepted | denied
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
