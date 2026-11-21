"""Retraining gate decision endpoints and investigation access."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.agents.retraining_decision import RetrainingDecisionAgent
from backend.app.agents.root_cause import RootCauseAgent
from backend.app.db import get_session
from backend.app.repositories.decision_repo import DecisionRepository, InvestigationRepository
from backend.app.schemas.dto import DecideRequest, DecisionOutput

router = APIRouter(prefix="/api/v1/retraining", tags=["retraining"])


@router.post("/decide", response_model=DecisionOutput)
def post_decide(
    request: DecideRequest, session: Session = Depends(get_session)
) -> DecisionOutput:
    return RetrainingDecisionAgent().decide(session, request.window_id)


@router.get("/decisions")
def get_decisions(session: Session = Depends(get_session)) -> dict:
    rows = DecisionRepository.latest(session)
    return {
        "decisions": [
            {
                "id": r.id,
                "window_id": r.window_id,
                "decision": r.decision,
                "reasons": r.reasons,
                "gate_inputs": r.gate_inputs,
                "projected_benefit": r.projected_benefit,
                "created_at": str(r.created_at),
            }
            for r in rows
        ]
    }


@router.get("/investigations/latest")
def get_latest_investigation(session: Session = Depends(get_session)) -> dict:
    row = InvestigationRepository.latest(session)
    if row is None:
        return {"investigation": None}
    return {
        "investigation": {
            "id": row.id,
            "window_id": row.window_id,
            "incident_id": row.incident_id,
            "root_cause": row.root_cause,
            "confidence": row.confidence,
            "observations": row.observations,
            "recommended_actions": row.recommended_actions,
        }
    }


@router.post("/investigations/{window_id}")
def post_investigate(window_id: int, session: Session = Depends(get_session)) -> dict:
    analysis = RootCauseAgent().investigate(session, window_id)
    return analysis.model_dump()
