from datetime import datetime

import pytest

from app import clock
from app.data import db
from app.data.seed import SeedConfig, seed

T0 = datetime(2026, 3, 2, 9, 0)  # a Monday


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("EIR_LLM_MODE", "MOCK")
    monkeypatch.setenv("EIR_BACKOFF_BASE_SECONDS", "2")
    clock.freeze(T0)
    db.init_db(f"sqlite:///{tmp_path / 'test.db'}")
    yield
    clock.reset()


SMALL = dict(patients=30, practitioners=3, weeks=2, appointments=40, checkins=20, supply_items=10)


@pytest.fixture
def seeded(fresh_db):
    seed(SeedConfig(**SMALL, start=datetime(2026, 3, 9).date()))
    return None
