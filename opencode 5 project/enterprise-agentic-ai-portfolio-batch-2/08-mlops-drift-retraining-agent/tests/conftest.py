"""Shared pytest fixtures: isolated temp database per test session."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

_TMP = tempfile.mkdtemp(prefix="drift-agent-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP).as_posix()}/test.db"
os.environ["ARTIFACTS_DIR"] = str(Path(_TMP) / "artifacts")
os.environ["WINDOW_DATA_DIR"] = str(Path(_TMP) / "windows")
os.environ["LLM_MODE"] = "mock"

import pytest
from fastapi.testclient import TestClient

from backend.app.db import get_session, init_db, reset_database, SessionLocal
from backend.app.main import app


@pytest.fixture(scope="session", autouse=True)
def database() -> None:
    init_db()
    yield


@pytest.fixture()
def fresh_db() -> None:
    reset_database()
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def trained_baseline(client):
    response = client.post(
        "/api/v1/models/train-baseline", json={"seed": 42, "n_samples": 3000}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture()
def evaluated_window(client, trained_baseline):
    def _make(knobs: dict | None = None, seed: int = 1001, name: str = "w") -> dict:
        window = client.post(
            "/api/v1/monitoring/windows",
            json={"name": name, "n_samples": 2500, "seed": seed, "knobs": knobs or {}},
        ).json()
        evaluation = client.post(
            f"/api/v1/monitoring/windows/{window['id']}/evaluate", json={}
        ).json()
        return {"window": window, "evaluation": evaluation}

    return _make


def override_session_dependency():
    """Yield a session from the same engine used by direct service calls."""
    from backend.app.db import SessionLocal as SL

    db = SL()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_session_dependency
