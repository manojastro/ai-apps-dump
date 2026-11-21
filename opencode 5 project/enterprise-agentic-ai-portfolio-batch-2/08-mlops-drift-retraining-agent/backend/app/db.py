"""Database engine, session factory and schema lifecycle helpers."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.app.config import settings

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, future=True
)
Base = declarative_base()


def get_session() -> Iterator[Session]:
    """Yield a scoped session for request handlers."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    from backend.app.models import entities

    Base.metadata.create_all(bind=engine)


def reset_database() -> None:
    """Drop and recreate every table, clearing artifacts and window data."""
    from backend.app.models import entities

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    for path in settings.artifacts_dir.glob("*"):
        path.unlink(missing_ok=True)
    for path in settings.window_data_dir.glob("*"):
        path.unlink(missing_ok=True)
