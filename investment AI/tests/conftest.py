from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app
from app.models.profile import HouseholdProfile


@pytest.fixture(scope="session")
def fixtures() -> dict:
    path = Path(__file__).resolve().parents[1] / "evals" / "households.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def household_2(fixtures) -> HouseholdProfile:
    row = next(h for h in fixtures["households"] if h["id"] == "2")
    return HouseholdProfile.model_validate(row["profile"])


@pytest.fixture
def client():
    init_db()
    with TestClient(app) as c:
        yield c
