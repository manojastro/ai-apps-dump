"""Test harness: a fresh PostgreSQL test database built by migrations, temp storage, demo agent mode."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "documents"


def _test_db_url() -> str:
    url = os.environ.get("SPREADLENS_TEST_DATABASE_URL")
    if not url:
        env = Path(__file__).resolve().parents[1] / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("SPREADLENS_TEST_DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
    if not url:
        from spreadlens.devdb import start, write_env

        base = start()
        write_env(base)
        url = f"{base}/spreadlens_test"
    return url


@pytest.fixture(scope="session", autouse=True)
def _env():
    storage = tempfile.mkdtemp(prefix="spreadlens-test-")
    os.environ.update({
        "SPREADLENS_ENV": "test", "SPREADLENS_DATABASE_URL": _test_db_url(), "SPREADLENS_STORAGE_ROOT": storage,
        "SPREADLENS_AGENT_MODE": "demo", "SPREADLENS_RUN_WORKER_IN_API": "false", "SPREADLENS_SEED_PASSWORD": "test-pass-123",
        "SPREADLENS_AGENT_TOOL_TOKEN": "test-tool-token",
    })
    from spreadlens.config import get_settings
    from spreadlens.db import reset_engine_cache
    from spreadlens.storage.base import reset_storage

    get_settings.cache_clear()
    reset_engine_cache()
    reset_storage()
    yield
    shutil.rmtree(storage, ignore_errors=True)


@pytest.fixture(scope="session")
def db_ready(_env):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from spreadlens.db import get_engine, session_scope
    from spreadlens.seed import seed

    eng = get_engine()
    with eng.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    cfg.set_main_option("sqlalchemy.url", os.environ["SPREADLENS_DATABASE_URL"])
    command.upgrade(cfg, "head")
    with session_scope() as db:
        return seed(db)


@pytest.fixture(scope="session")
def client(db_ready):
    from fastapi.testclient import TestClient

    from spreadlens.main import app

    with TestClient(app) as c:
        yield c


def login(client, email: str) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": "test-pass-123"})
    assert r.status_code == 200, r.text
    return {"authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="session")
def analyst(client):
    return login(client, "analyst@demo.local")


@pytest.fixture(scope="session")
def reviewer(client):
    return login(client, "reviewer@demo.local")


@pytest.fixture(scope="session")
def admin(client):
    return login(client, "admin@demo.local")


@pytest.fixture(scope="session")
def other(client):
    return login(client, "other@demo.local")


@pytest.fixture(scope="session")
def workspace_id(db_ready):
    return db_ready["Demo Credit Team"]


def drain() -> None:
    from spreadlens.config import get_settings
    from spreadlens.workflow.worker import Worker

    Worker(get_settings()).drain()


def new_company(client, headers, workspace_id: str, name: str) -> str:
    r = client.post(f"/api/workspaces/{workspace_id}/companies", headers=headers, json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def upload(client, headers, company_id: str, fixture: str) -> dict:
    media = "application/pdf" if fixture.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    with open(FIXTURES / fixture, "rb") as f:
        r = client.post(f"/api/companies/{company_id}/documents", headers=headers, files={"file": (fixture, f, media)})
    assert r.status_code == 201, r.text
    return r.json()
