from backend.app.detectors import TraceDetector
from backend.app.simulator import SCENARIO_GROUND_TRUTH, SyntheticBackupAgentAdapter
from backend.app.verification import OutcomeVerifier


def detect(scenario: str) -> set[str]:
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run(scenario, "test")
    verified = OutcomeVerifier(adapter.artifact_provider).verify(
        trace, trace.started_at, trace.expected_outcome.deadline
    )
    return {finding.code for finding in TraceDetector().detect(trace, verified)}


def test_every_scenario_matches_ground_truth_exactly():
    for scenario, truth in SCENARIO_GROUND_TRUTH.items():
        assert detect(scenario) == truth


def test_reliable_outcome_passes_independent_verification():
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run("reliable", "test")
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        trace, trace.started_at, trace.expected_outcome.deadline
    )
    assert result.success is True
    assert all(result.checks.values())


def test_hallucinated_success_is_not_trusted():
    adapter = SyntheticBackupAgentAdapter()
    trace = adapter.run("hallucinated_success", "test")
    assert trace.claimed_outcome.success is True
    result = OutcomeVerifier(adapter.artifact_provider).verify(
        trace, trace.started_at, trace.expected_outcome.deadline
    )
    assert result.success is False
    assert "artifact exists" in result.mismatch_reasons


def test_unsafe_shell_like_input_is_only_detected_never_executed():
    trace = SyntheticBackupAgentAdapter().run("unsafe_action", "test")
    assert "UNSAFE_ACTION" in detect("unsafe_action")
    blocked_step = next(step for step in trace.steps if step.name == "shell_exec")
    assert blocked_step.success is False
    assert blocked_step.result == {"blocked": True}
