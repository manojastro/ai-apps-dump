"""Database engines and tenant-scoped sessions.

The runtime uses a non-owner role so PostgreSQL row-level security applies. Every tenant-scoped
transaction sets app.tenant_id with set_config(..., is_local => true); RLS policies compare
against it. The tenant ID always comes from the authenticated server-side session or a job row,
never from client input.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


@lru_cache
def app_engine() -> Engine:
    s = get_settings()
    return create_engine(s.app_database_url, pool_pre_ping=True, pool_size=10, max_overflow=10)


@lru_cache
def owner_engine() -> Engine:
    s = get_settings()
    return create_engine(s.app_migration_database_url, pool_pre_ping=True, pool_size=2)


@lru_cache
def _factory() -> sessionmaker[Session]:
    return sessionmaker(bind=app_engine(), expire_on_commit=False)


def set_tenant(session: Session, tenant_id: uuid.UUID | str) -> None:
    session.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})


@contextmanager
def tenant_session(tenant_id: uuid.UUID | str) -> Iterator[Session]:
    """A transaction bound to one tenant. Commits on success."""
    session = _factory()()

    # Re-apply the tenant setting at the start of every transaction, including after a mid-block commit.
    @event.listens_for(session, "after_begin")
    def _apply(sess, transaction, connection):  # noqa: ARG001
        connection.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})

    try:
        session.begin()
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def global_session() -> Iterator[Session]:
    """A transaction with no tenant context: only non-tenant tables (users, sessions, jobs) are visible."""
    session = _factory()()
    try:
        session.begin()
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
