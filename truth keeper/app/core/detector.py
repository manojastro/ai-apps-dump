"""Rule-based conflict detector. Code decides whether a conflict exists - never the LLM.

Each rule takes one UnifiedCustomer and returns a Conflict or None. Evidence always holds the
exact field values from each system that triggered the rule, so a reviewer (and the LLM)
can see why it fired. Conflict ids are deterministic: same type + customer -> same id.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, date, datetime

from app.core.catalog import PAST_DUE_THRESHOLD_DAYS
from app.core.models import Conflict, ConflictType, MatchLink, UnifiedCustomer

CHARGING_STATUSES = {"active", "past_due"}


def conflict_id(ctype: ConflictType, customer_key: str) -> str:
    return "cf_" + hashlib.sha1(f"{ctype.value}|{customer_key}".encode()).hexdigest()[:12]


def _billing_ev(link: MatchLink) -> dict:
    r = link.record
    return {
        "billing_customer_id": r.record_id,
        "subscription_id": r.attrs.get("subscription_id"),
        "billing_status": r.status,
        "billing_plan": r.plan,
        "billing_email": r.raw_email,
        "monthly_amount": r.attrs.get("monthly_amount"),
        "currency": r.attrs.get("currency"),
        "next_charge_date": r.attrs.get("next_charge_date"),
        "past_due_since": r.attrs.get("past_due_since"),
        "match_method": link.method,
        "match_confidence": link.confidence,
    }


def _crm_ev(c: UnifiedCustomer) -> dict:
    return {
        "crm_account_id": c.crm.record_id,
        "crm_status": c.crm.status,
        "crm_plan": c.crm.plan,
        "crm_email": c.crm.raw_email,
        "crm_name": c.crm.raw_name,
    }


def _make(ctype: ConflictType, c: UnifiedCustomer, evidence: dict, now: datetime) -> Conflict:
    return Conflict(id=conflict_id(ctype, c.customer_key), type=ctype, customer_key=c.customer_key,
                    evidence=evidence, detected_at=now)


def rule_cancelled_but_billing_active(c: UnifiedCustomer, as_of: date, now: datetime) -> Conflict | None:
    if c.crm.status != "cancelled":
        return None
    charging = [b for b in c.live_billing() if b.record.status in CHARGING_STATUSES]
    if not charging:
        return None
    return _make(ConflictType.CANCELLED_BUT_BILLING_ACTIVE, c,
                 {**_crm_ev(c), "billing": [_billing_ev(b) for b in charging]}, now)


def rule_plan_mismatch(c: UnifiedCustomer, as_of: date, now: datetime) -> Conflict | None:
    if c.crm.status != "active" or not c.crm.plan:
        return None
    diff = [b for b in c.live_billing()
            if b.record.status in CHARGING_STATUSES and b.record.plan and b.record.plan != c.crm.plan]
    if not diff:
        return None
    return _make(ConflictType.PLAN_MISMATCH, c, {**_crm_ev(c), "billing": [_billing_ev(b) for b in diff]}, now)


def rule_churned_still_marketed(c: UnifiedCustomer, as_of: date, now: datetime) -> Conflict | None:
    if c.crm.status != "cancelled":
        return None
    subscribed = [m for m in c.marketing if m.record.attrs.get("subscribed")]
    if not subscribed:
        return None
    contacts = [
        {
            "contact_id": m.record.record_id,
            "marketing_email": m.record.raw_email,
            "subscribed": True,
            "lifecycle_stage": m.record.attrs.get("lifecycle_stage"),
            "last_campaign": m.record.attrs.get("last_campaign"),
            "match_method": m.method,
            "match_confidence": m.confidence,
        }
        for m in subscribed
    ]
    return _make(ConflictType.CHURNED_STILL_MARKETED, c, {**_crm_ev(c), "marketing": contacts}, now)


def rule_email_mismatch(c: UnifiedCustomer, as_of: date, now: datetime) -> Conflict | None:
    if not c.crm.email:
        return None
    diffs = []
    for link in c.live_billing() + c.marketing:
        if link.record.email and link.record.email != c.crm.email:
            diffs.append({
                "system": link.record.system.value,
                "record_id": link.record.record_id,
                "other_email": link.record.raw_email,
                "match_method": link.method,
                "match_confidence": link.confidence,
                "monthly_amount": link.record.attrs.get("monthly_amount"),
                "currency": link.record.attrs.get("currency"),
            })
    if not diffs:
        return None
    return _make(ConflictType.EMAIL_MISMATCH, c, {**_crm_ev(c), "mismatches": diffs}, now)


def rule_duplicate_customer(c: UnifiedCustomer, as_of: date, now: datetime) -> Conflict | None:
    live = c.live_billing()
    if len(live) < 2:
        return None
    return _make(ConflictType.DUPLICATE_CUSTOMER, c, {**_crm_ev(c), "billing": [_billing_ev(b) for b in live]}, now)


def rule_past_due_but_crm_active(c: UnifiedCustomer, as_of: date, now: datetime) -> Conflict | None:
    if c.crm.status != "active":
        return None
    hits = []
    for b in c.live_billing():
        since = b.record.attrs.get("past_due_since")
        if b.record.status == "past_due" and since:
            days = (as_of - date.fromisoformat(since)).days
            if days > PAST_DUE_THRESHOLD_DAYS:
                hits.append({**_billing_ev(b), "days_past_due": days})
    if not hits:
        return None
    return _make(ConflictType.PAST_DUE_BUT_CRM_ACTIVE, c,
                 {**_crm_ev(c), "billing": hits, "threshold_days": PAST_DUE_THRESHOLD_DAYS}, now)


RULES: dict[ConflictType, Callable[[UnifiedCustomer, date, datetime], Conflict | None]] = {
    ConflictType.CANCELLED_BUT_BILLING_ACTIVE: rule_cancelled_but_billing_active,
    ConflictType.PLAN_MISMATCH: rule_plan_mismatch,
    ConflictType.CHURNED_STILL_MARKETED: rule_churned_still_marketed,
    ConflictType.EMAIL_MISMATCH: rule_email_mismatch,
    ConflictType.DUPLICATE_CUSTOMER: rule_duplicate_customer,
    ConflictType.PAST_DUE_BUT_CRM_ACTIVE: rule_past_due_but_crm_active,
}


def detect(customers: list[UnifiedCustomer], as_of: date, suppressed_ids: set[str] | None = None,
           now: datetime | None = None) -> list[Conflict]:
    """Run every rule over every customer.

    suppressed_ids: conflicts that already have an open finance-review flag (handed to a human
    queue outside this tool) are not re-reported.
    """
    now = now or datetime.now(UTC)
    suppressed_ids = suppressed_ids or set()
    out: list[Conflict] = []
    for c in customers:
        for rule in RULES.values():
            hit = rule(c, as_of, now)
            if hit and hit.id not in suppressed_ids:
                out.append(hit)
    return out
