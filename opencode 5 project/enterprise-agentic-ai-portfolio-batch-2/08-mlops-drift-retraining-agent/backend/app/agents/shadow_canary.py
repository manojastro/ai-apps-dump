"""Shadow replay and canary slice evaluation agent."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.agents.common import load_candidate, load_champion
from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    DriftKnobs,
    TARGET,
    generate_customer_data,
)
from backend.app.ml.pipeline import predict_pipeline
from backend.app.models.entities import CanaryResult, ShadowComparison
from backend.app.repositories.results_repo import CandidateRepository, WindowRepository


def _recent_traffic_knobs(session: Session) -> DriftKnobs:
    """Replay uses the most recent window's population when available."""
    latest = WindowRepository.latest(session, evaluated_only=False)
    if latest is not None and latest.knobs:
        return DriftKnobs.from_dict(latest.knobs)
    return DriftKnobs()


class ShadowCanaryAgent:
    """Replays identical requests through champion and challenger."""

    def shadow_compare(
        self, session: Session, version: str, n_requests: int = 3000, seed: int = 555
    ) -> dict:
        candidate = load_candidate(session, version)
        champion_row, champion_artifact = load_champion(session)
        cand_pipeline = _load_candidate_pipeline(candidate.artifact_path)

        replay = generate_customer_data(
            n_requests, seed=seed, knobs=_recent_traffic_knobs(session)
        )
        features = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c in replay.columns]
        champ_pred, champ_prob = predict_pipeline(champion_artifact["pipeline"], replay[features])
        cand_pred, cand_prob = predict_pipeline(cand_pipeline, replay[features])

        disagreement = float((champ_pred != cand_pred).mean())
        mean_abs_diff = float(abs(champ_prob - cand_prob).mean())

        per_segment: dict[str, float] = {}
        frame = replay.copy()
        frame["disagree"] = (champ_pred != cand_pred).astype(int)
        for segment, group in frame.groupby("customer_segment"):
            per_segment[str(segment)] = round(float(group["disagree"].mean()), 6)

        row = ShadowComparison(
            version=version,
            window_id=None,
            n_requests=int(n_requests),
            disagreement_rate=round(disagreement, 6),
            mean_abs_prob_diff=round(mean_abs_diff, 6),
            per_segment=per_segment,
        )
        CandidateRepository.save_shadow(session, row)
        return {
            "version": version,
            "n_requests": int(n_requests),
            "disagreement_rate": round(disagreement, 6),
            "mean_abs_prob_diff": round(mean_abs_diff, 6),
            "per_segment": per_segment,
        }

    def canary_evaluate(
        self, session: Session, version: str, n_requests: int = 2500, seed: int = 777
    ) -> dict:
        candidate = load_candidate(session, version)
        champion_row, champion_artifact = load_champion(session)
        cand_pipeline = _load_candidate_pipeline(candidate.artifact_path)

        canary = generate_customer_data(
            n_requests, seed=seed, knobs=_recent_traffic_knobs(session)
        )
        features = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c in canary.columns]

        slices: dict[str, dict] = {}
        passed = True
        from sklearn.metrics import f1_score

        champ_pred, _ = predict_pipeline(champion_artifact["pipeline"], canary[features])
        cand_pred, _ = predict_pipeline(cand_pipeline, canary[features])
        work = canary.assign(champ=champ_pred, cand=cand_pred)
        for segment, group in work.groupby("customer_segment"):
            y = group[TARGET]
            champ_f1 = float(f1_score(y, group["champ"], zero_division=0))
            cand_f1 = float(f1_score(y, group["cand"], zero_division=0))
            ok = bool(len(group) >= 50 and cand_f1 >= champ_f1 - 0.02)
            passed = passed and ok
            slices[str(segment)] = {
                "n": int(len(group)),
                "champion_f1": round(champ_f1, 6),
                "candidate_f1": round(cand_f1, 6),
                "passed": ok,
            }

        row = CanaryResult(
            version=version,
            slices=slices,
            passed=bool(passed),
            details={"seed": seed, "n_requests": int(n_requests)},
        )
        CandidateRepository.save_canary(session, row)
        return {
            "version": version,
            "passed": bool(passed),
            "slices": slices,
            "details": {"seed": seed, "n_requests": int(n_requests)},
        }


def _load_candidate_pipeline(path: str):
    from backend.app.ml.pipeline import load_artifact

    payload = load_artifact(path)
    if isinstance(payload, dict) and "pipeline" in payload:
        return payload["pipeline"]
    raise ValueError("candidate artifact missing pipeline")
