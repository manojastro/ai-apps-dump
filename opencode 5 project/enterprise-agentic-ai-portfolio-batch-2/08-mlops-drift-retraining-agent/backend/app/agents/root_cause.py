"""Root cause analysis agent producing evidence-backed RCA records."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.config import settings
from backend.app.models.entities import (
    EvidenceItem,
    Hypothesis,
    Investigation,
    RejectedHypothesis,
)
from backend.app.repositories.decision_repo import InvestigationRepository
from backend.app.repositories.results_repo import ResultsRepository
from backend.app.schemas.dto import RootCauseAnalysis
from backend.app.services.llm import get_llm


class RootCauseAgent:
    """Deterministic investigation of a drifted window with persisted evidence."""

    def investigate(self, session: Session, window_id: int) -> RootCauseAnalysis:
        window = load_window(session, window_id)
        _row, artifact = load_champion(session)
        drift_rows = ResultsRepository.drift_for_window(session, window_id)
        perf = ResultsRepository.performance_for_window(session, window_id)
        fairness = ResultsRepository.fairness_for_window(session, window_id)
        quality = ResultsRepository.quality_for_window(session, window_id)
        pred_stat = ResultsRepository.prediction_stat_for_window(session, window_id)

        ranked = sorted(
            drift_rows,
            key=lambda r: max(
                r.psi or 0.0, r.tv_delta or 0.0, (r.missing_delta or 0.0) * 2.5
            ),
            reverse=True,
        )
        top = [r for r in ranked if r.severity in ("medium", "high")][:3]
        top_names = [r.feature for r in top] or [r.feature for r in ranked[:2]]
        knobs = window.knobs or {}
        baseline_metrics = artifact["metrics"]

        observations: list[str] = []
        if top:
            observations.append(
                "Top drifted features: "
                + ", ".join(
                    f"{r.feature} (psi={r.psi}, tv={r.tv_delta}, "
                    f"missing_delta={r.missing_delta})"
                    for r in top
                )
            )
        if perf is not None:
            observations.append(
                f"Champion F1 fell from {baseline_metrics.get('f1', 0.0):.3f} to "
                f"{perf.f1:.3f} on {perf.n_evaluated} labelled rows"
            )
        if pred_stat is not None:
            observations.append(
                f"Positive prediction rate moved from "
                f"{pred_stat.baseline_positive_rate:.3f} to {pred_stat.positive_rate:.3f}"
            )
        if fairness is not None:
            observations.append(
                f"Segment disparity ratio {fairness.disparity_ratio:.3f} against "
                f"threshold {fairness.threshold} passed={fairness.passed}"
            )
        failed_dq = [c.check_name for c in quality if not c.passed]
        if failed_dq:
            observations.append(f"Failed data quality checks: {', '.join(failed_dq)}")

        hypotheses: list[dict] = []
        rejected: list[dict] = []

        def confirm(statement: str, confidence_value: float, rationale: str) -> None:
            hypotheses.append(
                {
                    "statement": statement,
                    "status": "confirmed",
                    "confidence": round(confidence_value, 3),
                    "rationale": rationale,
                }
            )

        def reject(statement: str, rationale: str) -> None:
            rejected.append({"statement": statement, "rationale": rationale})
            hypotheses.append(
                {
                    "statement": statement,
                    "status": "rejected",
                    "confidence": 0.05,
                    "rationale": rationale,
                }
            )

        max_missing = (
            max((r.missing_delta or 0.0) for r in drift_rows) if drift_rows else 0.0
        )
        schema_failed = any(
            c.check_name == "schema_complete" and not c.passed for c in quality
        )
        if max_missing >= 0.03 or schema_failed:
            confirm(
                "Upstream schema change introduced missing values",
                min(0.9, 0.5 + max_missing),
                f"max missing-rate delta {max_missing:.3f} across features",
            )
        else:
            reject(
                "Upstream schema change introduced missing values",
                f"max missing-rate delta only {max_missing:.3f}",
            )

        max_psi = max((r.psi or 0.0) for r in drift_rows) if drift_rows else 0.0
        if max_psi >= settings.psi_meaningful:
            confirm(
                "Population covariate shift in numeric features",
                min(0.95, 0.5 + max_psi / 2.0),
                f"PSI reached {max_psi:.3f}",
            )
        elif max_psi >= 0.10:
            confirm(
                "Mild population shift below gate threshold",
                0.45,
                f"PSI {max_psi:.3f}",
            )
        else:
            reject(
                "Population covariate shift in numeric features",
                f"PSI stayed at {max_psi:.3f}",
            )

        seasonality = float(knobs.get("seasonality_factor", 1.0) or 1.0)
        if abs(seasonality - 1.0) > 1e-9 and "usage_gb" in top_names:
            confirm(
                "Seasonality driving usage changes",
                0.7,
                f"seasonality_factor={seasonality} with usage_gb among top drifted",
            )
        else:
            reject(
                "Seasonality driving usage changes",
                "no seasonality knob applied or usage_gb not dominant",
            )

        label_noise = float(knobs.get("label_noise", 0.0) or 0.0)
        if label_noise > 0.01:
            confirm(
                "Label corruption in recent ground truth",
                min(0.9, 0.5 + label_noise),
                f"label noise rate {label_noise:.2f} degrades measured performance",
            )
        else:
            reject(
                "Label corruption in recent ground truth",
                "window generated without a label noise knob",
            )

        segment_shift = float(knobs.get("new_segment_share", 0.0) or 0.0)
        seg_row = next((r for r in drift_rows if r.feature == "customer_segment"), None)
        seg_tv = seg_row.tv_delta if seg_row is not None else 0.0
        if segment_shift > 0.02 or (seg_tv or 0.0) >= 0.2:
            confirm(
                "Marketing campaign changed customer segment mix",
                0.65,
                f"new_segment_share={segment_shift}, segment tv_delta={seg_tv}",
            )
        else:
            reject(
                "Marketing campaign changed customer segment mix",
                "segment distribution remained stable",
            )

        confirmed_statements = [
            h["statement"] for h in hypotheses if h["status"] == "confirmed"
        ]
        cause_parts: list[str] = []
        if "Population covariate shift in numeric features" in confirmed_statements:
            cause_parts.append(f"covariate drift concentrated in {', '.join(top_names)}")
        if "Label corruption in recent ground truth" in confirmed_statements:
            cause_parts.append(f"label noise of {label_noise:.0%} inflating error rates")
        if "Upstream schema change introduced missing values" in confirmed_statements:
            cause_parts.append("rising missingness suggesting an upstream pipeline fault")
        if not cause_parts:
            cause_parts.append("minor distribution movement within tolerance")

        root_cause = (
            f"Performance deterioration is explained by {' combined with '.join(cause_parts)}."
        )
        confidence_value = min(
            0.95, 0.50 + 0.09 * len(confirmed_statements) + 0.02 * len(top)
        )

        recommended_actions = ["Keep monitoring the champion on subsequent windows"]
        if max_psi >= settings.psi_meaningful:
            recommended_actions.insert(
                0,
                "Run the retraining gate to decide whether candidate training is justified",
            )
        if "Upstream schema change introduced missing values" in confirmed_statements:
            recommended_actions.append(
                "Open a data engineering ticket for the upstream pipeline"
            )
        if "Label corruption in recent ground truth" in confirmed_statements:
            recommended_actions.append(
                "Audit the labeling process before trusting recent metrics"
            )

        incident_id = f"INC-{window_id:04d}"
        narration = get_llm().narrate(
            "root_cause",
            {
                "incident_id": incident_id,
                "root_cause": root_cause,
                "confidence": confidence_value,
                "top_features": ", ".join(top_names) or "none",
            },
        )

        investigation = InvestigationRepository.save_investigation(
            session,
            Investigation(
                window_id=window_id,
                incident_id=incident_id,
                root_cause=root_cause,
                confidence=round(confidence_value, 4),
                observations=observations,
                recommended_actions=recommended_actions,
                narration=narration,
            ),
        )
        InvestigationRepository.add_evidence(
            session,
            [
                EvidenceItem(
                    investigation_id=investigation.id,
                    kind="drift_table",
                    description="Per-feature drift measurements",
                    payload=_drift_payload(drift_rows),
                ),
                EvidenceItem(
                    investigation_id=investigation.id,
                    kind="performance",
                    description="Champion performance on window ground truth",
                    payload=_model_payload(perf),
                ),
                EvidenceItem(
                    investigation_id=investigation.id,
                    kind="fairness",
                    description="Segment parity measurement",
                    payload=_model_payload(fairness),
                ),
                EvidenceItem(
                    investigation_id=investigation.id,
                    kind="data_quality",
                    description="Data quality check outcomes",
                    payload={"failed": failed_dq, "checks_run": len(quality)},
                ),
                EvidenceItem(
                    investigation_id=investigation.id,
                    kind="knobs",
                    description="Simulator knobs used for this window",
                    payload=dict(knobs),
                ),
            ],
        )
        InvestigationRepository.add_hypotheses(
            session,
            [
                Hypothesis(
                    investigation_id=investigation.id,
                    statement=h["statement"],
                    status=h["status"],
                    confidence=h["confidence"],
                    rationale=h["rationale"],
                )
                for h in hypotheses
            ],
        )
        InvestigationRepository.add_rejected(
            session,
            [
                RejectedHypothesis(
                    investigation_id=investigation.id,
                    statement=r["statement"],
                    rationale=r["rationale"],
                )
                for r in rejected
            ],
        )

        return RootCauseAnalysis(
            incident_id=incident_id,
            observations=observations,
            evidence=[
                {"kind": "drift_table", "features": len(drift_rows)},
                {"kind": "performance", "captured": perf is not None},
                {"kind": "fairness", "captured": fairness is not None},
                {"kind": "data_quality", "failed": failed_dq},
                {"kind": "knobs", "applied": list(knobs.keys())},
            ],
            hypotheses=hypotheses,
            rejected_hypotheses=rejected,
            root_cause=root_cause,
            confidence=round(confidence_value, 4),
            recommended_actions=recommended_actions,
        )


def _drift_payload(rows: list) -> dict:
    return {
        "features": [
            {
                "feature": r.feature,
                "psi": r.psi,
                "tv_delta": r.tv_delta,
                "missing_delta": r.missing_delta,
                "severity": r.severity,
                "drifted": r.drifted,
            }
            for r in rows
        ]
    }


def _model_payload(row: object | None) -> dict:
    if row is None:
        return {}
    payload = {}
    for column in row.__table__.columns:
        if column.name == "id":
            continue
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        payload[column.name] = value
    return payload
