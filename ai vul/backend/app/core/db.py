"""Database engine/session management (SQLAlchemy 2.x, synchronous).

PostgreSQL is the primary target. SQLite is supported for fast hermetic tests and for
running the API without Docker; the schema avoids PostgreSQL-only features except where
a portable variant exists (e.g. JSONB with a JSON fallback).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import JSON, MetaData, create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# JSONB on PostgreSQL, JSON elsewhere.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: dict[Any, Any] = {dict[str, Any]: JSONType, list[Any]: JSONType}


class _DB:
    engine: Engine | None = None
    factory: sessionmaker[Session] | None = None


_db = _DB()


def _make_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn: Any, _record: Any) -> None:  # pragma: no cover - trivial
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.close()

        return engine
    return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=10)


def configure_engine(url: str | None = None) -> Engine:
    """(Re)configure the global engine. Tests call this with an isolated database URL."""
    url = url or get_settings().database_url
    if _db.engine is not None:
        _db.engine.dispose()
    _db.engine = _make_engine(url)
    _db.factory = sessionmaker(bind=_db.engine, expire_on_commit=False, autoflush=False)
    return _db.engine


def get_engine() -> Engine:
    if _db.engine is None:
        configure_engine()
    assert _db.engine is not None
    return _db.engine


def SessionLocal() -> Session:
    if _db.factory is None:
        configure_engine()
    assert _db.factory is not None
    return _db.factory()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope for background work (agents, runners, seeders)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, committed by the service layer."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
