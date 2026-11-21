"""Promotion approval endpoints and rollback."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db import get_session
from backend.app.repositories.decision_repo import (
    PromotionRepository,
    RollbackRepository,
)
from backend.app.schemas.dto import ApprovalRequest, PromotionCreateRequest, RollbackRequest
from backend.app.services.approval import promotion_service

router = APIRouter(tags=["promotions"])


class RiskTriggerResponse(BaseModel):
    ok: bool


@router.post("/api/v1/promotions")
def create_promotion(
    request: PromotionCreateRequest, session: Session = Depends(get_session)
) -> dict:
    from backend.app.agents.deployment_risk import DeploymentRiskAgent

    promotion = promotion_service.create(session, request.candidate_version)
    risk = DeploymentRiskAgent().assess(session, request.candidate_version)
    return {
        "promotion_id": promotion.id,
        "candidate_version": promotion.candidate_version,
        "previous_champion": promotion.previous_champion,
        "state": promotion.state,
        "risk": risk,
    }


@router.get("/api/v1/promotions")
def list_promotions(session: Session = Depends(get_session)) -> dict:
    rows = PromotionRepository.list_all(session)
    return {
        "promotions": [
            {
                "id": r.id,
                "candidate_version": r.candidate_version,
                "previous_champion": r.previous_champion,
                "state": r.state,
                "verification": r.verification,
                "created_at": str(r.created_at),
                "completed_at": str(r.completed_at) if r.completed_at else None,
            }
            for r in rows
        ]
    }


@router.post("/api/v1/promotions/{promotion_id}/approve")
def approve_promotion(
    promotion_id: int, request: ApprovalRequest, session: Session = Depends(get_session)
) -> dict:
    promotion = promotion_service.approve(
        session, promotion_id, request.approver, request.comment
    )
    return {"promotion_id": promotion.id, "state": promotion.state}


@router.post("/api/v1/promotions/{promotion_id}/reject")
def reject_promotion(
    promotion_id: int, request: ApprovalRequest, session: Session = Depends(get_session)
) -> dict:
    promotion = promotion_service.reject(
        session, promotion_id, request.approver, request.comment
    )
    return {"promotion_id": promotion.id, "state": promotion.state}


@router.post("/api/v1/rollback/{target_version}")
def rollback(target_version: str, request: RollbackRequest, session: Session = Depends(get_session)) -> dict:
    result = promotion_service.rollback(session, target_version, request.reason)
    history = RollbackRepository.list_all(session)
    result["rollback_count"] = len(history)
    return result


@router.get("/api/v1/rollbacks")
def rollback_history(session: Session = Depends(get_session)) -> dict:
    rows = RollbackRepository.list_all(session)
    return {
        "rollbacks": [
            {
                "id": r.id,
                "from_version": r.from_version,
                "to_version": r.to_version,
                "reason": r.reason,
                "created_at": str(r.created_at),
            }
            for r in rows
        ]
    }
