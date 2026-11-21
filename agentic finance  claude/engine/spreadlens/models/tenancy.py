"""Organization, workspace, users, memberships, sessions and audit events."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from spreadlens.models.base import Base, created_col, id_col


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = id_col()
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = created_col()


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = id_col()
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    materiality_pct: Mapped[str] = mapped_column(String(20), default="0.5")  # analyst materiality (percent), separate from rounding
    created_at: Mapped[datetime] = created_col()


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = id_col()
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = created_col()


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # analyst | reviewer | admin
    created_at: Mapped[datetime] = created_col()


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = id_col()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_col()


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = id_col()
    workspace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), default="ok")  # ok | denied | error
    details: Mapped[dict] = mapped_column(JSON, default=dict)  # never contains document content
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_col()
