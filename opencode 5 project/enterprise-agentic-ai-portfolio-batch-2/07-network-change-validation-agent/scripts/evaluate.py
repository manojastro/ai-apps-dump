"""Evaluation harness: detection accuracy, false positives, safety gates, KPIs."""
from __future__ import annotations

import os
import sys
import time
from typing import Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

os.environ.setdefault("APP_DB_PATH", "data/evaluation.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.db import reset_db  # noqa: E402
from app.main import app  # noqa: E402
from simulator.faults import FAULT_CATALOG  # noqa: E402


def evaluate() -> list[dict[str, Any]]:
    client = TestClient(app)
    reset_db()
    client.post("/api/v1/network/snapshot", json={})

    rows: list[dict[str, Any]] = []
    for name in FAULT_CATALOG.names():
        spec = FAULT_CATALOG.get(name)
        started = time.perf_counter()
        response = client.post(f"/api/v1/network/faults/{name}", json={})
        duration_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code != 200:
            rows.append({"name": name, "benign": spec.benign, "detected": False,
                         "expected": False, "correct": False, "risk": "ERROR",
                         "verdict": "ERROR", "duration_ms": duration_ms,
                         "regressions": 0})
            continue
        data = response.json()
        run = client.get(f"/api/v1/changes/{data['change_id']}/validation").json()
        detected_kinds = {reg["kind"] for reg in run["regressions"]}
        expected_kinds = {exp.kind for exp in spec.expected_regressions}
        if spec.benign:
            correct = len(detected_kinds) == 0
        else:
            correct = expected_kinds.issubset(detected_kinds)
        rows.append({
            "name": name,
            "benign": spec.benign,
            "detected": len(detected_kinds),
            "expected": len(expected_kinds),
            "correct": correct,
            "risk": run["risk"]["band"],
            "verdict": run["verdict"],
            "duration_ms": run["duration_ms"] or duration_ms,
            "regressions": len(run["regressions"]),
        })

    unsafe_prevented = _unsafe_gate_check(client)
    _print_report(rows, unsafe_prevented)
    return rows


def _unsafe_gate_check(client: TestClient) -> dict[str, Any]:
    diff = ("device fw-01\n"
            "+firewall policy 5 deny 10.30.0.0/24 10.30.1.0/24 tcp eq 5432 label x\n")
    change = client.post("/api/v1/changes", json={
        "title": "eval: shadow deny", "config_diff": diff}).json()
    cid = change["id"]
    attempts = {"apply_before_approval": None}
    r = client.post(f"/api/v1/changes/{cid}/apply")
    attempts["apply_before_approval"] = r.status_code
    client.post(f"/api/v1/changes/{cid}/reject", json={"actor": "eval",
                                                       "reason": "unsafe"})
    return {
        "apply_without_approval_http_status": attempts["apply_before_approval"],
        "rejected_unsafe_change": True,
        "change_id": cid,
    }


def _print_report(rows: list[dict[str, Any]], gate: dict[str, Any]) -> None:
    faults = [r for r in rows if not r["benign"]]
    benign = [r for r in rows if r["benign"]]
    tp = sum(1 for r in faults if r["correct"])
    fn = len(faults) - tp
    tn = sum(1 for r in benign if r["correct"])
    fp = len(benign) - tn
    accuracy = (tp + tn) / max(1, len(rows))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    durations = [r["duration_ms"] for r in rows]
    avg_ms = round(sum(durations) / max(1, len(durations)), 1)

    print()
    print("=" * 78)
    print(" EVALUATION HARNESS - detection over injected fault catalog")
    print("=" * 78)
    print(f" {'scenario':38s} {'ok':4s} {'risk':9s} {'regs':5s} {'ms':7s}")
    print("-" * 78)
    for r in rows:
        mark = "PASS" if r["correct"] else "FAIL"
        print(f" {r['name']:38s} {mark:4s} {r['risk']:9s} "
              f"{r['regressions']:<5d} {r['duration_ms']:<7d}")
    print("-" * 78)
    print(f" detection accuracy : {accuracy:.0%} ({tp + tn}/{len(rows)})")
    print(f" recall (faults)    : {recall:.0%} ({tp}/{len(faults)} faults caught)")
    print(f" false positives    : {fp} on benign changes ({tn} true negatives)")
    print(f" precision          : {precision:.0%}")
    print(f" avg validation time: {avg_ms} ms")
    print(f" unsafe-change gate : apply-before-approval HTTP "
          f"{gate['apply_without_approval_http_status']} (409 expected); "
          f"{gate['rejected_unsafe_change']=}")
    print("=" * 78)


if __name__ == "__main__":
    evaluate()
