"""Shadow replay and canary endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.agents.shadow_canary import ShadowCanaryAgent
from backend.app.db import get_session
from backend.app.repositories.results_repo import CandidateRepository

router = APIRouter(prefix="/api/v1/shadow", tags=["shadow"])


@router.post("/run")
def post_shadow_run(request: dict, session: Session = Depends(get_session)) -> dict:
    return ShadowCanaryAgent().shadow_compare(
        session,
        version=request["version"],
        n_requests=int(request.get("n_requests", 3000)),
        seed=int(request.get("seed", 555)),
    )


@router.post("/canary")
def post_canary(request: dict, session: Session = Depends(get_session)) -> dict:
    return ShadowCanaryAgent().canary_evaluate(
        session,
        version=request["version"],
        n_requests=int(request.get("n_requests", 2500)),
        seed=int(request.get("seed", 777)),
    )


@router.get("/results")
def list_results(session: Session = Depends(get_session)) -> dict:
    shadows = CandidateRepository.list_shadow(session)
    return {
        "shadow_comparisons": [
            {
                "id": r.id,
                "version": r.version,
                "n_requests": r.n_requests,
                "disagreement_rate": r.disagreement_rate,
                "mean_abs_prob_diff": r.mean_abs_prob_diff,
                "per_segment": r.per_segment,
            }
            for r in shadows
        ]
    }
