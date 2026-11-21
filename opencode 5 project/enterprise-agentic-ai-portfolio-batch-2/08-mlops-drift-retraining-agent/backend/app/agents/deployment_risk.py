"""Deployment risk agent with deterministic LOW/MEDIUM/HIGH scoring."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.repositories.results_repo import CandidateRepository


class DeploymentRiskAgent:
    """Scores candidate deployment risk from evaluation and shadow evidence."""

    def assess(self, session: Session, version: str) -> dict:
        evaluation = CandidateRepository.latest_evaluation(session, version)
        shadow = CandidateRepository.latest_shadow(session, version)
        canary = CandidateRepository.latest_canary(session, version)

        factors: dict[str, bool | float] = {}
        score = 0.0
        if evaluation is None:
            factors["no_evaluation"] = True
            score += 3.0
        else:
            f1_delta = float(evaluation.vs_champion.get("f1_delta", 0.0))
            factors["thin_f1_margin"] = f1_delta < 0.005
            score += 2.0 if f1_delta < 0.005 else 0.0
            factors["robustness_concern"] = evaluation.robustness_drop > 0.06
            score += 1.0 if evaluation.robustness_drop > 0.06 else 0.0
            factors["fairness_margin_thin"] = evaluation.fairness_ratio < 0.90
            score += 1.0 if evaluation.fairness_ratio < 0.90 else 0.0

        if shadow is None:
            factors["no_shadow_run"] = True
            score += 1.0
        else:
            disagreement = float(shadow.disagreement_rate)
            factors["high_disagreement"] = disagreement > 0.15
            score += 2.0 if disagreement > 0.15 else 0.0

        if canary is None:
            factors["no_canary_run"] = True
            score += 1.0
        elif not canary.passed:
            factors["canary_failed"] = True
            score += 3.0

        if score <= 1.5:
            level = "LOW"
        elif score <= 3.5:
            level = "MEDIUM"
        else:
            level = "HIGH"

        CandidateRepository.save_risk(
            session, _risk_row(version, level, score, factors)
        )
        return {"version": version, "risk_level": level, "score": score, "factors": factors}


def _risk_row(version: str, level: str, score: float, factors: dict):
    from backend.app.models.entities import DeploymentRisk

    return DeploymentRisk(
        version=version,
        risk_level=level,
        score=float(score),
        factors={k: (v if isinstance(v, (bool, float)) else str(v)) for k, v in factors.items()},
    )
