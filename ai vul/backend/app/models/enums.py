"""Domain enumerations. Stored as plain strings for portability and readable SQL."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    APPROVER = "approver"
    VIEWER = "viewer"


class Environment(StrEnum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class Criticality(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
    UNKNOWN = "unknown"


class FindingStatus(StrEnum):
    OPEN = "open"
    IN_REMEDIATION = "in_remediation"
    REMEDIATED = "remediated"  # verified remediated by fresh scan evidence
    CLOSED = "closed"
    RISK_ACCEPTED = "risk_accepted"


class CorrelationStatus(StrEnum):
    PENDING = "pending"
    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    UNMATCHED = "unmatched"


class VerificationState(StrEnum):
    NOT_STARTED = "not_started"
    PENDING_RESCAN = "pending_rescan"
    IN_PROGRESS = "verification_in_progress"
    VERIFIED_REMEDIATED = "verified_remediated"
    FAILED = "verification_failed"
    INCONCLUSIVE = "inconclusive"


class PlanStatus(StrEnum):
    DRAFT = "DRAFT"
    ASSESSMENT_COMPLETE = "ASSESSMENT_COMPLETE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    SUPERSEDED = "SUPERSEDED"


class ApprovalState(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    INVALIDATED = "INVALIDATED"
    CANCELLED = "CANCELLED"


class SyncState(StrEnum):
    SYNC_PENDING = "SYNC_PENDING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"


class RemediationState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    REMEDIATION_IN_PROGRESS = "REMEDIATION_IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    CANCELLED = "CANCELLED"


class LifecycleStage(StrEnum):
    """Combined, display-only lifecycle (derived from the independent state fields)."""

    DRAFT = "DRAFT"
    ASSESSMENT_COMPLETE = "ASSESSMENT_COMPLETE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SYNC_PENDING = "SYNC_PENDING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"
    REMEDIATION_IN_PROGRESS = "REMEDIATION_IN_PROGRESS"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


class WorkflowStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_MANUAL_REVIEW = "waiting_manual_review"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_SYNC_RETRY = "waiting_sync_retry"
    WAITING_EVIDENCE = "waiting_evidence"
    COMPLETED = "completed"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def active(cls) -> set[str]:
        return {
            cls.QUEUED,
            cls.RUNNING,
            cls.WAITING_MANUAL_REVIEW,
            cls.WAITING_APPROVAL,
            cls.WAITING_SYNC_RETRY,
            cls.WAITING_EVIDENCE,
        }

    @classmethod
    def terminal(cls) -> set[str]:
        return {cls.COMPLETED, cls.REJECTED, cls.BLOCKED, cls.FAILED, cls.CANCELLED}


class AgentStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    WAITING = "waiting"
