"""Model monitoring agent: orchestrates a full window evaluation."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.agents.data_drift import DataDriftAgent
from backend.app.agents.data_quality import DataQualityAgent
from backend.app.agents.fairness import BiasFairnessAgent
from backend.app.agents.performance import PerformanceAgent, performance_degradation
from backend.app.config import settings
from backend.app.api.errors import DomainError
from backend.app.ml.data_generator import TARGET
from backend.app.ml.drift import prediction_rate_drift, summarise_drift
from backend.app.ml.pipeline import predict_pipeline
from backend.app.repositories.results_repo import ResultsRepository, WindowRepository
from backend.app.schemas.dto import EvaluateWindowOutput


class ModelMonitoringAgent:
    """Runs drift, quality, performance and fairness agents for one window."""

    def __init__(self) -> None:
        self.drift_agent = DataDriftAgent()
        self.quality_agent = DataQualityAgent()
        self.performance_agent = PerformanceAgent()
        self.fairness_agent = BiasFairnessAgent()

    def evaluate_window(self, session: Session, window_id: int) -> EvaluateWindowOutput:
        window = load_window(session, window_id)
        if window.evaluated:
            raise DomainError(409, f"window {window_id} has already been evaluated")
        champion_row, artifact = load_champion(session)
        frame = WindowRepository.load_frame(window)
        thresholds = dict(champion_row.thresholds or {})

        drift_rows = self.drift_agent.evaluate(session, window_id)
        summary = summarise_drift(
            [
                type("M", (), {
                    "feature": r.feature,
                    "feature_type": r.feature_type,
                    "psi": r.psi,
                    "tv_delta": r.tv_delta,
                    "missing_delta": r.missing_delta,
                    "severity": r.severity,
                })()
                for r in drift_rows
            ]
        )

        self.quality_agent.run(
            session, window_id, max_severity_score=min(1.0, float(summary["max_psi"]))
        )
        perf = self.performance_agent.evaluate(session, window_id)
        fairness_row = self.fairness_agent.run(session, window_id)

        pred, _ = predict_pipeline(artifact["pipeline"], frame)
        baseline_rate = float(artifact["stats"].get("positive_rate", 0.0))
        pred_threshold = float(
            thresholds.get("pred_rate_meaningful", settings.pred_rate_meaningful)
        )
        rate_payload = prediction_rate_drift(baseline_rate, float(pred.mean()), pred_threshold)
        ResultsRepository.save_prediction_stat(
            session, _prediction_stat_row(window_id, len(frame), rate_payload)
        )

        degraded, _reasons = performance_degradation(
            dict(artifact["metrics"]),
            {"f1": perf.f1, "roc_auc": perf.roc_auc, "brier": perf.brier},
            float(thresholds.get("perf_f1_tol", settings.perf_f1_tol)),
        )
        quality_rows = ResultsRepository.quality_for_window(session, window_id)
        quality_passed = all(c.passed for c in quality_rows)

        meaningful_feature_drift = any(r.drifted for r in drift_rows)
        alert = bool(
            meaningful_feature_drift
            or rate_payload["drifted"]
            or degraded
            or not fairness_row.passed
            or not quality_passed
        )

        WindowRepository.mark_evaluated(session, window, alert)

        from backend.app.services.llm import get_llm

        get_llm().narrate(
            "window_summary",
            {
                "window_id": window_id,
                "name": window.name or f"window-{window_id}",
                "alert": alert,
                "drift_count": summary["drift_count"],
                "max_psi": float(summary["max_psi"]),
                "f1": perf.f1,
            },
        )

        return EvaluateWindowOutput(
            window_id=window_id,
            alert=alert,
            drift_count=int(summary["drift_count"]),
            max_psi=float(summary["max_psi"]),
            max_tv_delta=float(summary["max_tv_delta"]),
            quality_passed=bool(quality_passed),
            fairness_ratio=float(fairness_row.disparity_ratio),
            f1=float(perf.f1),
            positive_rate_delta=float(rate_payload["absolute_delta"]),
        )


def _prediction_stat_row(window_id: int, n_predictions: int, payload: dict):
    from backend.app.models.entities import PredictionStat

    return PredictionStat(
        window_id=window_id,
        n_predictions=n_predictions,
        positive_rate=payload["positive_rate"],
        baseline_positive_rate=payload["baseline_positive_rate"],
        absolute_delta=payload["absolute_delta"],
        drifted=payload["drifted"],
    )
