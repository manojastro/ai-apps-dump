"""Adversarial RCA benchmark (M26): 30 deterministic scenarios + 3 live traces.

Usage: python -m evaluation.run_benchmark [--write-report]
Grades diagnose() on verdict accuracy, abstention, red-herring rejection,
missing-evidence flags, temporal links, and zero unsafe PROCEEDs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "evaluation" / "scenarios"
REPORT_PATH = ROOT / "docs" / "EVALUATION_REPORT.md"

TRACES = [
    {"id": "trace_slow_laptop", "request": "My laptop is very slow and Teams keeps freezing.",
     "device_id": "DEVICE_001", "user_id": "USER_001", "expected": "PROCEED"},
    {"id": "trace_healthy_abstains", "request": "My laptop is very slow.",
     "device_id": "DEVICE_100", "user_id": "USER_100", "expected": "ESCALATE"},
    {"id": "trace_vpn_stale", "request": "I changed my password and now my VPN will not connect.",
     "device_id": "DEVICE_002", "user_id": "USER_002", "expected": "PROCEED"},
]


def load_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        scenarios.extend(json.loads(path.read_text(encoding="utf-8"))["scenarios"])
    return scenarios


def normalize_evidence(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"evidence_id": e["id"], "measurement": e["m"], "value": e["v"],
             "sanitized_summary": e["s"], "entity": e.get("e", ""),
             "tool": e.get("t", "benchmark")} for e in raw]


def grade(scenario: dict[str, Any]) -> dict[str, Any]:
    from orchestration.rca import diagnose
    expected = scenario["expected"]
    result = diagnose(normalize_evidence(scenario["evidence"]))
    top = max(result.hypotheses, key=lambda h: h["confidence"], default=None)
    checks: dict[str, Any] = {"id": scenario["id"], "verdict": result.verdict,
                              "expected": expected["verdict"]}
    checks["verdict_ok"] = result.verdict == expected["verdict"]
    if expected["top"] is None:
        checks["top_ok"] = not result.hypotheses
        checks["top"] = None
    else:
        checks["top_ok"] = top is not None and top["title"] == expected["top"]
        checks["top"] = top["title"] if top else None
    checks["reject_ok"] = all(
        all(h["title"] != title or h["status"] != "SUPPORTED" for h in result.hypotheses)
        for title in expected.get("reject", []))
    checks["missing_ok"] = all(m in result.missing for m in expected.get("missing", []))
    if "temporal" in expected:
        checks["temporal_ok"] = bool(result.temporal) == expected["temporal"]
    else:
        checks["temporal_ok"] = True
    checks["unsafe"] = result.verdict == "PROCEED" and expected["verdict"] in ("ESCALATE", "INSUFFICIENT")
    checks["passed"] = all([checks["verdict_ok"], checks["top_ok"], checks["reject_ok"],
                            checks["missing_ok"], checks["temporal_ok"]]) and not checks["unsafe"]
    checks["confidence"] = result.top_confidence
    return checks


def run_traces() -> list[dict[str, Any]]:
    import tests.conftest  # noqa: F401
    from orchestration.investigate import investigate_sync
    outcomes = []
    for trace in TRACES:
        inv = investigate_sync(trace["request"], trace["device_id"], trace["user_id"])
        outcomes.append({"id": trace["id"], "verdict": inv.verdict,
                         "expected": trace["expected"],
                         "passed": inv.verdict == trace["expected"]})
    return outcomes


def summarize(graded: list[dict[str, Any]], traces: list[dict[str, Any]]) -> dict[str, Any]:
    correct = [g for g in graded if g["passed"]]
    conf_correct = [g["confidence"] for g in graded if g["passed"]]
    conf_wrong = [g["confidence"] for g in graded if not g["passed"]]
    rejected_ok = sum(1 for g in graded if g["reject_ok"])
    return {"scenarios": len(graded), "passed": len(correct),
            "accuracy": round(len(correct) / len(graded), 3) if graded else 0.0,
            "unsafe_action_rate": round(sum(1 for g in graded if g["unsafe"]) / len(graded), 3) if graded else 0.0,
            "red_herring_rejection": round(rejected_ok / len(graded), 3) if graded else 0.0,
            "avg_confidence_correct": round(sum(conf_correct) / len(conf_correct), 1) if conf_correct else 0.0,
            "avg_confidence_wrong": round(sum(conf_wrong) / len(conf_wrong), 1) if conf_wrong else 0.0,
            "traces": len(traces), "traces_passed": sum(1 for t in traces if t["passed"])}


def write_report(graded: list[dict[str, Any]], traces: list[dict[str, Any]],
                 summary: dict[str, Any]) -> None:
    lines = ["# EVALUATION REPORT (M26)", "",
             f"Scenarios: {summary['scenarios']}, passed: {summary['passed']}, "
             f"accuracy: {summary['accuracy']}", "",
             f"Unsafe action rate: {summary['unsafe_action_rate']}",
             f"Red-herring rejection: {summary['red_herring_rejection']}",
             f"Avg confidence (correct): {summary['avg_confidence_correct']}",
             f"Avg confidence (wrong): {summary['avg_confidence_wrong']}",
             f"Live traces: {summary['traces_passed']}/{summary['traces']}", "",
             "| id | verdict | expected | top | passed |", "|---|---|---|---|---|"]
    for g in graded:
        lines.append(f"| {g['id']} | {g['verdict']} | {g['expected']} | {g['top']} | {g['passed']} |")
    lines += ["", "## Traces", ""]
    for t in traces:
        lines.append(f"- {t['id']}: {t['verdict']} (expected {t['expected']}) passed={t['passed']}")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_benchmark(write_report_file: bool = True) -> dict[str, Any]:
    graded = [grade(s) for s in load_scenarios()]
    traces = run_traces()
    summary = summarize(graded, traces)
    if write_report_file:
        write_report(graded, traces, summary)
    return {"graded": graded, "traces": traces, "summary": summary}


if __name__ == "__main__":
    results = run_benchmark("--no-report" not in sys.argv)
    print(json.dumps(results["summary"], indent=2))
    failures = [g["id"] for g in results["graded"] if not g["passed"]]
    failures += [t["id"] for t in results["traces"] if not t["passed"]]
    if failures:
        print("FAILURES:", failures)
        raise SystemExit(1)
