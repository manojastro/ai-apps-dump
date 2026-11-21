"""The fix allow-list: which actions exist, what params each takes, and which actions make sense
for which conflict type. This is code, not prompt text - the LLM can only pick from it."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.catalog import PLANS
from app.core.models import Action, Conflict, ConflictType


class _P(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateCrmStatusParams(_P):
    account_id: str
    new_status: Literal["active", "cancelled", "trial"]


class UpdateCrmPlanParams(_P):
    account_id: str
    new_plan: str


class CancelSubscriptionParams(_P):
    subscription_id: str


class UnsubscribeContactParams(_P):
    contact_id: str


class MergeBillingDuplicatesParams(_P):
    keep_customer_id: str
    remove_customer_id: str


class FlagForFinanceReviewParams(_P):
    reason: str = Field(min_length=3, max_length=300)


class NoActionParams(_P):
    pass


PARAM_MODELS: dict[Action, type[_P]] = {
    Action.UPDATE_CRM_STATUS: UpdateCrmStatusParams,
    Action.UPDATE_CRM_PLAN: UpdateCrmPlanParams,
    Action.CANCEL_SUBSCRIPTION: CancelSubscriptionParams,
    Action.UNSUBSCRIBE_CONTACT: UnsubscribeContactParams,
    Action.MERGE_BILLING_DUPLICATES: MergeBillingDuplicatesParams,
    Action.FLAG_FOR_FINANCE_REVIEW: FlagForFinanceReviewParams,
    Action.NO_ACTION: NoActionParams,
}

# Which actions are allowed for which conflict type (code-level compatibility table).
COMPATIBLE: dict[ConflictType, set[Action]] = {
    ConflictType.CANCELLED_BUT_BILLING_ACTIVE: {
        Action.CANCEL_SUBSCRIPTION, Action.UPDATE_CRM_STATUS, Action.FLAG_FOR_FINANCE_REVIEW, Action.NO_ACTION},
    ConflictType.PLAN_MISMATCH: {Action.UPDATE_CRM_PLAN, Action.FLAG_FOR_FINANCE_REVIEW, Action.NO_ACTION},
    ConflictType.CHURNED_STILL_MARKETED: {Action.UNSUBSCRIBE_CONTACT, Action.NO_ACTION},
    ConflictType.EMAIL_MISMATCH: {Action.FLAG_FOR_FINANCE_REVIEW, Action.NO_ACTION},
    ConflictType.DUPLICATE_CUSTOMER: {
        Action.MERGE_BILLING_DUPLICATES, Action.FLAG_FOR_FINANCE_REVIEW, Action.NO_ACTION},
    ConflictType.PAST_DUE_BUT_CRM_ACTIVE: {Action.FLAG_FOR_FINANCE_REVIEW, Action.NO_ACTION},
}

PARAM_SPEC = {
    "update_crm_status": {"account_id": "CRM account id", "new_status": "active|cancelled|trial"},
    "update_crm_plan": {"account_id": "CRM account id", "new_plan": "|".join(PLANS)},
    "cancel_subscription": {"subscription_id": "billing subscription id"},
    "unsubscribe_contact": {"contact_id": "marketing contact id"},
    "merge_billing_duplicates": {"keep_customer_id": "billing customer id",
                                 "remove_customer_id": "billing customer id"},
    "flag_for_finance_review": {"reason": "short reason for the finance team"},
    "no_action": {},
}


class ParamsError(ValueError):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


def _evidence_ids(conflict: Conflict) -> dict[str, set[str]]:
    ev = conflict.evidence
    billing = ev.get("billing", [])
    return {
        "subscription_id": {b["subscription_id"] for b in billing if b.get("subscription_id")},
        "billing_customer_id": {b["billing_customer_id"] for b in billing if b.get("billing_customer_id")},
        "contact_id": {m["contact_id"] for m in ev.get("marketing", [])},
        "plans": {p for p in [ev.get("crm_plan")] + [b.get("billing_plan") for b in billing] if p},
    }


def validate_params(action: Action, params: dict[str, Any], conflict: Conflict) -> dict[str, Any]:
    """Check params match the action's schema AND refer only to entities in this conflict's evidence."""
    try:
        parsed = PARAM_MODELS[action].model_validate(params or {})
    except ValidationError as e:
        raise ParamsError("bad_params", f"params do not match {action.value}: {e.errors()}") from e
    ids = _evidence_ids(conflict)
    p = parsed.model_dump()
    if "account_id" in p and p["account_id"] != conflict.customer_key:
        raise ParamsError("params_not_in_evidence", f"account_id {p['account_id']!r} is not this conflict's account")
    if action == Action.UPDATE_CRM_PLAN:
        if p["new_plan"] not in PLANS:
            raise ParamsError("bad_params", f"unknown plan {p['new_plan']!r}")
        if p["new_plan"] not in ids["plans"]:
            raise ParamsError("params_not_in_evidence", f"plan {p['new_plan']!r} does not appear in the evidence")
    if action == Action.CANCEL_SUBSCRIPTION and p["subscription_id"] not in ids["subscription_id"]:
        raise ParamsError("params_not_in_evidence", f"subscription {p['subscription_id']!r} not in evidence")
    if action == Action.UNSUBSCRIBE_CONTACT and p["contact_id"] not in ids["contact_id"]:
        raise ParamsError("params_not_in_evidence", f"contact {p['contact_id']!r} not in evidence")
    if action == Action.MERGE_BILLING_DUPLICATES:
        keep, remove = p["keep_customer_id"], p["remove_customer_id"]
        if keep == remove:
            raise ParamsError("bad_params", "keep_customer_id and remove_customer_id must differ")
        if not {keep, remove} <= ids["billing_customer_id"]:
            raise ParamsError("params_not_in_evidence", "merge ids must both be billing customers in the evidence")
    return p


def check_compatible(action: Action, conflict: Conflict) -> None:
    if action not in COMPATIBLE[conflict.type]:
        raise ParamsError("incompatible_action",
                          f"action {action.value} is not allowed for {conflict.type.value}; "
                          f"allowed: {sorted(a.value for a in COMPATIBLE[conflict.type])}")
