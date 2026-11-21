"""End-to-end demo: drift caught, no-retrain case, safe promotion, bad candidate rejected."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from backend.app.db import init_db, reset_database
from backend.app.main import app
from simulator.drift_simulator import SEVERE_KNOBS, SUBTLE_KNOBS


def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def main() -> int:
    init_db()
    reset_database()
    client = TestClient(app)

    banner("STAGE 0 | TRAIN BASELINE CHAMPION")
    baseline = client.post(
        "/api/v1/models/train-baseline", json={"seed": 42, "n_samples": 6000}
    ).json()
    print(f"champion version : {baseline['version']}")
    print(f"clean-holdout    : {baseline['metrics']}")

    stages = [
        ("STAGE 1 | CLEAN WINDOW (expect: no alert, monitor only)", "clean", {}, 1001),
        ("STAGE 2 | SUBTLE DRIFT below gate (expect: NO retrain)", "subtle", SUBTLE_KNOBS, 1002),
    ]
    for title, name, knobs, seed in stages:
        banner(title)
        window = client.post(
            "/api/v1/monitoring/windows",
            json={"name": name, "n_samples": 4000, "seed": seed, "knobs": knobs},
        ).json()
        evaluation = client.post(
            f"/api/v1/monitoring/windows/{window['id']}/evaluate", json={}
        ).json()
        print(
            f"window id={window['id']} alert={evaluation['alert']} "
            f"max_psi={evaluation['max_psi']:.4f} f1={evaluation['f1']:.4f}"
        )
        decision = client.post(
            "/api/v1/retraining/decide", json={"window_id": window["id"]}
        ).json()
        print(f"gate decision    : {decision['decision']}")
        for reason in decision["reasons"]:
            print(f"  - {reason}")
        if decision["decision"] != "monitor":
            print("FATAL: gate should not trigger retraining for this stage")
            return 1

    banner("STAGE 3 | SEVERE DRIFT (expect alert, investigation, retrain justified)")
    severe_window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "severe", "step": 3, "n_samples": 4000, "seed": 1003, "knobs": SEVERE_KNOBS},
    ).json()
    severe_eval = client.post(
        f"/api/v1/monitoring/windows/{severe_window['id']}/evaluate", json={}
    ).json()
    print(
        f"window id={severe_window['id']} alert={severe_eval['alert']} "
        f"drift_count={severe_eval['drift_count']} max_psi={severe_eval['max_psi']:.4f} "
        f"f1={severe_eval['f1']:.4f}"
    )

    rca = client.post(
        f"/api/v1/retraining/investigations/{severe_window['id']}", json={}
    ).json()
    print(f"incident         : {rca['incident_id']} confidence={rca['confidence']:.2f}")
    print(f"root cause       : {rca['root_cause']}")
    print(f"top observation  : {rca['observations'][0]}")
    print(f"rejected hyps    : {[h['statement'] for h in rca['rejected_hypotheses']]}")

    decision = client.post(
        "/api/v1/retraining/decide", json={"window_id": severe_window["id"]}
    ).json()
    gate_inputs = decision["gate_inputs"]
    print(f"gate decision    : {decision['decision']} projected_benefit={decision['projected_benefit']}")
    print(
        f"gate inputs      : meaningful_drift={gate_inputs['meaningful_drift']} "
        f"perf_degradation={gate_inputs['perf_degradation']} "
        f"high_risk_drift={gate_inputs['high_risk_drift']} "
        f"sufficient_samples={gate_inputs['sufficient_new_labeled_samples']}"
    )
    if decision["decision"] != "retrain":
        print("FATAL: severe window did not justify retraining")
        return 1

    banner("STAGE 4 | TRAIN CANDIDATE AND RUN DEPLOYMENT GATES")
    trained = client.post(
        "/api/v1/candidates/train",
        json={"source_window_id": severe_window["id"], "seed": 7},
    ).json()
    print(f"candidate        : {trained['version']} trained on window {severe_window['id']}")
    evaluated = client.post(
        "/api/v1/candidates/evaluate", json={"version": trained["version"]}
    ).json()
    print(f"verdict          : {evaluated['verdict']}")
    print(f"vs champion      : {evaluated['vs_champion']}")
    print(f"gates            : {evaluated['vs_thresholds']}")
    print(
        f"fairness ratio   : {evaluated['fairness_ratio']:.3f} "
        f"robustness drop: {evaluated['robustness_drop']:.3f}"
    )
    if evaluated["verdict"] != "pass":
        print(f"FATAL: candidate rejected unexpectedly: {evaluated['reasons']}")
        return 1

    banner("STAGE 5 | SHADOW REPLAY AND CANARY SLICES")
    shadow = client.post(
        "/api/v1/shadow/run",
        json={"version": trained["version"], "n_requests": 3000, "seed": 555},
    ).json()
    print(
        f"shadow disagreement rate : {shadow['disagreement_rate']:.4f} "
        f"over {shadow['n_requests']} requests"
    )
    canary = client.post(
        "/api/v1/shadow/canary",
        json={"version": trained["version"], "n_requests": 2500, "seed": 777},
    ).json()
    for segment, metrics in canary["slices"].items():
        print(
            f"canary slice {segment:9}: champ_f1={metrics['champion_f1']:.3f} "
            f"cand_f1={metrics['candidate_f1']:.3f} passed={metrics['passed']}"
        )

    banner("STAGE 6 | APPROVAL-GATED PROMOTION")
    promotion = client.post(
        "/api/v1/promotions", json={"candidate_version": trained["version"]}
    ).json()
    print(
        f"promotion {promotion['promotion_id']} state={promotion['state']} "
        f"risk={promotion['risk']['risk_level']}"
    )
    approved = client.post(
        f"/api/v1/promotions/{promotion['promotion_id']}/approve",
        json={"approver": "demo-operator", "comment": "gates passed"},
    ).json()
    print(f"approval result  : state={approved['state']}")
    registry = client.get("/api/v1/registry").json()
    champion = next(m for m in registry["models"] if m["status"] == "champion")
    print(f"current champion : {champion['version']} f1={champion['metrics'].get('f1')}")
    if champion["version"] != trained["version"] or approved["state"] != "COMPLETED":
        print("FATAL: champion was not safely updated after promotion")
        return 1

    banner("STAGE 7 | BAD CANDIDATE INJECTION (bad-model prevention)")
    bad = client.post(
        "/api/v1/candidates/train",
        json={"inject_bad": True, "bad_n_samples": 140, "bad_label_noise": 0.35},
    ).json()
    print(f"bad candidate    : {bad['version']} trained on {bad['n_samples']} noisy rows")
    bad_eval = client.post(
        "/api/v1/candidates/evaluate", json={"version": bad["version"]}
    ).json()
    print(f"verdict          : {bad_eval['verdict']}")
    for reason in bad_eval["reasons"]:
        print(f"  - {reason}")
    blocked = client.post("/api/v1/promotions", json={"candidate_version": bad["version"]})
    print(f"promotion attempt for rejected candidate -> HTTP {blocked.status_code} (blocked)")
    if bad_eval["verdict"] != "reject" or blocked.status_code == 200:
        print("FATAL: bad candidate was not prevented from promotion")
        return 1

    banner("FINAL KPIs")
    kpis = client.get("/api/v1/kpis").json()
    for key in (
        "windows_evaluated",
        "alerts_total",
        "false_alert_rate",
        "retraining_decisions_retrain",
        "retraining_decisions_monitor",
        "candidates_trained",
        "candidates_rejected_bad_model_prevention",
        "promotions_completed",
        "champion_version",
    ):
        print(f"{key:45}: {kpis[key]}")

    print("\nDEMO COMPLETE - all stages behaved as designed (exit 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
