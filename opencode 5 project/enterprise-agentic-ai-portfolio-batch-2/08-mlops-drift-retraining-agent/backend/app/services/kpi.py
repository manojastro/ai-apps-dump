"""KPI computation and snapshot persistence."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.entities import (
    CandidateEvaluation,
    MonitoringWindow,
    Promotion,
    RetrainingDecision,
    RollbackRecord,
)
from backend.app.repositories.decision_repo import KpiRepository
from backend.app.repositories.registry_repo import RegistryRepository


def compute_kpis(session: Session) -> dict:
    """Aggregate platform KPIs from persisted state."""
    windows = [
        w for w in session.query(MonitoringWindow).order_by(MonitoringWindow.id).all()
    ]
    evaluated = [w for w in windows if w.evaluated]
    alerts = [w for w in evaluated if w.alert]
    decisions = list(session.query(RetrainingDecision).all())
    retrain_decisions = [d for d in decisions if d.decision == "retrain"]
    monitor_decisions = [d for d in decisions if d.decision == "monitor"]
    evaluations = list(session.query(CandidateEvaluation).all())
    rejected = [e for e in evaluations if e.verdict == "reject"]
    passed = [e for e in evaluations if e.verdict == "pass"]
    promotions = list(session.query(Promotion).all())
    completed = [p for p in promotions if p.state == "COMPLETED"]
    rollbacks = list(session.query(RollbackRecord).all())

    clean_windows = [
        w for w in evaluated if not (w.knobs or {}).get("mean_shift")
        and not (w.knobs or {}).get("label_noise")
        and not (w.knobs or {}).get("category_redistribution")
        and not (w.knobs or {}).get("missingness_rate")
    ]
    false_alerts = [w for w in clean_windows if w.alert]

    time_to_detection = None
    for index, window in enumerate(evaluated, start=1):
        if window.alert:
            time_to_detection = index
            break

    champion = RegistryRepository.current_champion(session)
    payload = {
        "windows_submitted": len(windows),
        "windows_evaluated": len(evaluated),
        "alerts_total": len(alerts),
        "alert_rate": round(len(alerts) / len(evaluated), 4) if evaluated else 0.0,
        "false_alert_rate": round(len(false_alerts) / len(clean_windows), 4)
        if clean_windows
        else 0.0,
        "time_to_detection_windows": time_to_detection,
        "retraining_decisions_retrain": len(retrain_decisions),
        "retraining_decisions_monitor": len(monitor_decisions),
        "candidates_trained": len({e.version for e in evaluations}),
        "candidates_passed": len(passed),
        "candidates_rejected_bad_model_prevention": len(rejected),
        "promotions_completed": len(completed),
        "rollbacks": len(rollbacks),
        "champion_version": champion.version if champion else None,
        "champion_metrics": champion.metrics if champion else {},
    }
    return payload


def snapshot_kpis(session: Session) -> dict:
    """Compute and persist a KPI snapshot."""
    payload = compute_kpis(session)
    KpiRepository.save(session, payload)
    return payload
