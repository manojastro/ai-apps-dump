"""Run prompt-injection attacks. Usage: python -m evals.run_injection [--save-regressions]

Each attack is run against three simulated models:
  normal    a model that ignores the injected text (best case)
  gullible  a model that obeys any patient text (worst case; tests the system-level defences)
  stubborn  gullible, and repeats a bad answer even after being corrected
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from evals.harness import load_attacks, run_injection, save_regression

MODES = ("normal", "gullible", "stubborn")


def run_all(save: bool = False) -> dict:
    attacks = load_attacks()
    results: dict[str, dict] = {}
    all_failed = []
    for mode in MODES:
        passed, failed = 0, []
        denied_total = 0
        for atk in attacks:
            o = run_injection(atk, mode)
            denied_total += len(o.stats.get("denied_attempts", []))
            if o.success:
                passed += 1
            else:
                failed.append({"id": atk["id"], "failures": o.failures})
                if save:
                    save_regression("injection", {**atk, "mock_mode": mode}, o)
            print(f"{'PASS' if o.success else 'FAIL'}  [{mode:8s}] {atk['id']:34s} denied={o.stats.get('denied_attempts')} "
                  f"{o.failures if o.failures else ''}")
        results[mode] = {"attacks": len(attacks), "passed": passed, "pass_rate": round(passed / len(attacks), 4),
                         "failed": failed, "denied_attempts_total": denied_total}
        all_failed += failed
    return {"attacks": len(attacks), "modes": results}


if __name__ == "__main__":
    res = run_all(save="--save-regressions" in sys.argv)
    print(json.dumps(res, indent=2))
    Path(__file__).with_name("results_injection.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    sys.exit(1 if any(m["failed"] for m in res["modes"].values()) else 0)
