"""Core data models shared across adapters, matcher, detector, proposer and API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class System(StrEnum):
    CRM = "crm"
    BILLING = "billing"
    MARKETING = "marketing"


class CustomerRecord(BaseModel):
    """One record from one system, already normalised by its adapter."""

    system: System
    record_id: str
    crm_account_id: str | None = None  # external reference to the CRM account, if the system stores one
    name: str | None = None  # normalised name
    raw_name: str | None = None
    email: str | None = None  # normalised email
    raw_email: str | None = None
    status: str | None = None
    plan: str | None = None
    attrs: dict[str, Any] = Field(default_factory=dict)


MatchMethod = Literal["id", "email", "fuzzy_name_domain", "name_only"]


class MatchLink(BaseModel):
    record: CustomerRecord
    method: MatchMethod
    confidence: float


class UnifiedCustomer(BaseModel):
    """A CRM account plus every billing / marketing record linked to it."""

    customer_key: str
    crm: CustomerRecord
    billing: list[MatchLink] = Field(default_factory=list)
    marketing: list[MatchLink] = Field(default_factory=list)

    def live_billing(self) -> list[MatchLink]:
        """Billing records that have not been merged into another record."""
        return [b for b in self.billing if not b.record.attrs.get("merged_into")]


class ConflictType(StrEnum):
    CANCELLED_BUT_BILLING_ACTIVE = "CANCELLED_BUT_BILLING_ACTIVE"
    PLAN_MISMATCH = "PLAN_MISMATCH"
    CHURNED_STILL_MARKETED = "CHURNED_STILL_MARKETED"
    EMAIL_MISMATCH = "EMAIL_MISMATCH"
    DUPLICATE_CUSTOMER = "DUPLICATE_CUSTOMER"
    PAST_DUE_BUT_CRM_ACTIVE = "PAST_DUE_BUT_CRM_ACTIVE"


class Impact(BaseModel):
    amount: float
    currency: str
    amount_usd: float
    formula: str
    monetary: bool = True


class Conflict(BaseModel):
    id: str
    type: ConflictType
    customer_key: str
    evidence: dict[str, Any]
    detected_at: datetime
    impact: Impact | None = None


class Action(StrEnum):
    UPDATE_CRM_STATUS = "update_crm_status"
    UPDATE_CRM_PLAN = "update_crm_plan"
    CANCEL_SUBSCRIPTION = "cancel_subscription"
    UNSUBSCRIBE_CONTACT = "unsubscribe_contact"
    MERGE_BILLING_DUPLICATES = "merge_billing_duplicates"
    FLAG_FOR_FINANCE_REVIEW = "flag_for_finance_review"
    NO_ACTION = "no_action"


class ProposalStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    FAILED = "FAILED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    STALE = "STALE"


class ConflictStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"  # a fix was applied and the conflict no longer detects
    GONE = "GONE"  # no longer detected for some other reason
