"""Shared pytest fixtures: isolated temp database and API test client."""
from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(PROJECT_ROOT, "backend")
for p in (PROJECT_ROOT, BACKEND):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["APP_DB_PATH"] = os.path.join(
    os.environ.get("TEMP", os.environ.get("TMP", "/tmp")), "opencode_p7_tests.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import dispose_engine, reset_db  # noqa: E402


def _purge() -> None:
    dispose_engine()
    base = os.environ["APP_DB_PATH"]
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(base + suffix)
        except OSError:
            pass


@pytest.fixture()
def client():
    _purge()
    reset_db()
    with TestClient(app_import()) as c:
        yield c
    dispose_engine()


@pytest.fixture(scope="module")
def module_client():
    _purge()
    reset_db()
    with TestClient(app_import()) as c:
        yield c
    dispose_engine()


def app_import():
    from app.main import app

    return app


@pytest.fixture()
def seeded_payload():
    from simulator.lab import build_lab_twin

    return build_lab_twin().to_dict()
