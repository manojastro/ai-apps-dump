"""Relational data model. Tenant-scoped tables carry tenant_id and are protected by RLS policies
created in the initial migration."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

Json = JSON().with_variant(JSONB(), "postgresql")
Money = Numeric(14, 2)


def new_id() -> uuid.UUID:
    return uuid.uuid4()


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: Json, list[Any]: Json, uuid.UUID: UUID(as_uuid=True), Decimal: Money}


def pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)


def tenant_fk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)


def created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# --------------------------------------------------------------------------- identity


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = pk()
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = created()


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = pk()
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str | None] = mapped_column(String(300))
    oidc_subject: Mapped[str | None] = mapped_column(String(300), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = created()


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", "role"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))  # requester | approver | admin | viewer
    created_at: Mapped[datetime] = created()


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # sha256 of the cookie token
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    csrf_token: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = created()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", "endpoint", "key"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    endpoint: Mapped[str] = mapped_column(String(200))
    key: Mapped[str] = mapped_column(String(200))
    request_hash: Mapped[str] = mapped_column(String(64))
    status_code: Mapped[int] = mapped_column(Integer)
    response: Mapped[dict[str, Any]] = mapped_column(Json)
    created_at: Mapped[datetime] = created()


# --------------------------------------------------------------------------- suppliers & policy


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("tenant_id", "key"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    key: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    base_url: Mapped[str] = mapped_column(String(300))
    allowed_origins: Mapped[list[Any]] = mapped_column(Json, default=list)
    adapter: Mapped[str] = mapped_column(String(64), default="semantic_portal_v1")
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    eligibility_status: Mapped[str] = mapped_column(String(32), default="approved")  # approved | suspended
    status_api_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    conditional_submit_supported: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = created()


class SupplierCredentialMetadata(Base):
    __tablename__ = "supplier_credentials_metadata"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"), unique=True)
    credential_ref: Mapped[str] = mapped_column(String(200))  # key in the secret store, never the secret
    username_hint: Mapped[str] = mapped_column(String(64))
    session_retention_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()


class BrowserSessionState(Base):
    __tablename__ = "browser_session_states"
    __table_args__ = (UniqueConstraint("tenant_id", "supplier_id"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    encrypted_state: Mapped[bytes] = mapped_column(LargeBinary)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = created()


class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    __table_args__ = (UniqueConstraint("tenant_id", "version"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    version: Mapped[int] = mapped_column(Integer)
    rules: Mapped[dict[str, Any]] = mapped_column(Json)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created()


class PolicyException(Base):
    """An explicit, authorized exception to a hard rule for one quote. Never created by the agent."""

    __tablename__ = "policy_exceptions"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"))
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"))
    rule: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    granted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created()


# --------------------------------------------------------------------------- requests & runs


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"
    __table_args__ = (UniqueConstraint("tenant_id", "requester_id", "idempotency_key"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    canonical_product_id: Mapped[str] = mapped_column(String(64))
    spec_requirements: Mapped[dict[str, Any]] = mapped_column(Json)
    quantity: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    budget_total: Mapped[Decimal] = mapped_column(Money)
    address_ref: Mapped[str] = mapped_column(String(64))
    delivery_deadline: Mapped[date] = mapped_column(Date)
    allowed_supplier_ids: Mapped[list[Any]] = mapped_column(Json, default=list)
    status: Mapped[str] = mapped_column(String(32), default="submitted")
    version: Mapped[int] = mapped_column(Integer, default=1)
    idempotency_key: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = created()


class RequestItem(Base):
    __tablename__ = "request_items"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_requests.id"), index=True)
    canonical_product_id: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer)
    spec: Mapped[dict[str, Any]] = mapped_column(Json)


class ProcurementRun(Base):
    __tablename__ = "procurement_runs"
    __table_args__ = (UniqueConstraint("tenant_id", "request_id", "idempotency_key"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_requests.id"), index=True)
    request_version: Mapped[int] = mapped_column(Integer)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policy_versions.id"))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    phase: Mapped[str] = mapped_column(String(64), default="queued")
    mode: Mapped[str] = mapped_column(String(16))  # fixture | real
    model_name: Mapped[str] = mapped_column(String(100))
    workflow: Mapped[str] = mapped_column(String(32), default="bounded")  # bounded | single_pass | fixed_selector
    fixture_options: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    action_count: Mapped[int] = mapped_column(Integer, default=0)
    active_ms: Mapped[int] = mapped_column(BigInteger, default=0)
    waiting_ms: Mapped[int] = mapped_column(BigInteger, default=0)
    model_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
    model_input_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    model_output_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    current_supplier: Mapped[str | None] = mapped_column(String(32))
    selected_quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    approval_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    order_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    handoff: Mapped[dict[str, Any] | None] = mapped_column(Json)
    outcome: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[str | None] = mapped_column(String(200))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()


class BrowserStep(Base):
    __tablename__ = "browser_steps"
    __table_args__ = (UniqueConstraint("run_id", "seq"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    supplier_key: Mapped[str | None] = mapped_column(String(32))
    tool: Mapped[str] = mapped_column(String(64))
    side_effect: Mapped[bool] = mapped_column(Boolean, default=False)
    input: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    status: Mapped[str] = mapped_column(String(16))  # ok | error | blocked
    observation: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(500))
    evidence_ids: Mapped[list[Any]] = mapped_column(Json, default=list)
    explanation: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[str] = mapped_column(String(32), default="code")  # code | fixture_model | model
    started_at: Mapped[datetime] = created()
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)


class Quote(Base):
    """Immutable; an updated offer is a new row with a higher version and supersedes_id."""

    __tablename__ = "quotes"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    sku: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(300))
    canonical_id: Mapped[str | None] = mapped_column(String(64))
    normalized_spec: Mapped[dict[str, Any]] = mapped_column(Json)
    quantity: Mapped[int] = mapped_column(Integer)
    pack_size: Mapped[int | None] = mapped_column(Integer)
    stock_observed: Mapped[int | None] = mapped_column(Integer)
    unit_price: Mapped[Decimal | None] = mapped_column(Money)
    subtotal: Mapped[Decimal | None] = mapped_column(Money)
    discount: Mapped[Decimal | None] = mapped_column(Money)
    tax: Mapped[Decimal | None] = mapped_column(Money)
    shipping: Mapped[Decimal | None] = mapped_column(Money)
    total: Mapped[Decimal | None] = mapped_column(Money)
    price_basis: Mapped[str | None] = mapped_column(String(16))
    tax_basis: Mapped[str | None] = mapped_column(String(32))
    currency: Mapped[str | None] = mapped_column(String(3))
    delivery_date: Mapped[date | None] = mapped_column(Date)
    delivery_confidence: Mapped[str] = mapped_column(String(16))  # confirmed | estimated | unknown
    address_ref: Mapped[str | None] = mapped_column(String(64))
    supplier_quote_ref: Mapped[str | None] = mapped_column(String(64))
    product_url: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str] = mapped_column(String(500))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evidence_ids: Mapped[list[Any]] = mapped_column(Json, default=list)
    extraction_method: Mapped[str] = mapped_column(String(32))
    issues: Mapped[list[Any]] = mapped_column(Json, default=list)
    canonical_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = created()


class QuoteLine(Base):
    __tablename__ = "quote_lines"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # goods | discount | tax | shipping
    description: Mapped[str] = mapped_column(String(300))
    amount: Mapped[Decimal] = mapped_column(Money)


class PolicyDecision(Base):
    __tablename__ = "policy_decisions"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"), index=True)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policy_versions.id"))
    context: Mapped[str] = mapped_column(String(32))  # comparison | recommendation | revalidation | approval
    eligible: Mapped[bool] = mapped_column(Boolean)
    results: Mapped[list[Any]] = mapped_column(Json)
    created_at: Mapped[datetime] = created()


# --------------------------------------------------------------------------- approvals & orders


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_requests.id"))
    request_version: Mapped[int] = mapped_column(Integer)
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"))
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    binding: Mapped[dict[str, Any]] = mapped_column(Json)
    fingerprint: Mapped[str] = mapped_column(String(64))
    cart_fingerprint: Mapped[str] = mapped_column(String(64))
    max_amount: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3))
    quantity: Mapped[int] = mapped_column(Integer)
    delivery_deadline: Mapped[date] = mapped_column(Date)
    address_ref: Mapped[str] = mapped_column(String(64))
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policy_versions.id"))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    invalidation: Mapped[dict[str, Any] | None] = mapped_column(Json)
    consumed_by_intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True)
    created_at: Mapped[datetime] = created()


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    approval_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("approval_requests.id"), unique=True)
    approver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(16))  # approved | rejected
    reason: Mapped[str] = mapped_column(Text)
    approved_fingerprint: Mapped[str] = mapped_column(String(64))
    policy_evaluation: Mapped[list[Any]] = mapped_column(Json)
    soft_overrides: Mapped[list[Any]] = mapped_column(Json, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime] = created()


class OrderIntent(Base):
    __tablename__ = "order_intents"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    approval_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("approval_requests.id"), unique=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"))
    intent_key: Mapped[str] = mapped_column(String(128), unique=True)  # supplier idempotency token / PO ref
    approved_fingerprint: Mapped[str] = mapped_column(String(64))
    max_amount: Mapped[Decimal] = mapped_column(Money)
    status: Mapped[str] = mapped_column(String(32), default="created")
    status_reason: Mapped[str | None] = mapped_column(Text)
    submit_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = created()


class OrderAttempt(Base):
    __tablename__ = "order_attempts"
    __table_args__ = (UniqueConstraint("intent_id", "attempt_no"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    intent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_intents.id"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer)
    worker_id: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(32), default="started")  # started|submitted|timeout|rejected|error
    detail: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    evidence_ids: Mapped[list[Any]] = mapped_column(Json, default=list)
    started_at: Mapped[datetime] = created()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupplierOrder(Base):
    __tablename__ = "supplier_orders"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    intent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_intents.id"), unique=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id"))
    supplier_order_ref: Mapped[str] = mapped_column(String(64))
    sku: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[int | None] = mapped_column(Integer)
    total: Mapped[Decimal | None] = mapped_column(Money)
    currency: Mapped[str | None] = mapped_column(String(3))
    delivery_date: Mapped[date | None] = mapped_column(Date)
    reconciled_via: Mapped[str] = mapped_column(String(32))  # confirmation_page | order_history | status_api
    receipt_evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = created()


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # screenshot | page_text | receipt | cart | export
    label: Mapped[str] = mapped_column(String(200))
    storage_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(100))
    redacted: Mapped[bool] = mapped_column(Boolean, default=True)
    retention_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()


# --------------------------------------------------------------------------- execution & audit


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_claim", "status", "available_at"),)
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # start | resume | reconcile
    payload: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    dedupe_key: Mapped[str] = mapped_column(String(200), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued | leased | done | failed | dead
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    lease_owner: Mapped[str | None] = mapped_column(String(100))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    worker_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    active_jobs: Mapped[int] = mapped_column(Integer, default=0)
    info: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)


class RunEvent(Base):
    __tablename__ = "run_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("procurement_runs.id"), index=True)
    type: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = created()


class AuditEvent(Base):
    """Append-only; UPDATE and DELETE are rejected by a trigger."""

    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    actor_type: Mapped[str] = mapped_column(String(16))  # user | agent | worker | system
    actor_id: Mapped[str | None] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(100))
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    created_at: Mapped[datetime] = created()


class EvalRun(Base):
    __tablename__ = "eval_runs"
    id: Mapped[uuid.UUID] = pk()
    tenant_id: Mapped[uuid.UUID] = tenant_fk()
    label: Mapped[str] = mapped_column(String(200))
    mode: Mapped[str] = mapped_column(String(16))
    config: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    metrics: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    gates: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    results: Mapped[list[Any]] = mapped_column(Json, default=list)
    created_at: Mapped[datetime] = created()


TENANT_SCOPED_TABLES = [
    "idempotency_keys",
    "suppliers",
    "supplier_credentials_metadata",
    "browser_session_states",
    "policy_versions",
    "policy_exceptions",
    "procurement_requests",
    "request_items",
    "procurement_runs",
    "browser_steps",
    "quotes",
    "quote_lines",
    "policy_decisions",
    "approval_requests",
    "approvals",
    "order_intents",
    "order_attempts",
    "supplier_orders",
    "evidence_artifacts",
    "run_events",
    "audit_events",
    "eval_runs",
]

ACTIVE_RUN_STATUSES = ("queued", "running", "awaiting_approval", "submitting", "reconciling", "cancellation_requested")
