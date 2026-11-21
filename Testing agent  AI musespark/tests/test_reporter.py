"""Reporter tests: assembly gates, signatures, duplicate routing. All offline."""

from __future__ import annotations

import pytest

from sentinel.agents.reporter import (
    assemble_bug_report,
    duplicate_score,
    error_signature,
    find_duplicate,
)
from sentinel.models import RunTrace, StepResult, TestCase, Verdict


def _case() -> TestCase:
    return TestCase(id="TC-LEAD-001-HAPPY-1", story_id="US-LEAD-001",
                    title="Happy: create lead with valid data", type="happy",
                    steps=["Open Leads tab", "Create TEST- lead via New button"],
                    expected_result="Lead saved and visible", priority="high")


def _trace(run=1) -> RunTrace:
    return RunTrace(test_case_id="TC-LEAD-001-HAPPY-1", run_number=run, final_state="fail",
                    step_results=[
                        StepResult(step_index=0, action="click", target_description='click button "Save"',
                                   succeeded=True),
                        StepResult(step_index=1, action="click", target_description='click button "Save"',
                                   succeeded=False, error="Save button did nothing",
                                   console_errors=["Uncaught TypeError: x is null"]),
                    ])


def _verdict(cls="real_bug") -> Verdict:
    return Verdict(test_case_id="TC-LEAD-001-HAPPY-1", classification=cls, confidence=0.95,
                   evidence_summary="Failed 3/3 fresh runs.", runs_attempted=3, runs_failed=3)


def test_assembles_complete_report():
    report = assemble_bug_report(verdict=_verdict(), test_case=_case(), traces=[_trace()],
                                 environment="Chromium 1390x900, Dev org na123",
                                 test_data_used="Lead TEST-917 (LastName, Company Acme)")
    assert report.title.startswith("[TC-LEAD-001-HAPPY-1]")
    assert len(report.steps_to_reproduce) == 3  # case steps + observed failure
    assert "3/3" in report.actual
    assert report.console_log == ["Uncaught TypeError: x is null"]
    assert report.test_data_used.startswith("Lead TEST-")
    assert report.suspected_duplicate_of is None


def test_refuses_non_bug_verdicts():
    for cls in ("flaky", "blocked", "pass"):
        with pytest.raises(ValueError, match="only files real_bug"):
            assemble_bug_report(verdict=_verdict(cls), test_case=_case(), traces=[_trace()],
                                environment="env", test_data_used="data")


def test_refuses_thin_report():
    with pytest.raises(ValueError, match="empty"):
        assemble_bug_report(verdict=_verdict(), test_case=_case(), traces=[_trace()],
                            environment="  ", test_data_used="data")


def test_refuses_verdict_case_mismatch():
    bad = Verdict(test_case_id="TC-OTHER", classification="real_bug", confidence=0.9,
                  evidence_summary="x", runs_attempted=3, runs_failed=3)
    with pytest.raises(ValueError, match="does not match"):
        assemble_bug_report(verdict=bad, test_case=_case(), traces=[_trace()],
                            environment="env", test_data_used="data")


def test_signature_stable_across_runs():
    assert error_signature(_trace(run=1)) == error_signature(_trace(run=3))


def test_finds_duplicate_by_signature():
    report = assemble_bug_report(verdict=_verdict(), test_case=_case(), traces=[_trace()],
                                 environment="env", test_data_used="data")
    sig = error_signature(_trace())
    existing = [{"key": "SENT-42", "title": "[TC-LEAD-001-HAPPY-1] Happy: create lead with valid data",
                 "signature": sig},
                {"key": "SENT-7", "title": "Unrelated login flake", "signature": "other"}]
    assert find_duplicate(report, existing, signature=sig) == "SENT-42"


def test_no_duplicate_for_novel_bug():
    report = assemble_bug_report(verdict=_verdict(), test_case=_case(), traces=[_trace()],
                                 environment="env", test_data_used="data")
    existing = [{"key": "SENT-7", "title": "Unrelated login flake", "signature": "other"}]
    assert find_duplicate(report, existing, signature=error_signature(_trace())) is None


def test_duplicate_score_bounds():
    assert duplicate_score("a b c", "sig", "a b c", "sig") == 1.0
    assert duplicate_score("alpha beta", "x", "gamma delta", "y") < 0.5
