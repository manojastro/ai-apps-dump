"""Test fixtures.

A fully seeded simulated enterprise (including historical LangGraph runs) is built once per
session into a SQLite file, then copied for each test module so tests are isolated yet fast.
Set TEST_DATABASE_URL to a PostgreSQL URL to run the API/workflow suites against PostgreSQL.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.update(
    {
        "APP_ENV": "test",
        "AI_PROVIDER": "mock",
        "SERVICENOW_MODE": "mock",
        "THREAT_INTEL_MODE": "offline",
        "LOG_JSON": "false",
        "LOG_LEVEL": "WARNING",
        "SEED_ON_START": "false",
        "ENABLE_SERVICENOW_WRITES": "false",
        "SECRET_KEY": "test-secret-key-that-is-long-enough-123456",
    }
)

from app.core.config import get_settings

get_settings.cache_clear()

from app.core import db as dbmod  # noqa: E402
from app.core.db import Base, configure_engine  # noqa: E402
from app.graphs.runner import WorkflowRunner, make_checkpointer, set_runner  # noqa: E402

DEMO_PASSWORD = "AegisDemo!2026"


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


@pytest.fixture(scope="session")
def seeded_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("seed") / "base.db"
    url = _sqlite_url(base)
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    configure_engine(url)
    import app.models  # noqa: F401

    Base.metadata.create_all(dbmod.get_engine())
    from app.seed.seed import seed_all

    seed_all(with_history=True)
    set_runner(None)
    with dbmod.get_engine().connect() as conn:
        conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
    dbmod.get_engine().dispose()
    cp = base.with_name("base_checkpoints.db")
    if cp.exists():
        c = sqlite3.connect(cp)
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        c.close()
    return base


@pytest.fixture(scope="module")
def seeded_db(seeded_template: Path, tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """A private copy of the seeded database (and its LangGraph checkpoints) for one test module."""
    target_dir = tmp_path_factory.mktemp("db")
    target = target_dir / "aegis.db"
    shutil.copy(seeded_template, target)
    cp = seeded_template.with_name("base_checkpoints.db")
    if cp.exists():
        shutil.copy(cp, target_dir / "aegis_checkpoints.db")
    url = _sqlite_url(target)
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    configure_engine(url)
    saver, _ = make_checkpointer(url)
    runner = WorkflowRunner(checkpointer=saver, synchronous=True)
    set_runner(runner)
    yield url
    set_runner(None)
    dbmod.get_engine().dispose()


@pytest.fixture()
def db(seeded_db: str) -> Iterator:
    session = dbmod.SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module")
def client(seeded_db: str) -> Iterator:
    from fastapi.testclient import TestClient

    from app.api.routes_auth import login_limiter
    from app.main import create_app

    login_limiter.reset()
    with TestClient(create_app()) as c:
        yield c


def login(client, email: str) -> dict[str, str]:
    from app.api.routes_auth import login_limiter

    login_limiter.reset()
    r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD, "include_token": True})
    assert r.status_code == 200, r.text
    client.cookies.clear()  # tests authenticate with explicit bearer headers only
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def analyst_h(client) -> dict[str, str]:
    return login(client, "analyst@northstar.example")


@pytest.fixture(scope="module")
def approver_h(client) -> dict[str, str]:
    return login(client, "approver@northstar.example")


@pytest.fixture(scope="module")
def viewer_h(client) -> dict[str, str]:
    return login(client, "viewer@northstar.example")


@pytest.fixture(scope="module")
def admin_h(client) -> dict[str, str]:
    return login(client, "admin@northstar.example")


def principal(db, email: str):
    from sqlalchemy import select

    from app.models.identity import User
    from app.security.auth import Principal

    return Principal.from_user(db.scalar(select(User).where(User.email == email)))


def finding_id(db, hostname: str, cve: str) -> str:
    from sqlalchemy import select

    from app.models.vulnerability import Finding, Vulnerability

    f = db.scalar(
        select(Finding)
        .join(Vulnerability)
        .where(Vulnerability.cve_id == cve, Finding.reported_asset_identifier.like(f"{hostname}%"))
    )
    assert f is not None, f"{hostname}/{cve}"
    return f.id
