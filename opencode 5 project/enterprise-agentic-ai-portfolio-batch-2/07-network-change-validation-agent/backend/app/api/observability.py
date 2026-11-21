"""Health, readiness, metrics and dashboard endpoints."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.metrics import METRICS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
router = APIRouter(tags=["observability"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "network-twin-validation-agent"}


@router.get("/readiness")
def readiness(session: Session = Depends(get_db)) -> dict[str, object]:
    checks: dict[str, bool] = {}
    try:
        session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        from simulator.lab import build_lab_twin

        build_lab_twin()
        checks["twin_seed"] = True
    except Exception:
        checks["twin_seed"] = False
    ready = all(checks.values())
    return {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
        "llm_mode": os.environ.get("LLM_MODE", "mock"),
    }


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=METRICS.render(), media_type="text/plain; version=0.0.4")


@router.get("/dashboard")
def dashboard() -> Response:
    index = PROJECT_ROOT / "frontend" / "index.html"
    if not index.exists():
        return Response(content="<h1>dashboard missing</h1>", media_type="text/html")
    return Response(content=index.read_text(encoding="utf-8"), media_type="text/html")
