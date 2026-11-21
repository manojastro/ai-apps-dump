"""Workflow runs, durable tasks, agent executions, typed artifacts and metadata questions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from spreadlens.models.base import Base, created_col, id_col


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    run_kind: Mapped[str] = mapped_column(String(20), default="initial")  # initial | retry | reextraction
    agent_mode: Mapped[str] = mapped_column(String(10))  # demo | live (fixed at start, recorded)
    state: Mapped[str] = mapped_column(String(40), default="queued")
    status: Mapped[str] = mapped_column(String(20), default="running")
    # running | awaiting_input | completed | failed | partial
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    budget: Mapped[dict] = mapped_column(JSON, default=dict)
    usage: Mapped[dict] = mapped_column(JSON, default=dict)  # model_calls, tokens_in, tokens_out, cost_usd, ocr_pages
    started_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = created_col()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowTask(Base):
    """A durable unit of work. Leased by a worker; an expired lease means the worker died and
    the task is picked up again. `idempotency_key` makes enqueueing safe to repeat."""

    __tablename__ = "workflow_tasks"
    __table_args__ = (UniqueConstraint("idempotency_key"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(40))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    # queued | running | succeeded | failed | blocked
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    output_artifact_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = created_col()
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Artifact(Base):
    """Typed, versioned agent output. Agents exchange these, never free-form chat."""

    __tablename__ = "artifacts"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    run_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(60))
    schema_version: Mapped[str] = mapped_column(String(20))
    produced_by: Mapped[str] = mapped_column(String(60))  # agent name or "code:<module>"
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = created_col()


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    run_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    agent: Mapped[str] = mapped_column(String(60))
    mode: Mapped[str] = mapped_column(String(10))  # demo | live
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tools_used: Mapped[list] = mapped_column(JSON, default=list)  # [{tool, input_digest, output_digest, ms}]
    input_artifact_ids: Mapped[list] = mapped_column(JSON, default=list)
    output_artifact_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # succeeded | failed | escalated
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    eve_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = created_col()


class MetadataQuestion(Base):
    """Ambiguous metadata the analyst must confirm before normalization."""

    __tablename__ = "metadata_questions"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[str] = mapped_column(String(32), index=True)
    field: Mapped[str] = mapped_column(String(40))  # entity_name | currency | scale | period | scope
    statement_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    answer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    answered_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = created_col()


class MetricEvent(Base):
    """Operational counters (processing time, OCR pages, export failures, ...)."""

    __tablename__ = "metric_events"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    value: Mapped[float] = mapped_column(Float)
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = created_col()


__all__ = ["WorkflowRun", "WorkflowTask", "Artifact", "AgentExecution", "MetadataQuestion", "MetricEvent", "Text"]
