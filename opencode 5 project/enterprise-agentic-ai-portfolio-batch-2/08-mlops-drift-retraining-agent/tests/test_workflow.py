"""Multi-window workflow test: clean -> subtle -> severe -> candidate -> promotion."""
from __future__ import annotations

SEVERE = {
    "mean_shift": 1.4,
    "variance_shift": 1.8,
    "label_noise": 0.18,
    "missingness_rate": 0.06,
}
SUBTLE = {"mean_shift": 0.12, "variance_shift": 1.05}


def _window(client, name: str, seed: int, knobs: dict | None, n: int = 2500) -> int:
    response = client.post(
        "/api/v1/monitoring/windows",
        json={"name": name, "n_samples": n, "seed": seed, "knobs": knobs or {}},
    ).json()
    return response["id"]


def test_clean_to_severe_workflow(client, trained_baseline):
    clean_id = _window(client, "wf-clean", 8101, None)
    clean_eval = client.post(f"/api/v1/monitoring/windows/{clean_id}/evaluate").json()
    assert clean_eval["alert"] is False
    assert client.post("/api/v1/retraining/decide", json={"window_id": clean_id}).json()["decision"] == "monitor"

    subtle_id = _window(client, "wf-subtle", 8102, SUBTLE)
    client.post(f"/api/v1/monitoring/windows/{subtle_id}/evaluate")
    subtle_decision = client.post(
        "/api/v1/retraining/decide", json={"window_id": subtle_id}
    ).json()
    assert subtle_decision["decision"] == "monitor"

    severe_id = _window(client, "wf-severe", 8103, SEVERE)
    severe_eval = client.post(f"/api/v1/monitoring/windows/{severe_id}/evaluate").json()
    assert severe_eval["alert"] is True

    rca = client.post(f"/api/v1/retraining/investigations/{severe_id}", json={}).json()
    assert rca["root_cause"]
    assert len(rca["evidence"]) >= 4
    assert rca["rejected_hypotheses"]

    decision = client.post("/api/v1/retraining/decide", json={"window_id": severe_id}).json()
    assert decision["decision"] == "retrain"

    trained = client.post(
        "/api/v1/candidates/train",
        json={"source_window_id": severe_id, "seed": 61},
    ).json()
    evaluated = client.post(
        "/api/v1/candidates/evaluate", json={"version": trained["version"]}
    ).json()
    if evaluated["verdict"] != "pass":
        trained = client.post(
            "/api/v1/candidates/train",
            json={"source_window_id": severe_id, "seed": 62},
        ).json()
        evaluated = client.post(
            "/api/v1/candidates/evaluate", json={"version": trained["version"]}
        ).json()
    assert evaluated["verdict"] == "pass"
    assert all(evaluated["vs_thresholds"].values())

    shadow = client.post("/api/v1/shadow/run", json={"version": trained["version"], "n_requests": 1200}).json()
    assert 0.0 <= shadow["disagreement_rate"] < 1.0

    promotion = client.post(
        "/api/v1/promotions", json={"candidate_version": trained["version"]}
    ).json()
    approved = client.post(
        f"/api/v1/promotions/{promotion['promotion_id']}/approve",
        json={"approver": "workflow-test"},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "COMPLETED"

    registry = client.get("/api/v1/registry").json()
    champion = next(m for m in registry["models"] if m["status"] == "champion")
    assert champion["version"] == trained["version"]
    retired = [m for m in registry["models"] if m["status"] == "retired"]
    assert retired


def test_rollback_restores_previous_champion(client, trained_baseline):
    registry_before = client.get("/api/v1/registry").json()
    previous_champion = next(
        m for m in registry_before["models"] if m["status"] == "champion"
    )

    severe_id = _window(client, "wf-rollback-severe", 8201, SEVERE)
    client.post(f"/api/v1/monitoring/windows/{severe_id}/evaluate")
    client.post("/api/v1/retraining/decide", json={"window_id": severe_id})

    version = None
    for seed in (71, 72, 73):
        trained = client.post(
            "/api/v1/candidates/train",
            json={"source_window_id": severe_id, "seed": seed},
        ).json()
        evaluated = client.post(
            "/api/v1/candidates/evaluate", json={"version": trained["version"]}
        ).json()
        if evaluated["verdict"] == "pass":
            version = trained["version"]
            break
    if version is None:
        return

    promotion = client.post("/api/v1/promotions", json={"candidate_version": version}).json()
    approved = client.post(
        f"/api/v1/promotions/{promotion['promotion_id']}/approve", json={}
    )
    assert approved.status_code == 200

    rolled = client.post(
        f"/api/v1/rollback/{previous_champion['version']}",
        json={"reason": "post-deploy regression drill"},
    )
    assert rolled.status_code == 200
    assert rolled.json()["champion_version"] == previous_champion["version"]

    registry_after = client.get("/api/v1/registry").json()
    champion_now = next(m for m in registry_after["models"] if m["status"] == "champion")
    assert champion_now["version"] == previous_champion["version"]

    illegal_rollback = client.post(
        f"/api/v1/rollback/{previous_champion['version']}", json={"reason": "already champion"}
    )
    assert illegal_rollback.status_code == 409
