from evalharness.dataset import generate_demo_cases
from evalharness.engine import EvaluationEngine, compare_runs
from evalharness.gate import apply_gate
from evalharness.models import GateConfig
from evalharness.targets import DemoAgentTarget


def config():
    return GateConfig(
        absolute_thresholds={"task_success": .9, "groundedness": .85},
        max_relative_regression=.03, max_p95_latency_ms=500,
        max_cost_per_request_usd=.002, forbid_unsafe_tools=True,
    )


def test_good_run_passes_and_bad_run_fails_against_baseline():
    cases = generate_demo_cases()[:20] + generate_demo_cases()[-5:]
    engine = EvaluationEngine()
    baseline = engine.run(cases, DemoAgentTarget("good"))
    candidate = engine.run(cases, DemoAgentTarget("bad"))
    assert apply_gate(baseline, config())["passed"]
    result = apply_gate(candidate, config(), baseline)
    assert not result["passed"]
    assert {failure["type"] for failure in result["failures"]} >= {
        "absolute_threshold", "latency", "cost", "unsafe_tool", "relative_regression"
    }


def test_comparison_lists_cases_that_changed():
    cases = generate_demo_cases()[:3]
    engine = EvaluationEngine()
    good = engine.run(cases, DemoAgentTarget("good"))
    bad = engine.run(cases, DemoAgentTarget("bad"))
    comparison = compare_runs(bad, good)
    assert len(comparison["changed_cases"]) == 3
    assert comparison["regressions"]["task_success"] == 1


def test_judge_configuration_is_pinned_in_metadata():
    report = EvaluationEngine().run(generate_demo_cases()[:1], DemoAgentTarget("good"))
    assert report.judge_config == {"provider": "mock", "model": "mock-judge-v1", "version": "1.0.0"}

