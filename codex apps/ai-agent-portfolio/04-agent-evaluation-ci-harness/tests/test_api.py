from fastapi.testclient import TestClient

import evalharness.api as api
from evalharness.store import Database


def test_api_seed_run_baseline_compare_and_gate(tmp_path):
    api.database = Database(f"sqlite:///{tmp_path / 'api.db'}")
    with TestClient(api.app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").json()["status"] == "ready"
        datasets = client.get("/api/datasets").json()
        assert datasets[0]["case_count"] == 200
        good = client.post("/api/runs", json={"mode": "good", "limit": 12}).json()
        assert good["aggregate"]["task_success"] == 1
        assert client.post(f"/api/runs/{good['id']}/baseline").status_code == 200
        bad = client.post("/api/runs", json={"mode": "bad", "limit": 12}).json()
        comparison = client.get(f"/api/compare?candidate_id={bad['id']}").json()
        assert comparison["regressions"]["task_success"] == 1
        gate = client.post("/api/gates", json={
            "candidate_id": bad["id"],
            "config": {"absolute_thresholds": {"task_success": .9}},
        }).json()
        assert gate["passed"] is False
        detail = client.get(f"/api/runs/{bad['id']}").json()
        assert detail["samples"][0]["response"]["tool_calls"]

