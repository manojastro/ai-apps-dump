import os
import time
import uuid
from pathlib import Path

from sqlalchemy import JSON, Float, ForeignKey, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATA = Path(os.environ.get("PRODUCTIONLENS_DATA", ".productionlens"))
DATA.mkdir(exist_ok=True, parents=True)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA / 'platform.db'}")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Session = sessionmaker(engine, expire_on_commit=False)

if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_setup(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)


class User(Record, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(30), default="viewer")


class LoginSession(Record, Base):
    __tablename__ = "sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[float] = mapped_column(Float)


class Incident(Record, Base):
    __tablename__ = "incidents"
    title: Mapped[str] = mapped_column(String(250))
    service: Mapped[str] = mapped_column(String(50), default="checkout")
    severity: Mapped[str] = mapped_column(String(10), default="P2")
    mode: Mapped[str] = mapped_column(String(20), default="replay")
    status: Mapped[str] = mapped_column(String(30), default="open")
    description: Mapped[str] = mapped_column(String(4000), default="")
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))


class Run(Record, Base):
    __tablename__ = "investigation_runs"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[dict] = mapped_column(JSON, default=dict)


class RunEvent(Record, Base):
    __tablename__ = "run_events"
    run_id: Mapped[str] = mapped_column(ForeignKey("investigation_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(4000))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class EvidenceRow(Record, Base):
    __tablename__ = "evidence"
    run_id: Mapped[str] = mapped_column(ForeignKey("investigation_runs.id"), index=True)
    data: Mapped[dict] = mapped_column(JSON)


class Action(Record, Base):
    __tablename__ = "action_proposals"
    run_id: Mapped[str] = mapped_column(ForeignKey("investigation_runs.id"), unique=True)
    proposal: Mapped[dict] = mapped_column(JSON)
    digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    expires_at: Mapped[float] = mapped_column(Float)
    reviewer: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict)


class Execution(Record, Base):
    __tablename__ = "action_executions"
    action_id: Mapped[str] = mapped_column(ForeignKey("action_proposals.id"), unique=True)
    result: Mapped[dict] = mapped_column(JSON)


class Job(Record, Base):
    __tablename__ = "jobs"
    kind: Mapped[str] = mapped_column(String(30))
    target_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    owner: Mapped[str] = mapped_column(String(64), default="")
    attempts: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Evaluation(Record, Base):
    __tablename__ = "evaluation_runs"
    mode: Mapped[str] = mapped_column(String(20), default="replay")
    status: Mapped[str] = mapped_column(String(30), default="queued")
    config: Mapped[dict] = mapped_column(JSON)
    report: Mapped[dict] = mapped_column(JSON, default=dict)


class CaseResult(Record, Base):
    __tablename__ = "case_results"
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    data: Mapped[dict] = mapped_column(JSON)


class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


class Audit(Record, Base):
    __tablename__ = "audit_events"
    actor: Mapped[str] = mapped_column(String(100))
    operation: Mapped[str] = mapped_column(String(100))
    target: Mapped[str] = mapped_column(String(100))
    data: Mapped[dict] = mapped_column(JSON, default=dict)


def add_event(db, run_id, kind, message, payload=None):
    db.add(RunEvent(run_id=run_id, kind=kind, message=message, payload=payload or {}))


def serialize(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}
