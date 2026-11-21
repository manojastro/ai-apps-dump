"""One command that rebuilds everything: data, index, models, forecast and briefs.

This is a full demo rebuild. It empties every table first, including the copilot audit
log, because upserts alone would leave rows from any earlier dataset mixed in. For a
routine refresh use `scripts.load_data`, which only upserts.

Run: uv run python -m scripts.build_all
"""
from __future__ import annotations

import json
import time

from alembic import command
from alembic.config import Config

from app.connectors.synthetic import SyntheticCsvConnector
from app.copilot import rag
from app.core.config import BACKEND_DIR, get_settings
from app.db.session import session_factory
from app.jobs.scheduler import refresh_scores_and_briefs
from app.ml import forecast_sim, train_churn, train_win
from app.ml.common import load_active
from app.ml.features import load_frames
from scripts import data_quality, generate_synthetic_data, load_data


def step(name: str, started: list[float]) -> None:
    now = time.perf_counter()
    print(f"[{now - started[0]:6.1f}s] {name}", flush=True)
    started[0] = now


def main() -> None:
    settings = get_settings()
    clock = [time.perf_counter()]

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "app" / "db" / "migrations"))
    command.upgrade(config, "head")
    load_data.reset_data()
    step("migrations and reset", clock)

    generate_synthetic_data.write_dataset(settings.data_dir, settings.data_as_of)
    step("synthetic data generated", clock)

    connector = SyntheticCsvConnector(settings.data_dir)
    load_data.load(connector)
    step("data loaded", clock)

    results = data_quality.run_checks(connector, settings.data_as_of)
    data_quality.save(results)
    step(f"data quality: {results['summary']}", clock)

    with session_factory()() as session:
        indexed = rag.build_index(session)
    step(f"embeddings indexed: {indexed}", clock)

    frames = load_frames()
    win = train_win.train(frames, settings.data_as_of)
    step(f"win model trained: {win['selected_algorithm']}", clock)
    churn = train_churn.train(frames, settings.data_as_of)
    step(f"churn model trained: {churn['selected_algorithm']}", clock)

    algorithm = load_active(train_win.MODEL_NAME)["algorithm"]
    backtest = forecast_sim.backtest(frames, settings.data_as_of, algorithm)
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    (settings.artifact_dir / "forecast_backtest.json").write_text(json.dumps(backtest, indent=2))
    step("forecast back-test", clock)

    print(refresh_scores_and_briefs())
    step("scores, snapshots and briefs", clock)


if __name__ == "__main__":
    main()
