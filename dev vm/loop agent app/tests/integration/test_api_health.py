from fastapi.testclient import TestClient

from app.main import app


def test_health():
    c = TestClient(app)
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_metrics_and_policies():
    c = TestClient(app)
    assert c.get("/api/metrics").status_code == 200
    assert c.get("/api/policies").status_code == 200
    assert c.get("/api/pipelines").status_code == 200
