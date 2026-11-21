"""Health, readiness, metrics and dashboard endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.db import get_session
from backend.app.metrics import metrics
from backend.app.repositories.registry_repo import RegistryRepository

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@router.get("/readiness")
def readiness(session: Session = Depends(get_session)) -> dict:
    database_ok = False
    champion: str | None = None
    try:
        session.execute(text("SELECT 1"))
        database_ok = True
        row = RegistryRepository.current_champion(session)
        champion = row.version if row else None
    except Exception:
        database_ok = False
    return {
        "ready": bool(database_ok),
        "database": database_ok,
        "champion_version": champion,
    }


@router.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics(session: Session = Depends(get_session)) -> PlainTextResponse:
    try:
        champion = RegistryRepository.current_champion(session)
        if champion is not None:
            metrics.set_gauge(
                "champion_info", 1.0, {"version": champion.version, "algorithm": champion.algorithm}
            )
            if "f1" in champion.metrics:
                metrics.set_gauge("champion_f1", float(champion.metrics["f1"]))
            if "roc_auc" in champion.metrics:
                metrics.set_gauge("champion_roc_auc", float(champion.metrics["roc_auc"]))
        from backend.app.models.entities import (
            MonitoringWindow,
            Promotion,
            RetrainingDecision,
        )

        windows = session.query(MonitoringWindow).count()
        alerts = (
            session.query(MonitoringWindow)
            .filter(MonitoringWindow.alert.is_(True))
            .count()
        )
        metrics.set_gauge("monitoring_windows_total", float(windows))
        metrics.set_gauge("drift_alerts_total", float(alerts))
        retrain_count = (
            session.query(RetrainingDecision)
            .filter(RetrainingDecision.decision == "retrain")
            .count()
        )
        monitor_count = (
            session.query(RetrainingDecision)
            .filter(RetrainingDecision.decision == "monitor")
            .count()
        )
        metrics.set_gauge("retraining_decisions_retrain_total", float(retrain_count))
        metrics.set_gauge("retraining_decisions_monitor_total", float(monitor_count))
        promotions_completed = (
            session.query(Promotion).filter(Promotion.state == "COMPLETED").count()
        )
        metrics.set_gauge("promotions_completed_total", float(promotions_completed))
    except Exception:
        pass
    return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")


@router.get("/dashboard")
def dashboard() -> FileResponse:
    index = settings.frontend_dir / "index.html"
    if not index.exists():
        raise FileNotFoundError("frontend not found")
    return FileResponse(index, media_type="text/html")
