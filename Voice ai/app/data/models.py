"""FHIR-shaped SQLAlchemy tables.

Differences from real FHIR (documented on purpose):
- Flat columns instead of nested JSON (Patient.name -> given/family).
- Ids are short strings like "pat-0001" instead of server-assigned logical ids.
- Slot/Appointment status vocabularies are reduced to the few values we use.
- Observation is a recovery check-in (pain_score, temperature, free_text), not a LOINC-coded observation.
- Communication.status uses draft/approved/rejected/sent_simulated (FHIR: preparation/completed/...).
All data is synthetic.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.data.db import Base


class Patient(Base):
    __tablename__ = "patient"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    given: Mapped[str] = mapped_column(String)
    family: Mapped[str] = mapped_column(String)
    birth_date: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)  # synthetic, 555-01xx style


class Practitioner(Base):
    __tablename__ = "practitioner"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    specialty: Mapped[str] = mapped_column(String)


class Slot(Base):
    __tablename__ = "slot"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    practitioner_id: Mapped[str] = mapped_column(String, index=True)
    start: Mapped[datetime] = mapped_column(DateTime, index=True)
    end: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="free")  # free | busy


class Appointment(Base):
    __tablename__ = "appointment"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    practitioner_id: Mapped[str] = mapped_column(String)
    slot_id: Mapped[str] = mapped_column(String)
    start: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String)  # booked | fulfilled | cancelled
    reason: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Observation(Base):
    """Recovery check-in submitted by a patient."""

    __tablename__ = "observation"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    appointment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    effective: Mapped[datetime] = mapped_column(DateTime)
    pain_score: Mapped[int] = mapped_column(Integer)  # 0-10
    temperature: Mapped[float] = mapped_column(Float)  # Celsius
    free_text: Mapped[str] = mapped_column(Text, default="")  # UNTRUSTED patient text
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reasons: Mapped[list] = mapped_column(JSON, default=list)
    review_summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="received")  # received | flagged | reviewed


class Communication(Base):
    __tablename__ = "communication"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String)  # draft | approved | rejected | sent_simulated
    body: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SupplyItem(Base):
    __tablename__ = "supply_item"
    sku: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    on_hand: Mapped[int] = mapped_column(Integer)
    reorder_level: Mapped[int] = mapped_column(Integer)
    usage_per_appointment: Mapped[float] = mapped_column(Float)
    pack_size: Mapped[int] = mapped_column(Integer, default=10)


class SupplyOrder(Base):
    __tablename__ = "supply_order"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String)  # draft | pending_approval | approved | rejected
    lines: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Approval(Base):
    __tablename__ = "approval"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)  # pending | approved | rejected | expired
    required_role: Mapped[str] = mapped_column(String, index=True)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    ref_id: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    requested_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditEntry(Base):
    __tablename__ = "audit_entry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    actor: Mapped[str] = mapped_column(String, index=True)  # agent role or "staff:<user>"
    tool: Mapped[str] = mapped_column(String, index=True)
    args_hash: Mapped[str] = mapped_column(String)
    patient_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String)  # ok | denied | error | replayed
    detail: Mapped[str] = mapped_column(Text, default="")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_record"
    __table_args__ = (UniqueConstraint("tool", "key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool: Mapped[str] = mapped_column(String)
    key: Mapped[str] = mapped_column(String)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, index=True, default="PENDING")  # PENDING|CLAIMED|DONE|DEAD
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    claimed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Workflow(Base):
    __tablename__ = "workflow"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)  # RUNNING|WAITING_APPROVAL|WAITING_TIMER|COMPLETED|FAILED|ESCALATED
    step: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON)
    history: Mapped[list] = mapped_column(JSON)
    event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class AgentRun(Base):
    __tablename__ = "agent_run"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    agent: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    steps: Mapped[int] = mapped_column(Integer)
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[float] = mapped_column(Float)
    prompt_version: Mapped[str] = mapped_column(String)
    llm_mode: Mapped[str] = mapped_column(String, default="MOCK")
    created_at: Mapped[datetime] = mapped_column(DateTime)


class StaffUser(Base):
    __tablename__ = "staff_user"
    username: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String)  # front_desk | nurse | inventory
    password_hash: Mapped[str] = mapped_column(String)  # demo only
