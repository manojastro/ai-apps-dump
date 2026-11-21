"""Scheduled jobs: daily score refresh, forecast snapshots and briefs.

A single in-process scheduler suits one API replica. With several replicas this should
move to one dedicated worker, or every replica would run the job.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import session_factory
from app.ml import train_churn, train_win
from app.ml.features import load_frames
from app.services import briefing, forecast

logger = logging.getLogger(__name__)


def refresh_scores_and_briefs() -> dict[str, int]:
    """Re-score with the active models, then rebuild snapshots and briefs."""
    as_of = get_settings().data_as_of
    frames = load_frames()
    results = {
        "deals_scored": train_win.store_scores(frames, as_of),
        "accounts_scored": train_churn.store_scores(frames, as_of),
    }
    with session_factory()() as session:
        results["snapshot_rows"] = forecast.write_snapshots(session, frames, as_of)
        results["briefs"] = briefing.generate_all(session, as_of)
    logger.info("daily_refresh", extra={"fields": results})
    return results


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        refresh_scores_and_briefs, "cron", hour=6, minute=0, id="daily_refresh",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
