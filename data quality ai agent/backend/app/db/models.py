from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIMENSIONS = 128


class Base(DeclarativeBase):
    pass


class IncidentRow(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    pipeline_id: Mapped[str] = mapped_column(String(80), index=True)
    environment: Mapped[str] = mapped_column(String(20))
    scenario: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), index=True)
    current_stage: Mapped[str] = mapped_column(String(80), default="incident_intake")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(40), index=True)
    updated_at: Mapped[str] = mapped_column(String(40))
    input: Mapped[dict[str, Any]] = mapped_column(JSON)
    artifact: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    failure_reason: Mapped[str] = mapped_column(Text, default="")


class EventRow(Base):
    __tablename__ = "incident_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    node: Mapped[str] = mapped_column(String(80))
    timestamp: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    __table_args__ = (Index("ix_events_incident_cursor", "incident_id", "id"),)


class EvidenceRow(Base):
    __tablename__ = "evidence"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    branch: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(Text)
    facts: Mapped[dict[str, Any]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[str] = mapped_column(String(40))


class HypothesisRow(Base):
    __tablename__ = "hypotheses"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    cause: Mapped[str] = mapped_column(String(100), primary_key=True)
    summary: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    contradicting_evidence: Mapped[list[str]] = mapped_column(JSON)


class AttemptRow(Base):
    __tablename__ = "remediation_attempts"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))
    feedback: Mapped[list[str]] = mapped_column(JSON)


class ValidationRow(Base):
    __tablename__ = "validation_results"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    attempt: Mapped[int] = mapped_column(Integer, primary_key=True)
    validator: Mapped[str] = mapped_column(String(100), primary_key=True)
    status: Mapped[str] = mapped_column(String(10))
    severity: Mapped[str] = mapped_column(String(20))
    expected: Mapped[Any] = mapped_column(JSON)
    actual: Mapped[Any] = mapped_column(JSON)
    evidence: Mapped[str] = mapped_column(Text)


class VerificationRow(Base):
    __tablename__ = "verifications"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    decision: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float)
    reason_summary: Mapped[str] = mapped_column(Text)
    unsupported_claims: Mapped[list[str]] = mapped_column(JSON)
    missing_checks: Mapped[list[str]] = mapped_column(JSON)
    risk_findings: Mapped[list[str]] = mapped_column(JSON)


class ApprovalRow(Base):
    __tablename__ = "approvals"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))
    comment: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean)
    decided_at: Mapped[str] = mapped_column(String(40))


class AuditRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    tool: Mapped[str] = mapped_column(String(80))
    timestamp: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class KnowledgeRow(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    pipeline_id: Mapped[str] = mapped_column(String(80))
    environment: Mapped[str] = mapped_column(String(20))
    service: Mapped[str] = mapped_column(String(80))
    source_type: Mapped[str] = mapped_column(String(30))
    document_type: Mapped[str] = mapped_column(String(30))
    version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[str] = mapped_column(String(40))
    __table_args__ = (Index("ix_knowledge_scope", "pipeline_id", "environment"),)


class ChunkRow(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(
        JSON().with_variant(Vector(EMBEDDING_DIMENSIONS), "postgresql")
    )
    embedding_model: Mapped[str] = mapped_column(String(100))


class EvaluationRow(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON)
    cases: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
