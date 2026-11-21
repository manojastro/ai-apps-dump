"""Deterministic MOCK LLM. Zero cost, no network.

Profiles:
  clean    - answers like a well-behaved model following the v2 source-of-truth policy
  noisy    - same, but injects realistic faults at fixed rates (bad JSON, actions outside the
             allow-list, wrong-but-allowed actions, over-long explanations, invented ids) so the
             retry / failure / eval / regression machinery can be exercised offline
  scripted - returns a fixed list of responses in order (tests and regression replays)

Numbers produced in MOCK mode measure the plumbing, not a model. They are labelled as such.
"""

from __future__ import annotations

import json
import random
import re
from collections.abc import Iterable

_CONFLICT = re.compile(r"<conflict>\s*(.*?)\s*</conflict>", re.DOTALL)
_TYPE = re.compile(r"Conflict type:\s*([A-Z_]+)")

NOISY_RATES = {
    "bad_json": 0.06,
    "disallowed_action": 0.03,
    "wrong_action": 0.06,
    "long_explanation": 0.03,
    "invented_id": 0.04,
}


def _oracle(ctype: str, ev: dict) -> dict:
    billing = ev.get("billing") or []
    acct = ev.get("crm_account_id")
    if ctype == "CANCELLED_BUT_BILLING_ACTIVE":
        b = billing[0]
        return {
            "explanation": (f"The CRM marks account {acct} as cancelled, but billing subscription "
                            f"{b['subscription_id']} is still {b['billing_status']} at {b['monthly_amount']} "
                            f"{b['currency']} per month. The customer will be charged after cancelling."),
            "action": "cancel_subscription", "params": {"subscription_id": b["subscription_id"]},
            "confidence": 0.9, "needs_human_note": "Check whether a refund for past charges is owed.",
        }
    if ctype == "PLAN_MISMATCH":
        b = billing[0]
        return {
            "explanation": (f"The CRM lists plan '{ev.get('crm_plan')}' for {acct}, but billing charges for "
                            f"'{b['billing_plan']}' ({b['monthly_amount']} {b['currency']}/month). Billing "
                            "reflects what the customer pays, so the CRM is out of date."),
            "action": "update_crm_plan", "params": {"account_id": acct, "new_plan": b["billing_plan"]},
            "confidence": 0.85, "needs_human_note": None,
        }
    if ctype == "CHURNED_STILL_MARKETED":
        m = ev["marketing"][0]
        return {
            "explanation": (f"Account {acct} is cancelled in the CRM, but marketing contact {m['contact_id']} is "
                            f"still subscribed in stage '{m['lifecycle_stage']}' (last campaign "
                            f"{m['last_campaign']}). A churned customer is still receiving onboarding email."),
            "action": "unsubscribe_contact", "params": {"contact_id": m["contact_id"]},
            "confidence": 0.92, "needs_human_note": None,
        }
    if ctype == "EMAIL_MISMATCH":
        mm = ev["mismatches"][0]
        return {
            "explanation": (f"The CRM email for {acct} is {ev.get('crm_email')}, but the {mm['system']} record "
                            f"{mm['record_id']} uses {mm['other_email']}. Invoices or notices may reach the "
                            "wrong person. Which address is correct needs a human decision."),
            "action": "flag_for_finance_review",
            "params": {"reason": f"Email differs between CRM and {mm['system']} for {acct}"},
            "confidence": 0.75, "needs_human_note": "Confirm the correct billing contact with the account owner.",
        }
    if ctype == "DUPLICATE_CUSTOMER":
        ordered = sorted(billing, key=lambda b: (b["match_method"] != "id", b["billing_customer_id"]))
        keep, remove = ordered[0]["billing_customer_id"], ordered[1]["billing_customer_id"]
        return {
            "explanation": (f"Account {acct} has {len(billing)} live billing customers ({keep} and {remove}), "
                            "each with its own subscription, so the customer is likely charged twice."),
            "action": "merge_billing_duplicates",
            "params": {"keep_customer_id": keep, "remove_customer_id": remove},
            "confidence": 0.88, "needs_human_note": "Refund any double charges after merging.",
        }
    if ctype == "PAST_DUE_BUT_CRM_ACTIVE":
        b = billing[0]
        return {
            "explanation": (f"Billing shows subscription {b['subscription_id']} past due for {b['days_past_due']} "
                            f"days, but the CRM still lists {acct} as an active, healthy account. Sales and "
                            "support do not know the account is at risk."),
            "action": "flag_for_finance_review",
            "params": {"reason": f"{b['days_past_due']} days past due while CRM shows active"},
            "confidence": 0.8, "needs_human_note": None,
        }
    return {"explanation": "Unknown conflict type.", "action": "no_action", "params": {}, "confidence": 0.1,
            "needs_human_note": "Unknown conflict type."}


_WRONG = {
    "cancel_subscription": ("no_action", {}),
    "update_crm_plan": ("flag_for_finance_review", {"reason": "Plan differs; please check"}),
    "unsubscribe_contact": ("no_action", {}),
    "flag_for_finance_review": ("no_action", {}),
    "merge_billing_duplicates": ("flag_for_finance_review", {"reason": "Possible duplicate"}),
}


class MockLLM:
    def __init__(self, profile: str = "clean", seed: int = 1234, scripted: Iterable[str] | None = None,
                 rates: dict[str, float] | None = None):
        self.profile = "scripted" if scripted is not None else profile
        self._scripted = list(scripted) if scripted is not None else None
        self._rng = random.Random(seed)
        self.rates = rates or NOISY_RATES
        self.calls: list[dict] = []

    def respond(self, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        if self._scripted is not None:
            if not self._scripted:
                raise RuntimeError("scripted MockLLM ran out of responses")
            return self._scripted.pop(0)
        cm, tm = _CONFLICT.search(user), _TYPE.search(user)
        if not cm or not tm:
            return json.dumps({"explanation": "No conflict provided.", "action": "no_action", "params": {},
                               "confidence": 0.0, "needs_human_note": "empty input"})
        out = _oracle(tm.group(1), json.loads(cm.group(1)))
        if self.profile == "noisy":
            out = self._inject(out)
            if isinstance(out, str):
                return out
        return json.dumps(out)

    def _inject(self, out: dict) -> dict | str:
        r = self._rng.random()
        acc = 0.0
        for fault, rate in self.rates.items():  # noqa: B007 - `fault` is used after the loop breaks
            acc += rate
            if r < acc:
                break
        else:
            return out
        if fault == "bad_json":
            return "Sure! Here is my proposal: {action: " + out["action"] + ", params: ..."
        if fault == "disallowed_action":
            return {**out, "action": "delete_customer", "params": {}}
        if fault == "wrong_action" and out["action"] in _WRONG:
            action, params = _WRONG[out["action"]]
            return {**out, "action": action, "params": params, "confidence": 0.55}
        if fault == "long_explanation":
            return {**out, "explanation": " ".join([out["explanation"]] * 4)}
        if fault == "invented_id":
            params = {k: ("SUB-99999" if k.endswith("_id") and k != "account_id" else v)
                      for k, v in out["params"].items()}
            if params != out["params"]:
                return {**out, "params": params}
        return out
