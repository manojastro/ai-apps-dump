import pytest

from packages.agent.contracts import Budget, Diagnosis, Evidence, action_hash, verify_recovery


def test_budget_reserves_before_tool_call():
    budget = Budget(tool_limit=1)
    budget.reserve_tool()
    with pytest.raises(ValueError, match="budget"):
        budget.reserve_tool()
    assert budget.tool_calls == 1


def test_diagnosis_cannot_cite_another_runs_evidence():
    evidence = Evidence.make("run-a", "metrics", {"latency_ms": 800}, "Latency elevated")
    diagnosis = Diagnosis(
        category="payment_delay",
        confidence="supported",
        explanation="Slow payment",
        evidence_ids=[evidence.id],
        missing=[],
    )
    with pytest.raises(ValueError, match="scope"):
        diagnosis.validate_evidence([evidence], "run-b")


def test_approval_binds_exact_parameters():
    a = {"operation": "reset_demo", "target": "checkout", "parameters": {"revision": 1}}
    b = {**a, "parameters": {"revision": 2}}
    assert action_hash(a) != action_hash(b)
    assert action_hash(a) == action_hash(dict(reversed(list(a.items()))))


def test_executor_success_is_not_recovery_proof():
    assert not verify_recovery(
        {"error_rate": 0.3, "p95_ms": 900}, {"samples": 2, "error_rate": 0, "p95_ms": 100}
    )["verified"]


def test_recovery_requires_both_latency_and_error_improvement():
    before = {"error_rate": 0.3, "p95_ms": 900}
    assert verify_recovery(before, {"samples": 100, "error_rate": 0.01, "p95_ms": 110})["verified"]
    assert not verify_recovery(before, {"samples": 100, "error_rate": 0.3, "p95_ms": 110})["verified"]
