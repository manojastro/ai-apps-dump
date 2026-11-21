"""Candidate training, evaluation and risk endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.agents.candidate_evaluation import CandidateEvaluationAgent
from backend.app.agents.candidate_training import CandidateTrainingAgent
from backend.app.agents.deployment_risk import DeploymentRiskAgent
from backend.app.db import get_session
from backend.app.repositories.results_repo import CandidateRepository
from backend.app.schemas.dto import (
    CandidateEvaluateRequest,
    CandidateTrainRequest,
    EvaluateCandidateOutput,
)

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.post("/train")
def post_train(
    request: CandidateTrainRequest, session: Session = Depends(get_session)
) -> dict:
    output = CandidateTrainingAgent().train(
        session,
        source_window_id=request.source_window_id,
        seed=request.seed,
        n_samples=request.n_samples,
        inject_bad=request.inject_bad,
        bad_n_samples=request.bad_n_samples,
        bad_label_noise=request.bad_label_noise,
    )
    return output.model_dump()


@router.post("/evaluate", response_model=EvaluateCandidateOutput)
def post_evaluate(
    request: CandidateEvaluateRequest, session: Session = Depends(get_session)
) -> EvaluateCandidateOutput:
    return CandidateEvaluationAgent().evaluate(session, request.version)


@router.get("")
def list_candidates(session: Session = Depends(get_session)) -> dict:
    rows = CandidateRepository.list_evaluations(session)
    return {
        "evaluations": [
            {
                "id": r.id,
                "version": r.version,
                "verdict": r.verdict,
                "offline_metrics": r.offline_metrics,
                "vs_thresholds": r.vs_thresholds,
                "vs_champion": r.vs_champion,
                "fairness_ratio": r.fairness_ratio,
                "robustness_drop": r.robustness_drop,
                "reasons": r.reasons,
            }
            for r in rows
        ]
    }


@router.get("/{version}/risk")
def get_risk(version: str, session: Session = Depends(get_session)) -> dict:
    return DeploymentRiskAgent().assess(session, version)
