from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def settings(tmp_path, **kwargs):
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        checkpoint_url=str(tmp_path / "checkpoints.db"),
        **kwargs,
    )


def test_create_run_inspect_evidence_attempts_and_artifact(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as client:
        response = client.post("/api/v1/incidents", json={"demo_force_first_fix_fail": True})
        assert response.status_code == 201
        assert response.headers["x-correlation-id"]
        case_id = response.json()["id"]
        assert client.post(f"/api/v1/incidents/{case_id}/run?wait=true").status_code == 200
        case = client.get(f"/api/v1/incidents/{case_id}").json()
        assert case["status"] == "COMPLETED"
        assert case["artifact"]["post_validation"] == "PASS"
        assert len(client.get(f"/api/v1/incidents/{case_id}/evidence").json()) == 5
        assert len(client.get(f"/api/v1/incidents/{case_id}/validations").json()) == 20
        assert client.post(f"/api/v1/incidents/{case_id}/run").status_code == 409
        assert client.get("/ready").status_code == 200


def test_approval_persists_and_repeated_decision_is_rejected(tmp_path):
    config = settings(tmp_path)
    with TestClient(create_app(config)) as client:
        case_id = client.post("/api/v1/incidents", json={"scenario": "dependency_failure"}).json()[
            "id"
        ]
        client.post(f"/api/v1/incidents/{case_id}/run?wait=true")
        assert client.get(f"/api/v1/incidents/{case_id}").json()["status"] == "WAITING_FOR_HUMAN"
    with TestClient(create_app(config)) as restarted:
        decision = {"actor": "reviewer", "comment": "Reviewed bounded retries"}
        response = restarted.post(f"/api/v1/incidents/{case_id}/approve?wait=true", json=decision)
        assert response.status_code == 200
        assert restarted.get(f"/api/v1/incidents/{case_id}").json()["status"] == "COMPLETED"
        assert (
            restarted.post(f"/api/v1/incidents/{case_id}/approve", json=decision).status_code == 409
        )


def test_api_rejects_unknown_inputs_and_requires_configured_token(tmp_path):
    with TestClient(create_app(settings(tmp_path, api_token="test-token"))) as client:
        assert client.get("/api/v1/incidents").status_code == 401
        headers = {"Authorization": "Bearer test-token"}
        assert (
            client.post(
                "/api/v1/incidents",
                headers=headers,
                json={"scenario": "../secret", "max_attempts": 999},
            ).status_code
            == 422
        )
        missing = client.get("/api/v1/incidents/missing", headers=headers)
        assert missing.status_code == 404
        assert missing.json()["error"]["correlation_id"]
