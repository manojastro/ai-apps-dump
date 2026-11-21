"""Replay every saved regression case (evals/regressions/*.json).

MOCK mode (always): feed the recorded model responses back through the real validators and
assert the system handles them exactly as recorded (FAILED stays FAILED, etc.).
Real mode (on demand: LLM_MODE=real RUN_REAL_TESTS=1): ask the live model again and assert it
now proposes the expected action.
"""

import os
from datetime import UTC, datetime

import pytest

from app.config import ROOT, get_settings
from app.core.models import Conflict, ConflictType
from app.core.proposer import propose
from app.core.regressions import load_cases
from app.llm.client import LLMClient
from app.llm.mock import MockLLM

CASES = load_cases(ROOT / "evals" / "regressions")


def to_conflict(case) -> Conflict:
    c = case["conflict"]
    return Conflict(id=c["id"], type=ConflictType(c["type"]), customer_key=c["customer_key"], evidence=c["evidence"],
                    detected_at=datetime.now(UTC))


def test_there_are_at_least_five_regression_cases():
    assert len(CASES) >= 5


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_replay_in_mock_mode(case):
    responses = [r for r in case["recorded_responses"] if r is not None]
    llm = LLMClient(get_settings(), mock=MockLLM(scripted=responses + [responses[-1]] * 3))
    r = propose(to_conflict(case), llm, case["prompt_version"])
    exp = case["expect_mock"]
    assert r.status.value == exp["status"], r.failure_reason
    if "failure_category" in exp:
        assert r.failure_category == exp["failure_category"]
    if "action" in exp:
        assert r.output and r.output.action.value == exp["action"]
    if "attempts" in exp:
        assert len(r.attempts) == exp["attempts"]


@pytest.mark.real
@pytest.mark.skipif(not (os.getenv("LLM_MODE") == "real" and os.getenv("RUN_REAL_TESTS") == "1"),
                    reason="real-model replay runs only on demand")
@pytest.mark.parametrize("case", [c for c in CASES if c["expected_action"]], ids=lambda c: c["id"])
def test_replay_against_real_model(case):  # pragma: no cover - needs an API key
    r = propose(to_conflict(case), LLMClient(get_settings()), case["prompt_version"])
    assert r.output and r.output.action.value == case["expected_action"]
