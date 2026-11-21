"""Promotion approval state machine with illegal-transition protection."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session

from backend.app.api.errors import DomainError
from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    DriftKnobs,
    generate_customer_data,
)
from backend.app.ml.pipeline import load_artifact, predict_pipeline
from backend.app.models.entities import ApprovalRecord, Promotion
from backend.app.repositories.decision_repo import PromotionRepository, RollbackRepository
from backend.app.repositories.registry_repo import RegistryRepository


class PromotionState:
    PROPOSED = "PROPOSED"
    VALIDATING = "VALIDATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    PromotionState.PROPOSED: {PromotionState.VALIDATING},
    PromotionState.VALIDATING: {PromotionState.AWAITING_APPROVAL, PromotionState.FAILED},
    PromotionState.AWAITING_APPROVAL: {PromotionState.APPROVED, PromotionState.FAILED},
    PromotionState.APPROVED: {PromotionState.EXECUTING, PromotionState.FAILED},
    PromotionState.EXECUTING: {PromotionState.VERIFYING, PromotionState.FAILED},
    PromotionState.VERIFYING: {
        PromotionState.COMPLETED,
        PromotionState.ROLLED_BACK,
        PromotionState.FAILED,
    },
    PromotionState.COMPLETED: set(),
    PromotionState.FAILED: set(),
    PromotionState.ROLLED_BACK: set(),
}


def transition(session: Session, promotion_id: int, new_state: str) -> Promotion:
    """Apply a state transition or raise 409 on an illegal move."""
    promotion = PromotionRepository.get(session, promotion_id)
    if promotion is None:
        raise DomainError(404, f"promotion {promotion_id} not found")
    allowed = ALLOWED_TRANSITIONS.get(promotion.state, set())
    if new_state not in allowed:
        raise DomainError(
            409,
            f"illegal transition {promotion.state} -> {new_state} for promotion {promotion_id}",
        )
    promotion.state = new_state
    if new_state in (PromotionState.COMPLETED, PromotionState.FAILED, PromotionState.ROLLED_BACK):
        promotion.completed_at = datetime.now(timezone.utc)
    return PromotionRepository.update(session, promotion)


class PromotionService:
    """Creates and executes approval-gated promotions with verification."""

    def create(self, session: Session, candidate_version: str) -> Promotion:
        candidate = RegistryRepository.get(session, candidate_version)
        if candidate is None:
            raise DomainError(404, f"candidate version {candidate_version} not found")
        if candidate.kind != "candidate":
            raise DomainError(409, "only candidate models can be promoted")
        champion = RegistryRepository.current_champion(session)
        promotion = PromotionRepository.create(
            session,
            Promotion(
                candidate_version=candidate_version,
                previous_champion=champion.version if champion else None,
                state=PromotionState.PROPOSED,
            ),
        )
        transition(session, promotion.id, PromotionState.VALIDATING)
        artifact_path = Path(candidate.artifact_path)
        if not artifact_path.exists():
            transition(session, promotion.id, PromotionState.FAILED)
            raise DomainError(409, f"candidate artifact missing for {candidate_version}")
        transition(session, promotion.id, PromotionState.AWAITING_APPROVAL)
        return PromotionRepository.get(session, promotion.id)  # type: ignore[return-value]

    def approve(
        self, session: Session, promotion_id: int, approver: str, comment: str
    ) -> Promotion:
        promotion = PromotionRepository.get(session, promotion_id)
        if promotion is None:
            raise DomainError(404, f"promotion {promotion_id} not found")
        if promotion.state != PromotionState.AWAITING_APPROVAL:
            raise DomainError(
                409,
                f"promotion {promotion_id} is {promotion.state}, approvals require AWAITING_APPROVAL",
            )
        transition(session, promotion_id, PromotionState.APPROVED)

        try:
            transition(session, promotion_id, PromotionState.EXECUTING)
            self._swap_champion(session, promotion.candidate_version)
            transition(session, promotion_id, PromotionState.VERIFYING)
            verification = self._verify(session, promotion)
            promotion.verification = verification
            PromotionRepository.update(session, promotion)
            if verification.get("smoke_ok") and verification.get("champion_matches"):
                transition(session, promotion_id, PromotionState.COMPLETED)
            else:
                self._abort_and_restore(session, promotion)
                transition(session, promotion_id, PromotionState.ROLLED_BACK)
        except DomainError:
            transition(session, promotion_id, PromotionState.FAILED)
            raise

        PromotionRepository.add_approval(
            session,
            ApprovalRecord(
                promotion_id=promotion_id,
                decision="approved",
                approver=approver,
                comment=comment,
            ),
        )
        return PromotionRepository.get(session, promotion_id)  # type: ignore[return-value]

    def reject(
        self, session: Session, promotion_id: int, approver: str, comment: str
    ) -> Promotion:
        promotion = PromotionRepository.get(session, promotion_id)
        if promotion is None:
            raise DomainError(404, f"promotion {promotion_id} not found")
        if promotion.state != PromotionState.AWAITING_APPROVAL:
            raise DomainError(
                409,
                f"promotion {promotion_id} is {promotion.state}; rejection requires AWAITING_APPROVAL",
            )
        transition(session, promotion_id, PromotionState.FAILED)
        PromotionRepository.add_approval(
            session,
            ApprovalRecord(
                promotion_id=promotion_id,
                decision="rejected",
                approver=approver,
                comment=comment,
            ),
        )
        return PromotionRepository.get(session, promotion_id)  # type: ignore[return-value]

    def rollback(self, session: Session, target_version: str, reason: str) -> dict:
        champion = RegistryRepository.current_champion(session)
        target = RegistryRepository.get(session, target_version)
        if target is None:
            raise DomainError(404, f"version {target_version} not found in registry")
        if champion is None:
            raise DomainError(409, "no current champion to roll back from")
        if champion.version == target_version:
            raise DomainError(409, "target version is already the current champion")
        if not Path(target.artifact_path).exists():
            raise DomainError(409, f"artifact for {target_version} is missing")
        RegistryRepository.set_status(session, champion.version, "retired")
        RegistryRepository.set_status(session, target_version, "champion")
        RollbackRepository.save(
            session,
            RollbackRecord(
                from_version=champion.version, to_version=target_version, reason=reason
            ),
        )
        return {
            "from_version": champion.version,
            "to_version": target_version,
            "champion_version": target_version,
        }

    def _swap_champion(self, session: Session, candidate_version: str) -> None:
        RegistryRepository.retire_all_of_status(session, "champion")
        RegistryRepository.set_status(session, candidate_version, "champion")

    def _verify(self, session: Session, promotion: Promotion) -> dict:
        row = RegistryRepository.get(session, promotion.candidate_version)
        smoke_ok = False
        try:
            payload = load_artifact(Path(row.artifact_path))  # type: ignore[union-attr]
            frame = generate_customer_data(32, seed=31337)
            pred, _ = predict_pipeline(payload["pipeline"], frame)
            smoke_ok = bool(len(pred) == 32 and np.isfinite(pred).all())
        except Exception as exc:
            return {"smoke_ok": False, "error": str(exc), "champion_matches": False}
        champion = RegistryRepository.current_champion(session)
        return {
            "smoke_ok": smoke_ok,
            "champion_matches": bool(
                champion is not None and champion.version == promotion.candidate_version
            ),
            "champion_version": champion.version if champion else None,
        }

    def _abort_and_restore(self, session: Session, promotion: Promotion) -> None:
        RegistryRepository.retire_all_of_status(session, "champion")
        if promotion.previous_champion:
            RegistryRepository.set_status(
                session, promotion.previous_champion, "champion"
            )


promotion_service = PromotionService()
