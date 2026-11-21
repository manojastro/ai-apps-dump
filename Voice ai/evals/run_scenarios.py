"""Run all scenario evals. Usage: python -m evals.run_scenarios [--save-regressions]"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from evals.harness import Outcome, load_scenarios, run_scenario, save_regression


def run_all(save: bool = False) -> dict:
    specs = load_scenarios()
    outcomes: list[Outcome] = []
    for spec in specs:
        o = run_scenario(spec)
        outcomes.append(o)
        print(f"{'PASS' if o.success and o.trajectory_ok else 'FAIL'}  {o.id:45s} {o.failures if o.failures else ''}")
        if save and (not o.success or not o.trajectory_ok):
            print("   saved regression:", save_regression("scenario", spec, o))
    n = len(outcomes)
    per_wf: dict[str, list[dict]] = defaultdict(list)
    for o in outcomes:
        per_wf[o.workflow].append(o.stats)
    avg = {}
    for wf, rows in per_wf.items():
        k = len(rows)
        avg[wf] = {"scenarios": k, **{m: round(sum(r[m] for r in rows) / k, 1)
                                      for m in ("agent_runs", "steps", "tokens_in", "tokens_out", "latency_ms")}}
    return {
        "scenarios": n,
        "task_success_rate": round(sum(o.success for o in outcomes) / n, 4),
        "trajectory_accuracy": round(sum(o.trajectory_ok for o in outcomes) / n, 4),
        "failed": [o.id for o in outcomes if not (o.success and o.trajectory_ok)],
        "per_workflow_average": avg,
        "note": "MOCK mode: tokens are char/4 estimates and latency is the mock's own compute time, not model latency.",
    }


if __name__ == "__main__":
    res = run_all(save="--save-regressions" in sys.argv)
    print(json.dumps(res, indent=2))
    Path(__file__).with_name("results_scenarios.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    sys.exit(1 if res["failed"] else 0)
