import importlib

from fastapi.testclient import TestClient

from app.orchestrator.engine import Orchestrator
from app.orchestrator.runner import Simulation


def test_api_ingests_events_and_exposes_workflows(tmp_path, monkeypatch):
    monkeypatch.setenv("EIR_DB_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("EIR_API_KEY", "k")
    import app.main as main
    importlib.reload(main)
    with TestClient(main.app) as c:
        assert c.get("/health").json()["ok"] is True
        assert c.post("/events", json={"type": "STOCK_LOW", "payload": {}}).status_code == 401
        h = {"X-API-Key": "k"}
        assert c.post("/events", json={"type": "NOPE"}, headers=h).status_code == 422
        r = c.post("/events", json={"type": "STOCK_LOW", "payload": {}}, headers=h)
        assert r.status_code == 200 and r.json()["event_id"] >= 1
        from app.data.seed import SeedConfig, seed
        seed(SeedConfig(patients=10, practitioners=2, weeks=1, appointments=10, checkins=5, supply_items=5))
        Simulation(Orchestrator(), approver=None).pump()
        wfs = c.get("/api/workflows", headers=h).json()
        assert wfs and wfs[0]["type"] == "RESTOCK"
        assert c.get(f"/api/workflows/{wfs[0]['id']}", headers=h).json()["history"]
        assert c.get("/api/workflows/nope", headers=h).status_code == 404


def test_console_module_exposes_asgi_app(tmp_path, monkeypatch):
    monkeypatch.setenv("EIR_DB_URL", f"sqlite:///{tmp_path / 'console.db'}")
    import app.console.app as console
    asgi = console.app  # what `uvicorn app.console.app:app` loads
    assert TestClient(asgi).get("/health").json() == {"ok": True}


def test_worker_module_imports():
    import app.worker as w
    assert callable(w.main)
