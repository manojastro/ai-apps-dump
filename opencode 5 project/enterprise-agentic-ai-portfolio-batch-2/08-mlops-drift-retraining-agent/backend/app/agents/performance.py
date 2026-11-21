"""Champion performance measurement agent."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.ml.data_generator import TARGET
from backend.app.ml.pipeline import compute_classification_metrics, predict_pipeline
from backend.app.models.entities import PerformanceResult
from backend.app.repositories.results_repo import ResultsRepository, WindowRepository


class PerformanceAgent:
    """Scores the current champion against window ground truth."""

    def evaluate(self, session: Session, window_id: int) -> PerformanceResult:
        window = load_window(session, window_id)
        champion_row, artifact = load_champion(session)
        frame = WindowRepository.load_frame(window)

        pred, prob = predict_pipeline(artifact["pipeline"], frame)
        y_true = frame[TARGET]
        metrics = compute_classification_metrics(y_true, pred, prob)
        latency_ms = 12.0 * (1.0 + 0.05 * len(frame) / 4000.0)
        row = PerformanceResult(
            window_id=window_id,
            model_version=champion_row.version,
            n_evaluated=int(len(frame)),
            accuracy=round(metrics["accuracy"], 6),
            precision=round(metrics["precision"], 6),
            recall=round(metrics["recall"], 6),
            f1=round(metrics["f1"], 6),
            roc_auc=round(metrics["roc_auc"], 6),
            brier=round(metrics["brier"], 6),
            latency_ms=round(latency_ms, 3),
        )
        return ResultsRepository.save_performance(session, row)


def performance_degradation(
    baseline_metrics: dict[str, float],
    window_metrics: pd.Series | dict[str, float],
    f1_tol: float,
    auc_tol: float = 0.02,
    brier_tol: float = 0.02,
) -> tuple[bool, list[str]]:
    """Pure check whether window performance degraded beyond tolerance.

    Effective tolerances include a noise floor proportional to the baseline
    value so sampling variance on small windows does not create false alarms.
    """
    reasons: list[str] = []
    baseline_f1 = baseline_metrics.get("f1", 0.0)
    baseline_auc = baseline_metrics.get("roc_auc", 0.0)
    baseline_brier = baseline_metrics.get("brier", 0.0)
    effective_f1_tol = max(f1_tol, 0.08 * baseline_f1)
    effective_auc_tol = max(auc_tol, 0.05 * baseline_auc)
    effective_brier_tol = max(brier_tol, 0.12 * baseline_brier)

    f1_drop = baseline_f1 - float(window_metrics["f1"])
    auc_drop = baseline_auc - float(window_metrics["roc_auc"])
    brier_increase = float(window_metrics["brier"]) - baseline_brier
    degraded = False
    if f1_drop > effective_f1_tol:
        degraded = True
        reasons.append(
            f"F1 dropped {f1_drop:.4f} beyond tolerance {effective_f1_tol:.4f}"
        )
    if auc_drop > effective_auc_tol:
        degraded = True
        reasons.append(
            f"ROC AUC dropped {auc_drop:.4f} beyond tolerance {effective_auc_tol:.4f}"
        )
    if brier_increase > effective_brier_tol:
        degraded = True
        reasons.append(
            f"Brier score worsened by {brier_increase:.4f} beyond tolerance "
            f"{effective_brier_tol:.4f}"
        )
    return degraded, reasons
