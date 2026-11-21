"""Data quality agent running schema, range, null and latency rules."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.ml.drift import evaluate_window_drift, summarise_drift
from backend.app.ml.quality import run_quality_checks
from backend.app.models.entities import DataQualityCheck
from backend.app.repositories.results_repo import ResultsRepository, WindowRepository


class DataQualityAgent:
    """Executes data quality checks for a monitoring window."""

    def run(
        self, session: Session, window_id: int, max_severity_score: float | None = None
    ) -> list[DataQualityCheck]:
        window = load_window(session, window_id)
        _row, artifact = load_champion(session)
        frame = WindowRepository.load_frame(window)

        if max_severity_score is None:
            summary = summarise_drift(
                evaluate_window_drift(frame, artifact["reference_df"], artifact["stats"])
            )
            max_severity_score = min(1.0, summary["max_psi"])

        baseline_latency = float(artifact["stats"].get("baseline_latency_ms", 12.0))
        checks = run_quality_checks(frame, float(max_severity_score), baseline_latency)
        rows = [
            DataQualityCheck(
                window_id=window_id,
                check_name=c.check_name,
                passed=c.passed,
                value=c.value,
                details=c.details,
            )
            for c in checks
        ]
        return ResultsRepository.save_quality_checks(session, rows)
