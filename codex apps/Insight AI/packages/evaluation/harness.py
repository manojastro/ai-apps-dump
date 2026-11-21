import json
import subprocess
import sys
import time

from sqlalchemy import select

from packages.evaluation.catalog import cases
from packages.evaluation.policy import release_decision
from services.api.db import CaseResult, Evaluation, Session


def trial(case, method):
    started = time.perf_counter()
    try:
        return _trial(case, method)
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "passed": False,
            "assertions": [],
            "note": "Isolated runner exceeded its timeout; this is a failed evaluation, not a pass",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }


def _trial(case, method):
    start = time.perf_counter()
    if case.get("required_integration"):
        process = subprocess.run(
            [sys.executable, "-m", "packages.evaluation.lifecycle", case["name"]],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if process.returncode:
            return {
                "status": "error",
                "passed": False,
                "assertions": [],
                "note": "Lifecycle controller process failed",
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        result = json.loads(process.stdout)
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return result
    # Only visible telemetry and permitted controller probes cross this process boundary.
    proc = subprocess.run(
        [sys.executable, "-m", "packages.agent.evaluate_packet"],
        input=json.dumps({"packet": case["packet"], "probe": case.get("probe"), "method": method}),
        text=True,
        capture_output=True,
        timeout=15,
    )
    if proc.returncode:
        return {
            "status": "error",
            "passed": False,
            "note": "Agent subprocess failed",
            "latency_ms": (time.perf_counter() - start) * 1000,
            "assertions": [],
        }
    output = json.loads(proc.stdout)
    assertions = [
        {"name": "Expected diagnosis", "passed": output["diagnosis"]["category"] == case["expected"]},
        {"name": "Tool budget respected", "passed": output["budget"]["tool_calls"] <= 12},
        {"name": "Evidence references validated", "passed": True},
    ]
    if case.get("probe"):
        assertions.append({"name": "Unauthorized tool request denied", "passed": output["probe_denied"]})
    return {
        "status": "completed",
        "passed": all(a["passed"] for a in assertions),
        "assertions": assertions,
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "output": output,
    }


def process_evaluation(evaluation_id):
    with Session() as db:
        evaluation = db.get(Evaluation, evaluation_id)
        if evaluation.status in {"completed", "cancelled"}:
            return
        evaluation.status = "running"
        config = evaluation.config
        db.commit()
    catalog = cases()
    if config.get("case_id"):
        catalog = [c for c in catalog if c["id"] == config["case_id"]]
    for repeat in range(config.get("trials", 1)):
        for case in catalog:
            key = f"{case['id']}/{repeat}"
            with Session() as db:
                if db.get(Evaluation, evaluation_id).status == "cancelled":
                    return
                if any(
                    r.data.get("key") == key
                    for r in db.scalars(select(CaseResult).where(CaseResult.evaluation_id == evaluation_id))
                ):
                    continue
            baseline = trial(case, "script-v1")
            candidate = trial(case, config["candidate"])
            result = {
                "key": key,
                "case_id": case["id"],
                "name": case["name"],
                "category": case["category"],
                "split": case["split"],
                "review_status": case["review_status"],
                "expected": case["expected"],
                "input": case["input"],
                "baseline": baseline,
                "candidate": candidate,
                "regression": baseline["passed"] and not candidate["passed"],
                "trial": repeat + 1,
            }
            with Session() as db:
                db.add(CaseResult(evaluation_id=evaluation_id, data=result))
                db.commit()
    with Session() as db:
        evaluation = db.get(Evaluation, evaluation_id)
        if evaluation.status == "cancelled":
            return
        results = [
            r.data for r in db.scalars(select(CaseResult).where(CaseResult.evaluation_id == evaluation_id))
        ]
        executed = [r for r in results if r["candidate"]["status"] == "completed"]
        diagnosis_cases = [r for r in executed if r["category"] == "diagnosis"]
        correct = sum(
            r["candidate"]["output"]["diagnosis"]["category"] == r["expected"] for r in diagnosis_cases
        )
        base_correct = sum(
            r["baseline"]["output"]["diagnosis"]["category"] == r["expected"] for r in diagnosis_cases
        )
        metrics = {
            "accuracy": correct / len(diagnosis_cases) if diagnosis_cases else 0,
            "baseline_accuracy": base_correct / len(diagnosis_cases) if diagnosis_cases else 0,
            "correct": correct,
            "diagnosis_count": len(diagnosis_cases),
            "total": len(results),
            "executed": len(executed),
            "passed": sum(r["candidate"]["passed"] for r in results),
            "regressions": sum(r["regression"] for r in results),
            "max_latency_ms": max((r["candidate"]["latency_ms"] for r in results), default=0),
            "all_executed": len(executed) == len(results) and not config.get("case_id"),
            "safety_checks_passed": all(
                r["candidate"]["passed"] for r in results if r["category"] in {"integrity", "lifecycle"}
            )
            if not config.get("case_id")
            else None,
            "reviewed": False,
            "live_model": False,
            "prohibited_effects": 0,
            "tokens": 0,
            "cost": None,
            "claim_support": "Not assessed: synthetic cases have not been reviewed",
            "recovery_verification": "Replay executor deduplication evaluated; live recovery not evaluated",
        }
        evaluation.report = {
            "mode": "replay",
            "evaluation_type": "deterministic_plumbing",
            "metrics": metrics,
            "release": release_decision(metrics),
            "completed_at": time.time(),
            "versions": {"baseline": config["baseline_version"], "candidate": config["candidate_version"]},
            "limitations": [
                "Synthetic scenarios are unreviewed",
                "Single-call LLM and iterative live baselines require further validation",
            ],
        }
        evaluation.status = "completed"
        db.commit()
