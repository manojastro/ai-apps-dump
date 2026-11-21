"""CLI smoke tests: gate passes on baseline, fails on degraded run."""

import json

from typer.testing import CliRunner

from agentjudge.cli import app

runner = CliRunner()


def _report(tmp_path: object, **overrides: float) -> str:
    from pathlib import Path

    p = Path(str(tmp_path)) / "run.json"
    summary = {
        "hit_rate_at_5": 0.9,
        "faithfulness": 0.9,
        "refusal_accuracy": 1.0,
        "p95_latency_ms": 8.0,
        "recall_at_5": 0.9,
        "mrr": 0.9,
        "context_precision": 0.9,
        "context_recall": 0.9,
        "judge_correctness_mean": 4.5,
        "citation_validity": 1.0,
        "n": 50.0,
        "cost_usd": 0.0,
        "p50_latency_ms": 5.0,
    }
    summary.update(overrides)
    p.write_text(json.dumps({"summary": summary, "records": [], "worst_5": []}), encoding="utf-8")
    return str(p)


def test_gate_passes_and_fails(tmp_path: object) -> None:
    good = _report(tmp_path)
    base = good  # identical -> no regression
    r = runner.invoke(app, ["gate", good, "--baseline", base, "--config", "nonexistent.yaml"])
    assert r.exit_code == 0, r.output
    bad = _report(tmp_path, faithfulness=0.1)
    r2 = runner.invoke(app, ["gate", bad, "--baseline", base, "--config", "nonexistent.yaml"])
    assert r2.exit_code == 1, r2.output
