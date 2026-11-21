"""Metric engine + harness runner tests: exact numbers on a scripted matrix."""

from __future__ import annotations

import pytest

from evals.metrics import EvalResult, compute_metrics, render_markdown
from evals.run_evals import AgentOutcome, GoldenScenario, load_scenarios, run_golden


def _matrix() -> list[EvalResult]:
    # 3 real bugs (predict 2, miss 1), 2 flaky (1 false alarm), 1 blocked (1 misclassified), 1 pass.
    return [
        EvalResult(scenario_id="b1", expected="real_bug", predicted="real_bug", cost_usd=0.10, steps=5, bug_quality=5),
        EvalResult(scenario_id="b2", expected="real_bug", predicted="real_bug", cost_usd=0.20, steps=7, bug_quality=4),
        EvalResult(scenario_id="b3", expected="real_bug", predicted="pass", cost_usd=0.10, steps=4),
        EvalResult(scenario_id="f1", expected="flaky", predicted="real_bug", cost_usd=0.30, steps=9),
        EvalResult(scenario_id="f2", expected="flaky", predicted="flaky", cost_usd=0.10, steps=6),
        EvalResult(scenario_id="k1", expected="blocked", predicted="real_bug", cost_usd=0.05, steps=2),
        EvalResult(scenario_id="p1", expected="pass", predicted="pass", cost_usd=0.05, steps=3),
    ]


def test_confusion_matrix_math():
    r = compute_metrics(_matrix())
    assert r.n == 7
    assert r.precision == pytest.approx(2 / 4)   # 2 TP of 4 predicted bugs
    assert r.recall == pytest.approx(2 / 3)      # 2 found of 3 real bugs
    assert r.false_alarm_rate == pytest.approx(1 / 2)
    assert r.blocked_misclassification_rate == pytest.approx(1.0)
    assert r.mean_cost_usd == pytest.approx(0.90 / 7)
    assert r.mean_steps == pytest.approx(36 / 7)
    assert r.bug_quality_mean == pytest.approx(4.5) and r.bug_quality_n == 2


def test_empty_results_is_zero_not_crash():
    r = compute_metrics([])
    assert (r.precision, r.recall, r.false_alarm_rate) == (0.0, 0.0, 0.0)
    assert r.bug_quality_mean is None


def test_markdown_renders_all_seven_metrics():
    md = render_markdown(compute_metrics(_matrix()))
    for label in ("Precision", "Recall", "False-alarm", "Blocked-misclassification",
                  "Mean cost", "Mean steps", "Bug report quality"):
        assert label in md


def test_runner_end_to_end_with_scripted_agent():
    scenarios = [GoldenScenario(id="b1", flow="x", expected="real_bug"),
                 GoldenScenario(id="f1", flow="y", expected="flaky")]
    answers = {"b1": AgentOutcome(predicted="real_bug", cost_usd=0.1, steps=5, bug_quality=5),
               "f1": AgentOutcome(predicted="flaky", cost_usd=0.1, steps=5)}
    report = run_golden(scenarios, lambda s: answers[s.id])
    assert report.n == 2 and report.precision == 1.0 and report.recall == 1.0


def test_agent_crash_becomes_blocked_not_bug():
    scenarios = [GoldenScenario(id="k1", flow="x", expected="blocked")]

    def boom(scenario):
        raise ConnectionError("org down")

    report = run_golden(scenarios, boom)
    assert report.blocked_misclassification_rate == 0.0  # crash must never count as a bug


def test_loader_validates(tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text("- id: G-1\n  flow: create lead\n  expected: pass\n", encoding="utf-8")
    assert [s.id for s in load_scenarios(str(good))] == ["G-1"]

    bad = tmp_path / "bad.yaml"
    bad.write_text("- id: G-1\n  flow: x\n  expected: maybe\n", encoding="utf-8")
    with pytest.raises(Exception):
        load_scenarios(str(bad))

    dup = tmp_path / "dup.yaml"
    dup.write_text("- id: G-1\n  flow: x\n  expected: pass\n- id: G-1\n  flow: y\n  expected: pass\n",
                   encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_scenarios(str(dup))
