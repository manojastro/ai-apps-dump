"""Test harness: a real Postgres, the real pipeline, an isolated test database.

Tests use real Postgres and pgvector, not SQLite, because behaviour such as upserts and
vector search is exactly what they need to prove. The URL must contain "test", since this
fixture wipes the database.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from dotenv import dotenv_values

BACKEND = Path(__file__).resolve().parents[1]
_devdb = dotenv_values(BACKEND / ".env.devdb")
TEST_URL = os.environ.get("TEST_DATABASE_URL") or _devdb.get("TEST_DATABASE_URL")
if not TEST_URL or "test" not in TEST_URL:
    raise RuntimeError("Set TEST_DATABASE_URL to a database whose name contains 'test'.")

_tmp = Path(tempfile.mkdtemp(prefix="revenueos-test-"))
TEST_PASSWORD = "test-only-password"
os.environ.update({
    "DATABASE_URL": TEST_URL,
    "DEMO_USER_PASSWORD": TEST_PASSWORD,
    "JWT_SECRET": "test-only-secret-with-enough-length-for-hs256",
    "ANTHROPIC_API_KEY": "",
    "DATA_DIR": str(_tmp / "data"),
    "ARTIFACT_DIR": str(_tmp / "artifacts"),
    "ENABLE_SCHEDULER": "false",
    "COPILOT_RATE_LIMIT_PER_MINUTE": "1000",
    "MLFLOW_TRACKING_URI": "",
})

# Imported after the environment is set, so settings pick up the test values.
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.connectors.synthetic import SyntheticCsvConnector  # noqa: E402
from app.copilot import rag  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.security import create_token  # noqa: E402
from app.db.session import session_factory  # noqa: E402
from app.jobs.scheduler import refresh_scores_and_briefs  # noqa: E402
from app.main import app  # noqa: E402
from app.ml import forecast_sim, train_churn, train_win  # noqa: E402
from app.ml.features import load_frames  # noqa: E402
from scripts import data_quality, generate_synthetic_data, load_data  # noqa: E402

CRO, REVOPS, ADMIN = 1, 2, 3
MANAGER_NA, CSM_NA = 4, 6
MANAGER_EMEA = 7


@pytest.fixture(scope="session")
def pipeline() -> dict:
    """Build the whole system once and share the results across tests."""
    settings = get_settings()
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "app" / "db" / "migrations"))
    command.upgrade(config, "head")
    load_data.reset_data()

    generate_synthetic_data.write_dataset(settings.data_dir, settings.data_as_of)
    connector = SyntheticCsvConnector(settings.data_dir)
    counts = load_data.load(connector)
    quality = data_quality.run_checks(connector, settings.data_as_of)
    data_quality.save(quality)
    with session_factory()() as session:
        rag.build_index(session)

    frames = load_frames()
    win = train_win.train(frames, settings.data_as_of)
    churn = train_churn.train(frames, settings.data_as_of)
    backtest = forecast_sim.backtest(frames, settings.data_as_of, win["selected_algorithm"])
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    import json

    (settings.artifact_dir / "forecast_backtest.json").write_text(json.dumps(backtest))
    refresh = refresh_scores_and_briefs()
    return {
        "counts": counts, "quality": quality, "frames": frames, "win": win, "churn": churn,
        "backtest": backtest, "refresh": refresh, "connector": connector, "settings": settings,
    }


@pytest.fixture(scope="session")
def client(pipeline) -> TestClient:
    return TestClient(app)


@pytest.fixture
def db(pipeline):
    with session_factory()() as session:
        yield session


def auth(user_id: int, role: str = "cro") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, role)}"}
