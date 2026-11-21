"""Explicit state machines. Risk, approval, sync, remediation and verification states are
independent fields; ``lifecycle_stage`` derives the combined display stage from them."""

from __future__ import annotations

from app.models.enums import ApprovalState, LifecycleStage, PlanStatus, RemediationState, SyncState, VerificationState

PLAN_TRANSITIONS: dict[str, set[str]] = {
    PlanStatus.DRAFT: {PlanStatus.ASSESSMENT_COMPLETE, PlanStatus.PENDING_APPROVAL, PlanStatus.SUPERSEDED},
    PlanStatus.ASSESSMENT_COMPLETE: {PlanStatus.PENDING_APPROVAL, PlanStatus.DRAFT, PlanStatus.SUPERSEDED},
    PlanStatus.PENDING_APPROVAL: {
        PlanStatus.APPROVED,
        PlanStatus.REJECTED,
        PlanStatus.CHANGES_REQUESTED,
        PlanStatus.DRAFT,  # material edit or request cancelled -> approval invalidated
    },
    PlanStatus.CHANGES_REQUESTED: {PlanStatus.DRAFT, PlanStatus.PENDING_APPROVAL, PlanStatus.SUPERSEDED},
    PlanStatus.APPROVED: {PlanStatus.DRAFT},  # only before sync; enforced by the service layer
    PlanStatus.REJECTED: {PlanStatus.SUPERSEDED},
    PlanStatus.SUPERSEDED: set(),
}

APPROVAL_TRANSITIONS: dict[str, set[str]] = {
    ApprovalState.PENDING: {
        ApprovalState.APPROVED,
        ApprovalState.REJECTED,
        ApprovalState.CHANGES_REQUESTED,
        ApprovalState.INVALIDATED,
        ApprovalState.CANCELLED,
    },
    ApprovalState.APPROVED: {ApprovalState.INVALIDATED},
    ApprovalState.REJECTED: set(),
    ApprovalState.CHANGES_REQUESTED: set(),
    ApprovalState.INVALIDATED: set(),
    ApprovalState.CANCELLED: set(),
}

REMEDIATION_TRANSITIONS: dict[str, set[str]] = {
    RemediationState.NOT_STARTED: {
        RemediationState.REMEDIATION_IN_PROGRESS,
        RemediationState.IMPLEMENTED,
        RemediationState.CANCELLED,
    },
    RemediationState.REMEDIATION_IN_PROGRESS: {RemediationState.IMPLEMENTED, RemediationState.CANCELLED},
    RemediationState.IMPLEMENTED: {RemediationState.REMEDIATION_IN_PROGRESS},  # re-opened after failed verification
    RemediationState.CANCELLED: set(),
}


class InvalidTransition(ValueError):
    pass


def check_transition(machine: dict[str, set[str]], current: str, target: str, what: str) -> None:
    if current == target:
        return
    if target not in machine.get(current, set()):
        raise InvalidTransition(f"{what}: transition {current} -> {target} is not allowed")


def lifecycle_stage(
    plan_status: str,
    remediation_state: str,
    sync_state: str | None,
    verification_state: str,
    finding_status: str,
) -> str:
    if verification_state == VerificationState.VERIFIED_REMEDIATED:
        return LifecycleStage.CLOSED if finding_status in ("closed", "remediated") else LifecycleStage.VERIFIED
    if sync_state is not None:
        if sync_state == SyncState.SYNC_FAILED:
            return LifecycleStage.SYNC_FAILED
        if sync_state == SyncState.SYNC_PENDING:
            return LifecycleStage.SYNC_PENDING
        if remediation_state == RemediationState.IMPLEMENTED:
            return LifecycleStage.PENDING_VERIFICATION
        if remediation_state == RemediationState.REMEDIATION_IN_PROGRESS:
            return LifecycleStage.REMEDIATION_IN_PROGRESS
        return LifecycleStage.SYNCED
    stages: dict[str, str] = {
        PlanStatus.DRAFT: LifecycleStage.DRAFT,
        PlanStatus.CHANGES_REQUESTED: LifecycleStage.DRAFT,
        PlanStatus.ASSESSMENT_COMPLETE: LifecycleStage.ASSESSMENT_COMPLETE,
        PlanStatus.PENDING_APPROVAL: LifecycleStage.PENDING_APPROVAL,
        PlanStatus.APPROVED: LifecycleStage.APPROVED,
        PlanStatus.REJECTED: LifecycleStage.REJECTED,
        PlanStatus.SUPERSEDED: LifecycleStage.CLOSED,
    }
    return stages.get(plan_status, LifecycleStage.DRAFT)
