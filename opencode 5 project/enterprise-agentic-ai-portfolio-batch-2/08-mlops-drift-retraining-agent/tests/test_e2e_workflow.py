"""Full end-to-end workflow mirroring the demo, asserted end to end."""
from __future__ import annotations

SEVERE = {
    "mean_shift": 1.4,
    "variance_shift": 1.8,
    "label_noise": 0.18,
    "missingness_rate": 0.06,
    "new_segment_share": 0.45,
}
SUBTLE = {"mean_shift": 0.12, "variance_shift": 1.05}


def test_e2e_full_lifecycle(client):
    baseline = client.post(
        "/api/v1/models/train-baseline", json={"seed": 42, "n_samples": 4000}
    ).json()
    champion_version = baseline["version"]

    clean_window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "e2e-clean", "step": 1, "n_samples": 3000, "seed": 10001},
    ).json()
    clean_eval = client.post(
        f"/api/v1/monitoring/windows/{clean_window['id']}/evaluate"
    ).json()
    assert clean_eval["alert"] is False
    assert (
        client.post("/api/v1/retraining/decide", json={"window_id": clean_window["id"]}).json()[
            "decision"
        ]
        == "monitor"
    )

    subtle_window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "e2e-subtle", "step": 2, "n_samples": 3000, "seed": 10002, "knobs": SUBTLE},
    ).json()
    client.post(f"/api/v1/monitoring/windows/{subtle_window['id']}/evaluate")
    subtle_decision = client.post(
        "/api/v1/retraining/decide", json={"window_id": subtle_window["id"]}
    ).json()
    assert subtle_decision["decision"] == "monitor"
    assert subtle_decision["gate_inputs"]["meaningful_drift"] is False

    severe_window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": "e2e-severe", "step": 3, "n_samples": 3500, "seed": 10003, "knobs": SEVERE},
    ).json()
    severe_eval = client.post(
        f"/api/v1/monitoring/windows/{severe_window['id']}/evaluate"
    ).json()
    assert severe_eval["alert"] is True
    assert severe_eval["max_psi"] > 0.25

    rca = client.post(f"/api/v1/retraining/investigations/{severe_window['id']}", json={}).json()
    assert rca["confidence"] >= 0.5
    assert any("covariate" in h["statement"].lower() for h in rca["hypotheses"])

    decision = client.post(
        "/api/v1/retraining/decide", json={"window_id": severe_window["id"]}
    ).json()
    assert decision["decision"] == "retrain"
    gate_inputs = decision["gate_inputs"]
    assert gate_inputs["meaningful_drift"] is True
    assert gate_inputs["sufficient_new_labeled_samples"] is True
    assert decision["projected_benefit"] >= 0.15

    trained = client.post(
        "/api/v1/candidates/train",
        json={"source_window_id": severe_window["id"], "seed": 81},
    ).json()
    evaluated = client.post(
        "/api/v1/candidates/evaluate", json={"version": trained["version"]}
    ).json()
    if evaluated["verdict"] != "pass":
        trained = client.post(
            "/api/v1/candidates/train",
            json={"source_window_id": severe_window["id"], "seed": 82},
        ).json()
        evaluated = client.post(
            "/api/v1/candidates/evaluate", json={"version": trained["version"]}
        ).json()
    assert evaluated["verdict"] == "pass", evaluated["reasons"]

    shadow = client.post("/api/v1/shadow/run", json={"version": trained["version"], "n_requests": 1500}).json()
    canary = client.post("/api/v1/shadow/canary", json={"version": trained["version"], "n_requests": 1200}).json()
    assert canary["passed"] is True
    risk = client.get(f"/api/v1/candidates/{trained['version']}/risk").json()
    assert risk["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    promotion = client.post(
        "/api/v1/promotions", json={"candidate_version": trained["version"]}
    ).json()
    assert promotion["state"] == "AWAITING_APPROVAL"
    approved = client.post(
        f"/api/v1/promotions/{promotion['promotion_id']}/approve",
        json={"approver": "e2e-bot"},
    ).json()
    assert approved["state"] == "COMPLETED"

    registry = client.get("/api/v1/registry").json()
    champion = next(m for m in registry["models"] if m["status"] == "champion")
    assert champion["version"] == trained["version"]
    assert champion["version"] != champion_version

    kpis = client.get("/api/v1/kpis").json()
    assert kpis["promotions_completed"] >= 1
    assert kpis["candidates_trained"] >= 2
    assert kpis["alerts_total"] >= 1
    audit = client.get("/api/v1/audit/tool-calls").json()["tool_calls"]
    assert audit


def test_e2e_bad_model_never_reaches_production(client):
    bad = client.post(
        "/api/v1/candidates/train",
        json={"inject_bad": True, "bad_n_samples": 130, "bad_label_noise": 0.4},
    ).json()
    evaluated = client.post(
        "/api/v1/candidates/evaluate", json={"version": bad["version"]}
    ).json()
    assert evaluated["verdict"] == "reject"
    promotion_attempt = client.post(
        "/api/v1/promotions", json={"candidate_version": bad["version"]}
    )
    assert promotion_attempt.status_code == 409
    registry = client.get("/api/v1/registry").json()
    statuses = {m["version"]: m["status"] for m in registry["models"]}
    assert statuses[bad["version"]] in ("challenger", "retired")
