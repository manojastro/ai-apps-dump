"""Candidate evaluation agent: offline, fairness and robustness deployment gates."""
from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session

from backend.app.agents.common import load_candidate, load_champion
from backend.app.config import settings
from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    DriftKnobs,
    TARGET,
    generate_customer_data,
)
from backend.app.ml.fairness import evaluate_fairness
from backend.app.ml.pipeline import (
    compute_classification_metrics,
    load_artifact,
    predict_pipeline,
)
from backend.app.models.entities import CandidateEvaluation
from backend.app.repositories.decision_repo import TrainingRunRepository
from backend.app.repositories.registry_repo import RegistryRepository
from backend.app.repositories.results_repo import CandidateRepository
from backend.app.schemas.dto import EvaluateCandidateOutput


class CandidateEvaluationAgent:
    """Scores a candidate against thresholds and the champion on matched data."""

    def evaluate(self, session: Session, version: str) -> EvaluateCandidateOutput:
        candidate = load_candidate(session, version)
        champion_row, champion_artifact = load_champion(session)
        run = TrainingRunRepository.latest_for_version(session, version)
        if run is None:
            raise ValueError(f"no training run found for {version}")
        hyperparams = run.hyperparams or {}
        knobs = DriftKnobs.from_dict(hyperparams.get("knobs", {}))
        val_seed = int(hyperparams.get("val_seed", 108))
        val_n = int(hyperparams.get("val_n", 2500))

        validation = generate_customer_data(val_n, seed=val_seed, knobs=knobs)
        features = [
            c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c in validation.columns
        ]
        y_true = validation[TARGET]

        cand_pipeline = load_artifact(candidate.artifact_path)["pipeline"]
        champ_pred, champ_prob = predict_pipeline(champion_artifact["pipeline"], validation[features])
        cand_pred, cand_prob = predict_pipeline(cand_pipeline, validation[features])

        champ_metrics = compute_classification_metrics(y_true, champ_pred, champ_prob)
        cand_metrics = compute_classification_metrics(y_true, cand_pred, cand_prob)

        thresholds = dict(champion_row.thresholds or {})
        f1_tol = float(thresholds.get("cand_f1_tolerance", settings.cand_f1_tolerance))
        auc_tol = float(thresholds.get("cand_auc_tolerance", settings.cand_auc_tolerance))
        brier_eps = float(thresholds.get("cand_brier_eps", settings.cand_brier_eps))
        fair_min = float(thresholds.get("fairness_min_ratio", settings.fairness_min_ratio))
        robust_max = float(thresholds.get("robustness_max_drop", settings.robustness_max_drop))

        fairness_payload = evaluate_fairness(cand_pred, validation["customer_segment"], fair_min)
        robustness_drop = self._robustness_drop(
            cand_pipeline, validation, features, y_true, cand_metrics["f1"]
        )

        vs_thresholds = {
            "f1_ok": bool(cand_metrics["f1"] >= champ_metrics["f1"] - f1_tol),
            "auc_ok": bool(cand_metrics["roc_auc"] >= champ_metrics["roc_auc"] - auc_tol),
            "brier_ok": bool(cand_metrics["brier"] <= champ_metrics["brier"] + brier_eps),
            "fairness_ok": bool(fairness_payload["passed"]),
            "robustness_ok": bool(robustness_drop <= robust_max),
        }
        reasons: list[str] = []
        if not vs_thresholds["f1_ok"]:
            reasons.append(
                f"F1 {cand_metrics['f1']:.4f} below champion {champ_metrics['f1']:.4f} "
                f"minus tolerance {f1_tol}"
            )
        if not vs_thresholds["auc_ok"]:
            reasons.append(
                f"AUC {cand_metrics['roc_auc']:.4f} below champion "
                f"{champ_metrics['roc_auc']:.4f} minus tolerance {auc_tol}"
            )
        if not vs_thresholds["brier_ok"]:
            reasons.append(
                f"Brier {cand_metrics['brier']:.4f} above champion "
                f"{champ_metrics['brier']:.4f} plus epsilon {brier_eps}"
            )
        if not vs_thresholds["fairness_ok"]:
            reasons.append(
                f"fairness ratio {fairness_payload['disparity_ratio']:.3f} below {fair_min}"
            )
        if not vs_thresholds["robustness_ok"]:
            reasons.append(
                f"robustness drop {robustness_drop:.3f} exceeds maximum {robust_max}"
            )
        verdict = "pass" if all(vs_thresholds.values()) else "reject"
        if verdict == "reject":
            from backend.app.services.llm import get_llm

            get_llm().narrate("rejection", {"version": version, "reasons": "; ".join(reasons)})

        vs_champion = {
            "f1_delta": round(cand_metrics["f1"] - champ_metrics["f1"], 6),
            "roc_auc_delta": round(cand_metrics["roc_auc"] - champ_metrics["roc_auc"], 6),
            "brier_delta": round(cand_metrics["brier"] - champ_metrics["brier"], 6),
            "accuracy_delta": round(cand_metrics["accuracy"] - champ_metrics["accuracy"], 6),
        }

        CandidateRepository.save_evaluation(
            session,
            CandidateEvaluation(
                version=version,
                verdict=verdict,
                offline_metrics={k: round(v, 6) for k, v in cand_metrics.items()},
                vs_thresholds=vs_thresholds,
                vs_champion=vs_champion,
                fairness_ratio=fairness_payload["disparity_ratio"],
                robustness_drop=round(robustness_drop, 6),
                reasons=reasons,
            ),
        )
        candidate.metrics = {k: round(float(v), 6) for k, v in cand_metrics.items()}
        candidate.notes = f"evaluation verdict={verdict}; reasons={reasons if reasons else 'all gates passed'}"
        session.commit()

        return EvaluateCandidateOutput(
            version=version,
            verdict=verdict,
            offline_metrics=candidate.metrics,
            vs_thresholds=vs_thresholds,
            vs_champion=vs_champion,
            fairness_ratio=fairness_payload["disparity_ratio"],
            robustness_drop=round(robustness_drop, 6),
            reasons=reasons,
        )

    @staticmethod
    def _robustness_drop(
        pipeline: object,
        validation,
        features: list[str],
        y_true,
        clean_f1: float,
        noise_scale: float = 0.10,
    ) -> float:
        """Relative F1 drop under Gaussian noise on numeric inputs."""
        perturbed = validation.copy()
        rng = np.random.default_rng(20240815)
        for col in NUMERIC_FEATURES:
            if col not in perturbed.columns:
                continue
            sigma = float(perturbed[col].std()) or 1.0
            perturbed[col] = perturbed[col] + rng.normal(0.0, noise_scale * sigma, len(perturbed))
        pred, prob = predict_pipeline(pipeline, perturbed[features])  # type: ignore[arg-type]
        noisy_f1 = compute_classification_metrics(y_true, pred, prob)["f1"]
        denominator = max(clean_f1, 1e-4)
        return max(0.0, (clean_f1 - noisy_f1) / denominator)
