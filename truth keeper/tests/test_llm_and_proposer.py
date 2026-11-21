import json

import anthropic
import pytest

from app.config import get_settings
from app.core.detection import detect_dir
from app.core.models import Action, ConflictType, ProposalStatus
from app.core.proposer import llm_payload, propose
from app.llm.client import LLMCallError, LLMClient
from app.llm.mock import MockLLM
from app.llm.prompts import available_versions, load_prompt


@pytest.fixture(scope="module")
def conflicts(dataset):
    root, _, _ = dataset
    by_type = {}
    for c in sorted(detect_dir(root).conflicts, key=lambda c: c.id):
        by_type.setdefault(c.type, c)
    return by_type


def scripted(*responses):
    return LLMClient(get_settings(), mock=MockLLM(scripted=list(responses)))


def good(c, **over):
    sub = c.evidence["billing"][0]["subscription_id"]
    base = {"explanation": "CRM cancelled, billing active.", "action": "cancel_subscription",
            "params": {"subscription_id": sub}, "confidence": 0.9, "needs_human_note": None}
    return json.dumps({**base, **over})


# ---- client --------------------------------------------------------------------------------
def test_default_mode_is_mock_and_records_usage():
    llm = LLMClient()
    assert llm.mode == "mock"
    r = llm.complete(system="s", user="Conflict type: X\n<conflict>{}</conflict>", prompt_version="v1")
    assert r.mode == "mock" and r.prompt_version == "v1" and r.tokens_estimated
    assert r.input_tokens > 0 and r.output_tokens > 0 and r.latency_ms >= 0


def test_mock_is_deterministic(conflicts):
    c = conflicts[ConflictType.PLAN_MISMATCH]
    a = propose(c, LLMClient(), "v1")
    b = propose(c, LLMClient(), "v1")
    assert a.output.model_dump() == b.output.model_dump()


def test_prompts_are_versioned():
    assert {"v1", "v2"} <= set(available_versions())
    t = load_prompt("v2")
    assert t.version == "v2" and "{{conflict_json}}" in t.user and "Source-of-truth" in t.system


def test_real_mode_never_called_in_tests(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "real")
    llm = LLMClient(get_settings())
    # no key + blocked network -> fails fast, never reaches the API
    with pytest.raises((LLMCallError, RuntimeError, TypeError, anthropic.AnthropicError)):
        llm.complete(system="s", user="u", prompt_version="v1")


# ---- proposer --------------------------------------------------------------------------------
def test_clean_mock_proposes_expected_fix_for_every_type(conflicts):
    expected = {
        ConflictType.CANCELLED_BUT_BILLING_ACTIVE: Action.CANCEL_SUBSCRIPTION,
        ConflictType.PLAN_MISMATCH: Action.UPDATE_CRM_PLAN,
        ConflictType.CHURNED_STILL_MARKETED: Action.UNSUBSCRIBE_CONTACT,
        ConflictType.EMAIL_MISMATCH: Action.FLAG_FOR_FINANCE_REVIEW,
        ConflictType.DUPLICATE_CUSTOMER: Action.MERGE_BILLING_DUPLICATES,
        ConflictType.PAST_DUE_BUT_CRM_ACTIVE: Action.FLAG_FOR_FINANCE_REVIEW,
    }
    for t, c in conflicts.items():
        r = propose(c, LLMClient(), "v1")
        assert r.status == ProposalStatus.PENDING_REVIEW, (t, r.failure_reason)
        assert r.output.action == expected[t]
        assert r.prompt_version == "v1" and r.first_try_valid and len(r.attempts) == 1


def test_only_type_and_evidence_are_sent(conflicts):
    c = conflicts[ConflictType.CANCELLED_BUT_BILLING_ACTIVE]
    mock = MockLLM()
    propose(c, LLMClient(get_settings(), mock=mock), "v1")
    sent = mock.calls[0]["user"]
    assert json.dumps(c.evidence, indent=2, sort_keys=True) in sent
    assert set(llm_payload(c)) == {"type", "evidence"}
    assert c.id not in sent and "impact" not in sent and "money" not in sent.lower()


def test_bad_json_is_retried_twice_then_failed(conflicts):
    c = conflicts[ConflictType.CANCELLED_BUT_BILLING_ACTIVE]
    r = propose(c, scripted("nope", "{not json", "still no"), "v1")
    assert r.status == ProposalStatus.FAILED and r.failure_category == "invalid_json"
    assert len(r.attempts) == 3 and r.output is None


def test_retry_recovers_and_feeds_back_the_error(conflicts):
    c = conflicts[ConflictType.CANCELLED_BUT_BILLING_ACTIVE]
    mock = MockLLM(scripted=["oops", good(c)])
    r = propose(c, LLMClient(get_settings(), mock=mock), "v1")
    assert r.status == ProposalStatus.PENDING_REVIEW and len(r.attempts) == 2 and not r.first_try_valid
    assert "rejected (invalid_json)" in mock.calls[1]["user"]


@pytest.mark.parametrize("override,category", [
    ({"action": "delete_customer", "params": {}}, "disallowed_action"),
    ({"params": {"subscription_id": "SUB-99999"}}, "params_not_in_evidence"),
    ({"params": {}}, "bad_params"),
    ({"params": {"subscription_id": "x", "extra": 1}}, "bad_params"),
    ({"explanation": "word " * 81}, "explanation_too_long"),
    ({"confidence": 1.5}, "schema_error"),
    ({"surprise": True}, "schema_error"),
    ({"action": "unsubscribe_contact", "params": {"contact_id": "MC-1"}}, "incompatible_action"),
])
def test_invalid_outputs_are_never_accepted(conflicts, override, category):
    c = conflicts[ConflictType.CANCELLED_BUT_BILLING_ACTIVE]
    bad = good(c, **override)
    r = propose(c, scripted(bad, bad, bad), "v1")
    assert r.status == ProposalStatus.FAILED and r.failure_category == category, r.failure_reason


def test_llm_call_errors_count_as_attempts(conflicts):
    class Boom(LLMClient):
        def complete(self, **kw):
            raise LLMCallError("rate_limited", "429")

    r = propose(conflicts[ConflictType.PLAN_MISMATCH], Boom(), "v1")
    assert r.status == ProposalStatus.FAILED and r.failure_category == "rate_limited" and len(r.attempts) == 3


def test_noisy_mock_never_yields_invalid_accepted_proposals(dataset):
    root, _, _ = dataset
    llm = LLMClient(get_settings(), mock=MockLLM(profile="noisy", seed=99))
    for c in detect_dir(root).conflicts[:60]:
        r = propose(c, llm, "v1")
        if r.status == ProposalStatus.PENDING_REVIEW:
            assert r.output.action.value != "delete_customer"
            assert len(r.output.explanation.split()) <= 80
