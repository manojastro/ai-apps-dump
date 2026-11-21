"""ServiceNow linkage (our side) and the persistent ServiceNow simulator (the "remote" side).

The simulator tables are deliberately separate from the application's own tables: the mock
adapter talks to them exactly like the REST adapter talks to a real instance, so swapping
modes changes no business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, JSONType
from app.core.types import UTCDateTime, new_id, utcnow


class ServiceNowRecord(Base):
    __tablename__ = "servicenow_records"
    __table_args__ = (UniqueConstraint("idempotency_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    plan_id: Mapped[str] = mapped_column(ForeignKey("remediation_plans.id", ondelete="CASCADE"), index=True)
    approval_request_id: Mapped[str] = mapped_column(ForeignKey("approval_requests.id"), index=True)
    parent_record_id: Mapped[str | None] = mapped_column(ForeignKey("servicenow_records.id"), nullable=True)
    mode: Mapped[str] = mapped_column(String(8))  # mock | real
    instance: Mapped[str] = mapped_column(String(255))
    table_name: Mapped[str] = mapped_column(String(80))
    sys_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    record_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sync_state: Mapped[str] = mapped_column(String(16), default="SYNC_PENDING", index=True)
    external_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_close_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    last_sync_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)


class ServiceNowSyncAttempt(Base):
    __tablename__ = "servicenow_sync_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    record_id: Mapped[str | None] = mapped_column(
        ForeignKey("servicenow_records.id", ondelete="CASCADE"), index=True, nullable=True
    )
    operation: Mapped[str] = mapped_column(String(32))  # create | lookup | read | update | test_connection | cmdb_sync
    table_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    outcome: Mapped[str] = mapped_column(String(24))  # success | error | adopted_existing | denied
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)


class SnSimRecord(Base):
    """A record inside the simulated ServiceNow instance (any table)."""

    __tablename__ = "sn_sim_records"
    __table_args__ = (UniqueConstraint("table_name", "sys_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    table_name: Mapped[str] = mapped_column(String(80), index=True)
    sys_id: Mapped[str] = mapped_column(String(32), index=True)
    number: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    fields: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    sys_created_by: Mapped[str] = mapped_column(String(80), default="system")
    sys_created_on: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    sys_updated_on: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)


class SnSimActivity(Base):
    """Activity stream (sys_audit equivalent) for simulated records."""

    __tablename__ = "sn_sim_activity"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    table_name: Mapped[str] = mapped_column(String(80))
    sys_id: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(32))
    changes: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    actor: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
