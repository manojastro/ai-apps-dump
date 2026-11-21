"""M26 tests: benchmark integrity (30 scenarios + 3 traces, zero unsafe)."""

from __future__ import annotations


def test_benchmark_loads_30() -> None:
    from evaluation.run_benchmark import load_scenarios

    scenarios = load_scenarios()
    assert len(scenarios) == 30
    assert len({s["id"] for s in scenarios}) == 30  # unique ids


def test_benchmark_scores_and_reports() -> None:
    from evaluation.run_benchmark import REPORT_PATH, run_benchmark

    results = run_benchmark(write_report_file=True)
    summary = results["summary"]
    assert summary["scenarios"] == 30 and summary["passed"] == 30
    assert summary["accuracy"] == 1.0
    assert summary["unsafe_action_rate"] == 0.0
    assert summary["red_herring_rejection"] == 1.0
    assert summary["traces_passed"] == summary["traces"] == 3
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "accuracy: 1.0" in text and "Unsafe action rate: 0.0" in text
