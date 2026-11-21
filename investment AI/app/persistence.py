from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class HouseholdRow(Base):
    __tablename__ = "households"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProfileRow(Base):
    __tablename__ = "profiles"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    payload: Mapped[str] = mapped_column(Text)


class GoalRow(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    payload: Mapped[str] = mapped_column(Text)


class HoldingRow(Base):
    __tablename__ = "holdings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    payload: Mapped[str] = mapped_column(Text)


class IpsVersionRow(Base):
    __tablename__ = "ips_versions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id"))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlanJobRow(Base):
    __tablename__ = "plan_jobs"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    events: Mapped[str] = mapped_column(Text, default="[]")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlanRow(Base):
    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    household_id: Mapped[str] = mapped_column(String(40), default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    selected: Mapped[str] = mapped_column(String(20), default="")
    payload: Mapped[str] = mapped_column(Text)
    snapshot_id: Mapped[str] = mapped_column(String(40), default="")
    rules_version: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlanScenarioRow(Base):
    __tablename__ = "plan_scenarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"))
    name: Mapped[str] = mapped_column(String(20))
    payload: Mapped[str] = mapped_column(Text)


class RegulatorySnapshotRow(Base):
    __tablename__ = "regulatory_snapshots"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MarketSnapshotRow(Base):
    __tablename__ = "market_snapshots"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceRecordRow(Base):
    __tablename__ = "source_records"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(40), default="")
    payload: Mapped[str] = mapped_column(Text)


class RiskFindingRow(Base):
    __tablename__ = "risk_findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[str] = mapped_column(Text)


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event: Mapped[str] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    plan_id: Mapped[str] = mapped_column(String(40), default="")
    component: Mapped[str] = mapped_column(String(64), default="")
    metadata_json: Mapped[str] = mapped_column("metadata", Text, default="{}")


class PdfArtifactRow(Base):
    __tablename__ = "pdf_artifacts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(40), index=True)
    path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
