from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import PROJECT_ROOT, Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url="sqlite://",
        policy_path=str(PROJECT_ROOT / "config" / "policies.yaml"),
        seed_on_start=False,
    )


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings, seed=False)) as value:
        yield value


@pytest.fixture
def auth():
    return {"Authorization": "Bearer demo-operator-token", "X-CSRF-Token": "demo-csrf-token"}
