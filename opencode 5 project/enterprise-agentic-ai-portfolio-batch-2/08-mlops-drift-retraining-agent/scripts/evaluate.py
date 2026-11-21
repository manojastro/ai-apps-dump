"""Evaluation harness: detection accuracy, false alerts, TTD, gate correctness, prevention."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from backend.app.db import init_db, reset_database
from backend.app.main import app

SEVERE = {
    "mean_shift": 1.4,
    "variance_shift": 1.8,
    "label_noise": 0.18,
    "missingness_rate": 0.06,
}
MODERATE = {"mean_shift": 0.6, "label_noise": 0.05}


def evaluate() -> None:
    init_db()
    reset_database()
    client = TestClient(app)

    baseline = client.post(
        "/api/v1/models/train-baseline", json={"seed": 42, "n_samples": 6000}
    ).json()

    scenarios: list[tuple[str, dict, bool]] = [
        ("clean-a", {}, False),
        ("clean-b", {}, False),
        ("clean-c", {}, False),
        ("subtle-a", {"mean_shift": 0.12}, False),
        ("subtle-b", {"mean_shift": 0.15, "variance_shift": 1.05}, False),
        ("moderate-a", MODERATE, True),
        ("moderate-b", {"mean_shift": 0.8}, True),
        ("severe-a", SEVERE, True),
        ("severe-b", {**SEVERE, "new_segment_share": 0.4}, True),
    ]

    rows: list[dict] = []
    first_alert_step: int | None = None
    for index, (name, knobs, drift_expected) in enumerate(scenarios, start=1):
        window = client.post(
            "/api/v1/monitoring/windows",
            json={"name": name, "step": index, "n_samples": 3000, "seed": 5000 + index, "knobs": knobs},
        ).json()
        evaluation = client.post(
            f"/api/v1/monitoring/windows/{window['id']}/evaluate", json={}
        ).json()
        decision = client.post(
            "/api/v1/retraining/decide", json={"window_id": window["id"]}
        ).json()
        detected = evaluation["alert"]
        if detected and first_alert_step is None and drift_expected:
            first_alert_step = index
        rows.append(
            {
                "name": name,
                "drift_expected": drift_expected,
                "alert": detected,
                "max_psi": evaluation["max_psi"],
                "f1": evaluation["f1"],
                "decision": decision["decision"],
                "gate_correct": (decision["decision"] == "retrain") == drift_expected
                or (decision["decision"] == "monitor" and not drift_expected),
            }
        )

    detection_accuracy = sum(
        1 for r in rows if r["alert"] == r["drift_expected"]
    ) / len(rows)
    false_alerts = [r for r in rows if not r["drift_expected"] and r["alert"]]
    false_alert_rate = len(false_alerts) / max(1, sum(1 for r in rows if not r["drift_expected"]))
    gate_correctness = sum(1 for r in rows if r["gate_correct"]) / len(rows)

    print("\nDRIFT SCENARIO MATRIX")
    header = f"{'scenario':12} {'drift?':>7} {'alert':>6} {'max_psi':>9} {'f1':>7} {'gate':>9}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['name']:12} {str(r['drift_expected']):>7} {str(r['alert']):>6} "
            f"{r['max_psi']:>9.4f} {r['f1']:>7.4f} {r['decision']:>9}"
        )

    candidate = client.post(
        "/api/v1/candidates/train",
        json={
            "source_window_id": _find_window("severe-a"),
            "seed": 11,
        },
    ).json()
    evaluated = client.post(
        "/api/v1/candidates/evaluate", json={"version": candidate["version"]}
    ).json()
    improvement_delta = evaluated["vs_champion"]["f1_delta"]

    bad_prevented = 0
    for seed in (21, 22, 23):
        bad = client.post(
            "/api/v1/candidates/train",
            json={"inject_bad": True, "bad_n_samples": 120 + seed % 3 * 10, "bad_label_noise": 0.35},
        ).json()
        bad_eval = client.post(
            "/api/v1/candidates/evaluate", json={"version": bad["version"]}
        ).json()
        if bad_eval["verdict"] == "reject":
            bad_prevented += 1

    print("\nEVALUATION SUMMARY")
    print(f"baseline champion           : {baseline['version']}")
    print(f"drift detection accuracy    : {detection_accuracy:.2%} ({len(rows)} windows)")
    print(f"false-alert rate (clean/sub): {false_alert_rate:.2%}")
    print(f"time-to-detection           : window {first_alert_step} (first true alert)")
    print(f"retraining gate correctness : {gate_correctness:.2%}")
    print(f"candidate improvement delta : f1_delta={improvement_delta:+.4f}")
    print(f"bad-model prevention count  : {bad_prevented}/3 rejected before promotion")

    kpis = client.get("/api/v1/kpis").json()
    print(f"kpi snapshot persisted      : id={kpis['windows_evaluated']} windows evaluated")


def _find_window(name: str) -> int:
    from backend.app.db import SessionLocal
    from backend.app.models.entities import MonitoringWindow

    session = SessionLocal()
    try:
        row = (
            session.query(MonitoringWindow)
            .filter(MonitoringWindow.name == name)
            .order_by(MonitoringWindow.id.desc())
            .first()
        )
        if row is None:
            raise RuntimeError(f"window {name} not found")
        return int(row.id)
    finally:
        session.close()


if __name__ == "__main__":
    evaluate()
