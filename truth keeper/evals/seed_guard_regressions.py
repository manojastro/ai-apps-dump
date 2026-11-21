"""Write hand-built 'guard' regression cases from the debugging exercises in the build guide.

    python -m evals.seed_guard_regressions

Each case uses a real conflict from the default dataset and a scripted (recorded) model reply that
must be handled a specific way. They make the safety rules permanent tests.
"""

from __future__ import annotations

import json

from app.config import get_settings
from app.core.detection import detect_dir
from app.core.models import ConflictType
from app.core.regressions import build_case, save_case
from evals.run_all import ensure_dataset

BAD_JSON = "Sure! Here is my fix: {action: cancel_subscription"


def main() -> None:
    s = get_settings()
    data_dir, _ = ensure_dataset("default")
    by_type = {}
    for c in sorted(detect_dir(data_dir, respect_review_flags=False).conflicts, key=lambda c: c.id):
        by_type.setdefault(c.type, c)

    def cdict(c):
        return {"id": c.id, "type": c.type.value, "customer_key": c.customer_key, "evidence": c.evidence}

    cba = by_type[ConflictType.CANCELLED_BUT_BILLING_ACTIVE]
    sub = cba.evidence["billing"][0]["subscription_id"]
    good = {"explanation": "CRM says cancelled but billing is still charging.", "action": "cancel_subscription",
            "params": {"subscription_id": sub}, "confidence": 0.9, "needs_human_note": None}
    csm = by_type[ConflictType.CHURNED_STILL_MARKETED]
    pdue = by_type[ConflictType.PAST_DUE_BUT_CRM_ACTIVE]
    dup = by_type[ConflictType.DUPLICATE_CUSTOMER]
    ids = [b["billing_customer_id"] for b in dup.evidence["billing"]]

    cases = [
        build_case(source="guard", conflict=cdict(cba), prompt_version="v1",
                   recorded_responses=[BAD_JSON] * 3,
                   expect_mock={"status": "FAILED", "failure_category": "invalid_json"},
                   expected_action="cancel_subscription",
                   note="model always returns bad JSON: retried twice then FAILED, never accepted"),
        build_case(source="guard", conflict=cdict(cba), prompt_version="v1",
                   recorded_responses=[json.dumps({**good, "action": "delete_customer", "params": {}})] * 3,
                   expect_mock={"status": "FAILED", "failure_category": "disallowed_action"},
                   expected_action="cancel_subscription",
                   note="action outside the allow-list is rejected by the Enum"),
        build_case(source="guard", conflict=cdict(cba), prompt_version="v1",
                   recorded_responses=[json.dumps({**good, "params": {"subscription_id": "SUB-99999"}})] * 3,
                   expect_mock={"status": "FAILED", "failure_category": "params_not_in_evidence"},
                   expected_action="cancel_subscription",
                   note="invented subscription id is rejected: params must reference evidence"),
        build_case(source="guard", conflict=cdict(csm), prompt_version="v1",
                   recorded_responses=[json.dumps({**good, "action": "cancel_subscription",
                                                   "params": {"subscription_id": "x"}})] * 3,
                   expect_mock={"status": "FAILED", "failure_category": "incompatible_action"},
                   expected_action="unsubscribe_contact",
                   note="allowed action, but not compatible with CHURNED_STILL_MARKETED"),
        build_case(source="guard", conflict=cdict(pdue), prompt_version="v1",
                   recorded_responses=[json.dumps({"explanation": "word " * 120, "action": "flag_for_finance_review",
                                                   "params": {"reason": "overdue"}, "confidence": 0.7,
                                                   "needs_human_note": None})] * 3,
                   expect_mock={"status": "FAILED", "failure_category": "explanation_too_long"},
                   expected_action="flag_for_finance_review", note="explanation over 80 words"),
        build_case(source="guard", conflict=cdict(cba), prompt_version="v1",
                   recorded_responses=[BAD_JSON, "```json\n" + json.dumps(good) + "\n```"],
                   expect_mock={"status": "PENDING_REVIEW", "action": "cancel_subscription", "attempts": 2},
                   expected_action="cancel_subscription",
                   note="bad first reply, valid (fenced) second reply: retry recovers"),
        build_case(source="guard", conflict=cdict(dup), prompt_version="v1",
                   recorded_responses=[json.dumps({"explanation": "Two billing records.",
                                                   "action": "merge_billing_duplicates",
                                                   "params": {"keep_customer_id": ids[0],
                                                              "remove_customer_id": ids[0]},
                                                   "confidence": 0.8, "needs_human_note": None})] * 3,
                   expect_mock={"status": "FAILED", "failure_category": "bad_params"},
                   expected_action="merge_billing_duplicates", note="merge into itself is rejected"),
    ]
    for c in cases:
        print("wrote", save_case(s.regressions_dir, c).name, "-", c["note"])


if __name__ == "__main__":
    main()
