"""Monitoring window submission and evaluation result endpoints."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.errors import DomainError
from backend.app.config import settings
from backend.app.db import get_session
from backend.app.ml.data_generator import DriftKnobs, generate_customer_data
from backend.app.repositories.decision_repo import InvestigationRepository
from backend.app.repositories.results_repo import (
    ResultsRepository,
    WindowRepository,
)
from backend.app.schemas.dto import EvaluateWindowOutput, WindowCreateRequest, WindowCreatedResponse
from backend.app.tools.registry_tools import get_default_registry

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.post("/windows", response_model=WindowCreatedResponse)
def post_window(
    request: WindowCreateRequest, session: Session = Depends(get_session)
) -> WindowCreatedResponse:
    seed = request.seed if request.seed is not None else int(np.random.default_rng().integers(0, 2**31 - 1))
    knobs = DriftKnobs.from_dict(request.knobs)
    frame = generate_customer_data(request.n_samples, seed=seed, knobs=knobs)
    row = WindowRepository.create(
        session,
        name=request.name or f"window-step-{request.step}" if request.step else request.name or "window",
        step=request.step,
        n_samples=int(len(frame)),
        seed=seed,
        knobs=knobs.to_dict(),
        data_path="",
    )
    data_path = Path(settings.window_data_dir) / f"window_{row.id}.csv"
    frame.to_csv(data_path, index=False)
    row.data_path = str(data_path)
    session.commit()
    return WindowCreatedResponse(
        id=row.id, name=row.name, n_samples=row.n_samples, seed=seed, knobs=knobs.to_dict()
    )


@router.post("/windows/{window_id}/evaluate", response_model=EvaluateWindowOutput)
def post_evaluate_window(
    window_id: int, session: Session = Depends(get_session)
) -> EvaluateWindowOutput:
    registry = get_default_registry()
    output = registry.invoke(session, "evaluate_window_tool", {"window_id": window_id})
    return EvaluateWindowOutput(**output)


def _window_id_or_latest(session: Session, window_id: int | None) -> int:
    if window_id is not None:
        return window_id
    latest = WindowRepository.latest(session)
    if latest is None:
        raise DomainError(404, "no evaluated windows yet")
    return latest.id


@router.get("/latest")
def get_latest(session: Session = Depends(get_session)) -> dict:
    latest = WindowRepository.latest(session)
    if latest is None:
        raise DomainError(404, "no evaluated windows yet")
    drift = ResultsRepository.drift_for_window(session, latest.id)
    perf = ResultsRepository.performance_for_window(session, latest.id)
    fairness = ResultsRepository.fairness_for_window(session, latest.id)
    quality = ResultsRepository.quality_for_window(session, latest.id)
    pred_stat = ResultsRepository.prediction_stat_for_window(session, latest.id)
    investigation = InvestigationRepository.for_window(session, latest.id)
    decision_rows = [
        d for d in _decisions_desc(session) if d.window_id == latest.id
    ]
    return {
        "id": latest.id,
        "name": latest.name,
        "step": latest.step,
        "n_samples": latest.n_samples,
        "knobs": latest.knobs,
        "alert": latest.alert,
        "evaluated": latest.evaluated,
        "drift": [_drift_dict(d) for d in drift],
        "performance": _perf_dict(perf),
        "fairness": _fairness_dict(fairness),
        "quality": [{"check_name": q.check_name, "passed": q.passed, "value": q.value} for q in quality],
        "prediction_stats": _pred_stat_dict(pred_stat),
        "investigation": {
            "incident_id": investigation.incident_id,
            "root_cause": investigation.root_cause,
            "confidence": investigation.confidence,
        }
        if investigation
        else None,
        "decision": _decision_dict(decision_rows[0]) if decision_rows else None,
    }


def _decisions_desc(session: Session):
    from backend.app.models.entities import RetrainingDecision

    return list(
        session.query(RetrainingDecision).order_by(RetrainingDecision.id.desc()).all()
    )


@router.get("/drift")
def get_drift(
    window_id: int | None = Query(default=None), session: Session = Depends(get_session)
) -> dict:
    wid = _window_id_or_latest(session, window_id)
    rows = ResultsRepository.drift_for_window(session, wid)
    return {"window_id": wid, "results": [_drift_dict(r) for r in rows]}


@router.get("/performance")
def get_performance(
    window_id: int | None = Query(default=None), session: Session = Depends(get_session)
) -> dict:
    if window_id is not None:
        rows = [ResultsRepository.performance_for_window(session, window_id)]
        rows = [r for r in rows if r is not None]
    else:
        rows = ResultsRepository.performance_history(session)
    return {"results": [_perf_dict(r) for r in rows if r is not None]}


@router.get("/fairness")
def get_fairness(
    window_id: int | None = Query(default=None), session: Session = Depends(get_session)
) -> dict:
    wid = _window_id_or_latest(session, window_id)
    row = ResultsRepository.fairness_for_window(session, wid)
    return {"window_id": wid, "fairness": _fairness_dict(row)}


@router.get("/quality")
def get_quality(
    window_id: int | None = Query(default=None), session: Session = Depends(get_session)
) -> dict:
    wid = _window_id_or_latest(session, window_id)
    rows = ResultsRepository.quality_for_window(session, wid)
    return {
        "window_id": wid,
        "checks": [
            {"check_name": r.check_name, "passed": r.passed, "value": r.value, "details": r.details}
            for r in rows
        ],
    }


def _drift_dict(row) -> dict:
    return {
        "feature": row.feature,
        "feature_type": row.feature_type,
        "psi": row.psi,
        "ks_statistic": row.ks_statistic,
        "p_value": row.p_value,
        "tv_delta": row.tv_delta,
        "missing_delta": row.missing_delta,
        "drifted": row.drifted,
        "severity": row.severity,
    }


def _perf_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "window_id": row.window_id,
        "model_version": row.model_version,
        "accuracy": row.accuracy,
        "precision": row.precision,
        "recall": row.recall,
        "f1": row.f1,
        "roc_auc": row.roc_auc,
        "brier": row.brier,
        "latency_ms": row.latency_ms,
    }


def _fairness_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "window_id": row.window_id,
        "segment_column": row.segment_column,
        "selection_rates": row.selection_rates,
        "disparity_ratio": row.disparity_ratio,
        "threshold": row.threshold,
        "passed": row.passed,
    }


def _pred_stat_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "n_predictions": row.n_predictions,
        "positive_rate": row.positive_rate,
        "baseline_positive_rate": row.baseline_positive_rate,
        "absolute_delta": row.absolute_delta,
        "drifted": row.drifted,
    }


def _decision_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "decision": row.decision,
        "reasons": row.reasons,
        "gate_inputs": row.gate_inputs,
        "projected_benefit": row.projected_benefit,
    }
