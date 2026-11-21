from app.main import app


def test_health_and_ready(client):
    h = client.get("/health")
    r = client.get("/ready")
    assert h.status_code == 200
    assert r.status_code == 200
    assert h.json()["status"] == "ok"
    assert r.json()["status"] == "ready"
    assert "SEBI-registered" in h.json()["disclaimer"]


def test_no_execution_endpoints():
    paths = []
    for route in app.routes:
        p = getattr(route, "path", "")
        paths.append(p.lower())
    forbidden = ("/execute", "/order", "/trade", "/broker", "/sip/start", "/redeem", "/transfer")
    for f in forbidden:
        assert all(f not in p for p in paths)


def test_api_disclaimer_on_snapshot(client):
    res = client.get("/api/v1/regulatory/snapshot")
    assert res.status_code == 200
    assert res.json()["meta"]["disclaimer"]
    assert res.json()["meta"]["executes_transactions"] is False
