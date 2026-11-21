"""SQLAlchemy 2 models. See docs/data_dictionary.md for column meanings.

Primary keys are plain integers supplied by the connector, not database sequences,
because the loader upserts on source ids. That is what makes re-loading idempotent.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 512


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    region: Mapped[str] = mapped_column(String(20))


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    password_hash: Mapped[str | None] = mapped_column(String(200))
    team: Mapped[Team | None] = relationship()


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(200), index=True)
    domain: Mapped[str | None] = mapped_column(String(200), index=True)
    industry: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(20), index=True)
    segment: Mapped[str] = mapped_column(String(20), index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    arr: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    churned_at: Mapped[dt.date | None] = mapped_column(Date)
    health_score: Mapped[int | None] = mapped_column(Integer)
    health_status: Mapped[str | None] = mapped_column(String(10))
    owner: Mapped[User | None] = relationship()


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(200))
    is_executive: Mapped[bool] = mapped_column(Boolean, default=False)
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[dt.date | None] = mapped_column(Date, index=True)


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(250))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    stage: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[dt.date] = mapped_column(Date, index=True)
    close_date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    original_close_date: Mapped[dt.date | None] = mapped_column(Date)
    close_date_changed_at: Mapped[dt.date | None] = mapped_column(Date)
    closed_at: Mapped[dt.date | None] = mapped_column(Date, index=True)
    outcome: Mapped[str | None] = mapped_column(String(10), index=True)
    discount_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(30))
    type: Mapped[str] = mapped_column(String(20), index=True)
    account: Mapped[Account] = relationship()
    owner: Mapped[User | None] = relationship()


class DealStageHistory(Base):
    __tablename__ = "deal_stage_history"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), index=True)
    stage: Mapped[str] = mapped_column(String(20))
    entered_at: Mapped[dt.date] = mapped_column(Date, index=True)


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"), index=True)
    type: Mapped[str] = mapped_column(String(10))
    direction: Mapped[str] = mapped_column(String(10))
    occurred_at: Mapped[dt.date] = mapped_column(Date, index=True)
    summary_text: Mapped[str | None] = mapped_column(Text)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    start: Mapped[dt.date] = mapped_column(Date, index=True)
    end: Mapped[dt.date | None] = mapped_column(Date, index=True)
    mrr: Mapped[float] = mapped_column(Numeric(14, 2))
    seats: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    renewal_date: Mapped[dt.date | None] = mapped_column(Date, index=True)


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    issued_date: Mapped[dt.date] = mapped_column(Date, index=True)
    due_date: Mapped[dt.date] = mapped_column(Date, index=True)
    paid_date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    due_date: Mapped[dt.date] = mapped_column(Date)
    paid_date: Mapped[dt.date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20))


class UsageDaily(Base):
    __tablename__ = "usage_daily"
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    active_users: Mapped[int] = mapped_column(Integer)
    key_feature_events: Mapped[int] = mapped_column(Integer)
    seats_purchased: Mapped[int] = mapped_column(Integer)
    __table_args__ = (Index("ix_usage_daily_date", "date"),)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    opened_at: Mapped[dt.date] = mapped_column(Date, index=True)
    resolved_at: Mapped[dt.date | None] = mapped_column(Date, index=True)
    severity: Mapped[int] = mapped_column(Integer, index=True)
    subject: Mapped[str] = mapped_column(String(300))
    body_text: Mapped[str | None] = mapped_column(Text)


class Embedding(Base):
    __tablename__ = "embeddings"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_table: Mapped[str] = mapped_column(String(30))
    source_id: Mapped[int] = mapped_column(Integer)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    vector: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM))
    __table_args__ = (
        UniqueConstraint("source_table", "source_id", name="uq_embeddings_source"),
    )


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[int] = mapped_column(Integer)
    model_name: Mapped[str] = mapped_column(String(50))
    model_version: Mapped[str] = mapped_column(String(50))
    score: Mapped[float] = mapped_column(Float)
    reasons_json: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        Index("ix_predictions_entity", "entity_type", "entity_id", "created_at"),
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(50))
    algorithm: Mapped[str] = mapped_column(String(50))
    trained_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    metrics_json: Mapped[Any] = mapped_column(JSON)
    artifact_path: Mapped[str] = mapped_column(String(400))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("model_name", "version", name="uq_model_version"),)


class ForecastSnapshot(Base):
    """Point-in-time copy of each open deal, so week-on-week changes can be explained."""

    __tablename__ = "forecast_snapshots"
    snapshot_date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), primary_key=True)
    quarter: Mapped[str] = mapped_column(String(7), index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    stage: Mapped[str] = mapped_column(String(20))
    close_date: Mapped[dt.date | None] = mapped_column(Date)
    p_win: Mapped[float] = mapped_column(Float)
    p_in_quarter: Mapped[float] = mapped_column(Float)
    in_quarter: Mapped[bool] = mapped_column(Boolean)


class CopilotAudit(Base):
    __tablename__ = "copilot_audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    tools_called_json: Mapped[Any] = mapped_column(JSON)
    answer: Mapped[str] = mapped_column(Text)
    cited_sources_json: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class DailyBrief(Base):
    __tablename__ = "daily_briefs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    brief_date: Mapped[dt.date] = mapped_column(Date, index=True)
    content_json: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("user_id", "brief_date", name="uq_brief_user_date"),)


class DataQualityRun(Base):
    __tablename__ = "data_quality_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    results_json: Mapped[Any] = mapped_column(JSON)


class LoadReject(Base):
    """Rows the loader quarantined (for example orphans) instead of silently dropping."""

    __tablename__ = "load_rejects"
    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(40), index=True)
    source_id: Mapped[str] = mapped_column(String(60))
    reason: Mapped[str] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint("table_name", "source_id", name="uq_load_reject"),)
