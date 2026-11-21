"""Bias and fairness agent measuring segment selection parity."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.config import settings
from backend.app.ml.fairness import evaluate_fairness
from backend.app.ml.pipeline import predict_pipeline
from backend.app.models.entities import FairnessResult
from backend.app.repositories.results_repo import ResultsRepository, WindowRepository


class BiasFairnessAgent:
    """Measures churn-selection parity across customer segments."""

    def run(self, session: Session, window_id: int) -> FairnessResult:
        window = load_window(session, window_id)
        _row, artifact = load_champion(session)
        frame = WindowRepository.load_frame(window)
        thresholds = (_row.thresholds or {})
        threshold = float(thresholds.get("fairness_min_ratio", settings.fairness_min_ratio))

        if "customer_segment" not in frame.columns:
            return ResultsRepository.save_fairness(
                session,
                FairnessResult(
                    window_id=window_id,
                    segment_column="customer_segment",
                    selection_rates={},
                    disparity_ratio=1.0,
                    threshold=threshold,
                    passed=False,
                ),
            )

        pred, _ = predict_pipeline(artifact["pipeline"], frame)
        payload = evaluate_fairness(pred, frame["customer_segment"], threshold)
        row = FairnessResult(
            window_id=window_id,
            segment_column=payload["segment_column"],
            selection_rates=payload["selection_rates"],
            disparity_ratio=payload["disparity_ratio"],
            threshold=payload["threshold"],
            passed=payload["passed"],
        )
        return ResultsRepository.save_fairness(session, row)
