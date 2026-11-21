"""Offline unit tests: schema validation, coverage gates, guardrails, budget.

No API key needed — plan() is tested with an injected fake client.
Fakes here are test doubles for the Anthropic boundary, not production stubs.
"""

from __future__ import annotations

import json
import re

import pytest
from pydantic import ValidationError

from sentinel.agents.planner import (
    REQUIRED_EDGE_SIGNALS,
    build_planner_prompt,
    parse_and_validate,
    plan,
)
from sentinel.config import (
    BudgetExceeded,
    CostTracker,
    Settings,
    assert_sandbox_or_dev,
    is_action_blocked,
    is_domain_allowed,
)
from sentinel.models import TestCase, UserStory


def _story() -> UserStory:
    return UserStory(
        id="US-LEAD-001",
        title="Create Lead",
        description="Create a lead with required fields.",
        acceptance_criteria=["Last Name required.", "Company required."],
    )


def _valid_payload(story_id: str = "US-LEAD-001") -> str:
    cases = [
        {"id": f"{story_id}-HAPPY-01", "story_id": story_id, "title": "Happy: create lead with valid data",
         "type": "happy", "steps": ["Open Leads tab via navigation", "Create lead TEST-Alpha with last name and company via New button"],
         "expected_result": "Lead saved and visible", "priority": "high", "reasoning": "Core happy path."},
        {"id": f"{story_id}-NEG-01", "story_id": story_id, "title": "Negative: empty required field blocks save",
         "type": "negative", "steps": ["Attempt save with empty required field Last Name"],
         "expected_result": "Validation error shown", "priority": "high", "reasoning": "Required-field validation."},
        {"id": f"{story_id}-NEG-02", "story_id": story_id, "title": "Negative: invalid email rejected",
         "type": "negative", "steps": ["Enter invalid email format"], "expected_result": "Error shown",
         "priority": "medium", "reasoning": "Format validation."},
        {"id": f"{story_id}-BOUND-01", "story_id": story_id, "title": "Boundary: maximum-length input accepted",
         "type": "boundary", "steps": ["Enter maximum-length input of 255 chars in Last Name"],
         "expected_result": "Saved or cleanly rejected at limit", "priority": "medium", "reasoning": "Length limit."},
        {"id": f"{story_id}-EDGE-01", "story_id": story_id, "title": "Edge: special characters and emoji in name",
         "type": "edge", "steps": ["Enter special characters and emoji in Last Name"],
         "expected_result": "Saved safely without breaking layout", "priority": "low", "reasoning": "Encoding safety."},
        {"id": f"{story_id}-EDGE-02", "story_id": story_id, "title": "Edge: double-submit creates one record",
         "type": "edge", "steps": ["Double-submit the form by activating Save twice quickly"],
         "expected_result": "Single record created", "priority": "medium", "reasoning": "Idempotency."},
        {"id": f"{story_id}-EDGE-03", "story_id": story_id, "title": "Edge: browser-back mid-flow preserves data",
         "type": "edge", "steps": ["Use browser-back mid-flow then forward"],
         "expected_result": "Draft preserved or clean restart", "priority": "low", "reasoning": "Navigation safety."},
        {"id": f"{story_id}-BOUND-02", "story_id": story_id, "title": "Boundary: amount zero edge",
         "type": "boundary", "steps": ["Enter zero amount"], "expected_result": "Handled per rules",
         "priority": "low", "reasoning": "Zero boundary."},
    ]
    return json.dumps(cases)


class _FakeBlocks:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _FakeMsg:
    def __init__(self, text: str, in_tok=100, out_tok=200):
        self.content = [_FakeBlocks(text)]
        self.usage = type("U", (), {"input_tokens": in_tok, "output_tokens": out_tok})()


class _FakeMessages:
    def __init__(self, texts: list[str]):
        self._texts = list(texts)
        self.calls = 0

    def create(self, **kwargs):
        assert kwargs.get("timeout"), "LLM call must carry a timeout"
        text = self._texts[min(self.calls, len(self._texts) - 1)]
        self.calls += 1
        return _FakeMsg(text)


class _FakeClient:
    def __init__(self, texts: list[str]):
        self.messages = _FakeMessages(texts)


def _settings() -> Settings:
    return Settings(
        anthropic_api_key="test",
        anthropic_model="claude-sonnet-4-5-20250929",
        salesforce_instance_url="https://x.develop.my.salesforce.com",
        allowed_domains=["x.develop.my.salesforce.com"],
        max_tokens_per_run=100000,
        max_cost_usd_per_run=5.0,
    )


def test_models_reject_bad_test_type():
    with pytest.raises(ValidationError):
        TestCase(id="a", story_id="s", title="t", type="flaky-type", steps=["s1"], expected_result="e")


def test_parse_valid_payload_passes():
    cases = parse_and_validate(_valid_payload(), _story())
    assert len(cases) == 8
    assert {c.type for c in cases} >= {"happy", "negative", "boundary", "edge"}


def test_parse_rejects_too_few_cases():
    with pytest.raises(ValueError, match=">=8"):
        parse_and_validate(json.dumps(json.loads(_valid_payload())[:3]), _story())


def test_parse_rejects_missing_edge_signal():
    # Case-insensitive: the fixture contains both "double-submit" and "Double-submit".
    payload = re.sub("double-submit", "single click", _valid_payload(), flags=re.IGNORECASE)
    with pytest.raises(ValueError, match="missing signals"):
        parse_and_validate(payload, _story())


def test_parse_rejects_blocked_action():
    payload = _valid_payload().replace("Open Leads tab", "mass delete all records")
    with pytest.raises(ValueError, match="Blocked"):
        parse_and_validate(payload, _story())


def test_diff_requires_reasoning():
    data = json.loads(_valid_payload())
    data[0]["reasoning"] = "  "
    with pytest.raises(ValueError, match="reasoning"):
        parse_and_validate(json.dumps(data), _story(), git_diff="diff --git a/x b/x")


def test_plan_repairs_invalid_then_succeeds():
    client = _FakeClient(['[{"id": "junk"}]', _valid_payload()])
    cases = plan(_story(), settings=_settings(), client=client)
    assert len(cases) == 8
    assert client.messages.calls == 2


def test_plan_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    s = Settings(anthropic_api_key="", allowed_domains=[])
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        plan(_story(), settings=s, client=None)


def test_production_block_refuses_login_host():
    with pytest.raises(ValueError, match="production"):
        assert_sandbox_or_dev("https://login.salesforce.com")


def test_production_block_refuses_bare_prod():
    with pytest.raises(ValueError, match="production"):
        assert_sandbox_or_dev("https://acme.my.salesforce.com")


def test_production_block_allows_dev_and_sandbox():
    assert_sandbox_or_dev("https://acme.develop.my.salesforce.com")
    assert_sandbox_or_dev("https://acme.sandbox.my.salesforce.com")
    assert_sandbox_or_dev("http://localhost:8000/test")


def test_domain_allowlist():
    assert is_domain_allowed("https://a.develop.my.salesforce.com/x", ["a.develop.my.salesforce.com"])
    assert not is_domain_allowed("https://evil.com/x", ["a.develop.my.salesforce.com"])
    assert not is_domain_allowed("https://a.develop.my.salesforce.com/x", [])


def test_blocked_actions():
    assert is_action_blocked("please mass delete everything")
    assert not is_action_blocked("create a single TEST- lead")


def test_budget_kill_switch():
    t = CostTracker(max_tokens=10, max_cost_usd=100.0)
    with pytest.raises(BudgetExceeded):
        t.add(11, 0.01)


def test_prompt_includes_diff_and_caps_it():
    p = build_planner_prompt(_story(), git_diff="x" * 20000)
    assert "risk-based" in p.lower()
    assert len(p) < 20000  # capped
