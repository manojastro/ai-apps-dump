"""Verifier tests: full classification matrix with fake run functions.

No browser, no org — verify() takes an injectable run_once, so every branch
of the false-alarm logic is proven offline. Fakes here are test doubles for
the Phase-2 browser runner, not production stubs.
"""

from __future__ import annotations

import pytest

from sentinel.agents.verifier import AttemptResult, classify_attempts, verify
from sentinel.models import RunTrace, StepResult


def _fail_step(idx=0, err="Save button did nothing", target='click button "Save"') -> StepResult:
    return StepResult(step_index=idx, action="click", target_description=target,
                      succeeded=False, error=err,
                      console_errors=["Uncaught TypeError: x is null"],
                      failed_network_calls=[])


def _trace(tc="TC-1", run=1, failed=True, err="Save button did nothing") -> RunTrace:
    steps = [_fail_step(err=err)] if failed else [
        StepResult(step_index=0, action="click", target_description='click button "Save"', succeeded=True)]
    return RunTrace(test_case_id=tc, run_number=run, step_results=steps,
                    final_state="fail" if failed else "pass")


def _attempt(failed=True, env="", run=1, err="Save button did nothing") -> AttemptResult:
    return AttemptResult(trace=_trace(run=run, failed=failed, err=err), env_failure=env)


def _runner(script: list[AttemptResult]):
    calls: list[int] = []

    def run_once(run_number: int) -> AttemptResult:
        calls.append(run_number)
        return script[min(len(calls) - 1, len(script) - 1)]

    run_once.calls = calls  # type: ignore[attr-defined]
    return run_once


def test_three_of_three_is_real_bug():
    r = _runner([_attempt(run=1), _attempt(run=2), _attempt(run=3)])
    v = verify("TC-1", r)
    assert v.classification == "real_bug" and v.runs_attempted == 3 and v.runs_failed == 3
    assert r.calls == [1, 2, 3]  # always runs all three, never short-circuits a conviction
    assert "3/3" in v.evidence_summary


def test_one_of_three_is_flaky_and_files_nothing():
    r = _runner([_attempt(failed=False, run=1), _attempt(run=2), _attempt(failed=False, run=3)])
    v = verify("TC-1", r)
    assert v.classification == "flaky" and v.runs_failed == 1


def test_two_of_three_is_flaky():
    v = classify_attempts("TC-1", [_attempt(run=1), _attempt(run=2), _attempt(failed=False, run=3)])
    assert v.classification == "flaky" and v.runs_failed == 2


def test_zero_of_three_is_pass():
    v = verify("TC-1", _runner([_attempt(failed=False, run=i) for i in (1, 2, 3)]))
    assert v.classification == "pass" and v.runs_failed == 0


def test_all_env_failures_is_blocked_never_bug():
    v = verify("TC-1", _runner([_attempt(env="org unreachable", run=i) for i in (1, 2, 3)]))
    assert v.classification == "blocked"
    assert "Not a bug" in v.evidence_summary


def test_login_failure_is_blocked():
    v = classify_attempts("TC-1", [_attempt(env="sf session expired (401)", run=i) for i in (1, 2, 3)])
    assert v.classification == "blocked"


def test_mixed_env_and_product_failure_is_blocked_not_bug():
    """Unreliable lab must not produce a bug report, even with real failures present."""
    v = classify_attempts("TC-1", [_attempt(run=1), _attempt(env="login broke", run=2), _attempt(run=3)])
    assert v.classification == "blocked"
    assert "refusing to file" in v.evidence_summary.lower()


def test_runner_crash_counts_as_env_failure():
    def boom(run_number: int) -> AttemptResult:
        raise ConnectionError("browser disconnected")

    v = verify("TC-1", boom)
    assert v.classification == "blocked" and v.runs_attempted == 3


def test_inconsistent_failure_steps_lower_confidence():
    v = classify_attempts("TC-1", [
        _attempt(run=1, err="Save did nothing"),
        _attempt(run=2, err="Lookup returned 500"),
        _attempt(run=3, err="Save did nothing"),
    ])
    assert v.classification == "real_bug" and v.confidence < 0.95


def test_cannot_convict_on_fewer_than_three_runs():
    with pytest.raises(ValueError, match="Cannot convict"):
        classify_attempts("TC-1", [_attempt(run=1), _attempt(run=2)])


def test_empty_attempts_rejected():
    with pytest.raises(ValueError, match="at least one"):
        classify_attempts("TC-1", [])
