"""Retraining decision agent: the safety gate deciding IF retraining is justified."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_champion, load_window
from backend.app.agents.performance import performance_degradation
from backend.app.config import settings
from backend.app.repositories.decision_repo import DecisionRepository
from backend.app.repositories.results_repo import ResultsRepository
from backend.app.schemas.dto import DecisionOutput, GateInputs
from backend.app.services.llm import get_llm


def evaluate_gate(gate: GateInputs) -> tuple[str, list[str]]:
    """Pure gate logic: retrain only when every condition is met."""
    blockers: list[str] = []
    if not gate.meaningful_drift:
        blockers.append("no drift crossed meaningful thresholds")
    if not (gate.perf_degradation or gate.high_risk_drift):
        blockers.append(
            "neither performance degradation nor high-risk drift observed"
        )
    if not gate.sufficient_new_labeled_samples:
        blockers.append(
            f"insufficient labelled samples: {gate.n_labeled_samples} < "
            f"{gate.min_labeled_samples}"
        )
    if gate.projected_benefit < gate.min_projected_benefit:
        blockers.append(
            f"projected benefit {gate.projected_benefit:.3f} below minimum "
            f"{gate.min_projected_benefit}"
        )
    if blockers:
        return "monitor", blockers
    reasons = [
        "meaningful drift detected",
        "performance degraded or high-risk drift present",
        f"sufficient labelled samples ({gate.n_labeled_samples} >= "
        f"{gate.min_labeled_samples})",
        f"projected benefit {gate.projected_benefit:.3f} >= minimum",
    ]
    return "retrain", reasons


class RetrainingDecisionAgent:
    """Applies the retraining gate to an evaluated monitoring window."""

    def decide(self, session: Session, window_id: int) -> DecisionOutput:
        window = load_window(session, window_id)
        if not window.evaluated:
            raise ValueError(f"window {window_id} has not been evaluated yet")
        champion_row, artifact = load_champion(session)
        thresholds = champion_row.thresholds or {}

        drift_rows = ResultsRepository.drift_for_window(session, window_id)
        perf = ResultsRepository.performance_for_window(session, window_id)
        fairness = ResultsRepository.fairness_for_window(session, window_id)
        quality = ResultsRepository.quality_for_window(session, window_id)
        pred_stat = ResultsRepository.prediction_stat_for_window(session, window_id)

        feature_drifted = any(r.drifted for r in drift_rows)
        pred_drifted = bool(pred_stat.drifted) if pred_stat else False
        meaningful_drift = feature_drifted or pred_drifted

        baseline_metrics = dict(artifact["metrics"])
        perf_degraded = False
        perf_reasons: list[str] = []
        if perf is not None:
            perf_degraded, perf_reasons = performance_degradation(
                baseline_metrics,
                {
                    "f1": perf.f1,
                    "roc_auc": perf.roc_auc,
                    "brier": perf.brier,
                },
                float(thresholds.get("perf_f1_tol", settings.perf_f1_tol)),
            )

        max_psi = max((r.psi or 0.0) for r in drift_rows) if drift_rows else 0.0
        max_missing = (
            max((r.missing_delta or 0.0) for r in drift_rows) if drift_rows else 0.0
        )
        high_severity = any(r.severity == "high" for r in drift_rows)
        fairness_failed = bool(fairness and not fairness.passed)
        critical_dq_fail = any(
            (not c.passed) and c.check_name in {"schema_complete", "null_fraction"}
            for c in quality
        )
        high_risk_drift = bool(
            high_severity or fairness_failed or critical_dq_fail or max_missing >= 0.15
        )

        n_labeled = int(window.n_samples)
        min_labeled = int(thresholds.get("min_labeled_samples", settings.min_labeled_samples))

        baseline_f1 = float(baseline_metrics.get("f1", 0.0))
        window_f1 = float(perf.f1) if perf is not None else baseline_f1
        projected_benefit = round(
            0.6 * min(1.0, max_psi / 0.5)
            + 0.4 * min(1.0, max(0.0, baseline_f1 - window_f1) / 0.2),
            4,
        )
        min_benefit = float(
            thresholds.get("min_projected_benefit", settings.min_projected_benefit)
        )

        gate_inputs = GateInputs(
            meaningful_drift=meaningful_drift,
            perf_degradation=bool(perf_degraded),
            high_risk_drift=high_risk_drift,
            sufficient_new_labeled_samples=n_labeled >= min_labeled,
            projected_benefit=projected_benefit,
            min_projected_benefit=min_benefit,
            n_labeled_samples=n_labeled,
            min_labeled_samples=min_labeled,
        )
        decision, reasons = evaluate_gate(gate_inputs)

        context = {
            "window_id": window_id,
            "blockers": "; ".join(reasons),
            "benefit": projected_benefit,
            "f1_drop": round(baseline_f1 - window_f1, 4),
        }
        narration = get_llm().narrate(
            "decision_retrain" if decision == "retrain" else "decision_monitor",
            context,
        )

        persisted_gate = dict(gate_inputs.model_dump())
        persisted_gate["perf_degradation_reasons"] = perf_reasons
        persisted_gate["high_severity_features"] = [
            r.feature for r in drift_rows if r.severity == "high"
        ]
        persisted_gate["fairness_failed"] = fairness_failed
        persisted_gate["critical_dq_fail"] = critical_dq_fail

        DecisionRepository.save(
            session,
            _decision_row(
                window_id,
                decision,
                reasons + (perf_reasons if decision == "monitor" else []),
                persisted_gate,
                projected_benefit,
                narration,
            ),
        )
        return DecisionOutput(
            window_id=window_id,
            decision=decision,
            reasons=reasons + (perf_reasons if decision == "monitor" else []),
            gate_inputs=gate_inputs,
            projected_benefit=projected_benefit,
            narration=narration,
        )


def _decision_row(
    window_id: int,
    decision: str,
    reasons: list[str],
    gate_inputs: dict,
    projected_benefit: float,
    narration: str,
):
    from backend.app.models.entities import RetrainingDecision

    return RetrainingDecision(
        window_id=window_id,
        decision=decision,
        reasons=reasons,
        gate_inputs=gate_inputs,
        projected_benefit=projected_benefit,
        narration=narration,
    )
