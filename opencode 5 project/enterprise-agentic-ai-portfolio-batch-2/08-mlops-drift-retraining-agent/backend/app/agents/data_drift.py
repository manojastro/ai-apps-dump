"""Feature-level drift detection agent."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.config import settings
from backend.app.ml.drift import evaluate_window_drift
from backend.app.models.entities import DriftResult
from backend.app.repositories.results_repo import ResultsRepository, WindowRepository


class DataDriftAgent:
    """Measures per-feature drift for a monitoring window and persists results."""

    def evaluate(self, session: Session, window_id: int) -> list[DriftResult]:
        window = load_window(session, window_id)
        champion_row, artifact = load_champion(session)
        frame = WindowRepository.load_frame(window)
        reference = artifact["reference_df"]
        stats = artifact["stats"]
        thresholds = champion_row.thresholds or {}

        psi_threshold = float(thresholds.get("psi_meaningful", settings.psi_meaningful))
        tv_threshold = float(thresholds.get("tv_meaningful", settings.tv_meaningful))
        missing_threshold = float(
            thresholds.get("missing_meaningful", settings.missing_meaningful)
        )

        measurements = evaluate_window_drift(frame, reference, stats)
        rows: list[DriftResult] = []
        for m in measurements:
            if m.feature_type == "numeric":
                drifted = (m.psi is not None and m.psi >= psi_threshold) or (
                    m.missing_delta is not None
                    and m.missing_delta >= missing_threshold
                )
            else:
                drifted = (m.tv_delta is not None and m.tv_delta >= tv_threshold) or (
                    m.missing_delta is not None
                    and m.missing_delta >= missing_threshold
                )
            rows.append(
                DriftResult(
                    window_id=window_id,
                    feature=m.feature,
                    feature_type=m.feature_type,
                    psi=m.psi,
                    ks_statistic=m.ks_statistic,
                    p_value=m.p_value,
                    tv_delta=m.tv_delta,
                    missing_delta=m.missing_delta,
                    baseline_missing=m.baseline_missing,
                    current_missing=m.current_missing,
                    drifted=bool(drifted),
                    severity=m.severity,
                    detail=m.detail,
                )
            )
        return ResultsRepository.save_drift_results(session, rows)
