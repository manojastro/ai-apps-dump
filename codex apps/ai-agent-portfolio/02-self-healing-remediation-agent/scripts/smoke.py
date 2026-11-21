from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import PROJECT_ROOT, Settings


settings = Settings(
    database_url="sqlite://",
    policy_path=str(PROJECT_ROOT / "config" / "policies.yaml"),
    seed_on_start=True,
)
headers = {"Authorization": "Bearer demo-operator-token", "X-CSRF-Token": "demo-csrf-token"}
with TestClient(create_app(settings, seed=True)) as client:
    incidents = client.get("/api/incidents", headers=headers).json()
    assert len(incidents) == 7
    pending = next(item for item in incidents if item["status"] == "PENDING_APPROVAL")
    approved = client.post(
        f"/api/incidents/{pending['id']}/approval",
        headers=headers,
        json={"decision": "APPROVED", "comment": "clean smoke approval"},
    )
    assert approved.status_code == 200 and approved.json()["status"] == "RESOLVED"
    rolled_back = client.post(
        "/api/incidents", headers=headers,
        json={"scenario": "crashloop", "force_verification_failure": True},
    )
    assert rolled_back.status_code == 201 and rolled_back.json()["status"] == "ROLLED_BACK"
    dashboard = client.get("/api/dashboard", headers=headers).json()
    assert dashboard["total_incidents"] == 8
    assert client.get("/metrics").status_code == 200
    print({"seeded": 7, "approved_status": "RESOLVED", "forced_failure_status": "ROLLED_BACK",
           "audit_events": len(client.get("/api/audit", headers=headers).json())})

