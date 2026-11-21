"""Metering: cost math, soft/hard budgets, /v1/usage."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gateway import metering as metering_mod

from .conftest import auth_headers, make_tenant


def _prices() -> dict[str, dict[str, float]]:
    return {"m": {"input_per_1k": 1.0, "output_per_1k": 2.0}}


def test_estimate_cost_math() -> None:
    assert metering_mod.estimate_cost("m", 1000, 1000, _prices()) == 3.0
    assert metering_mod.estimate_cost("unknown", 999, 999, _prices()) == 0.0


def test_budget_thresholds() -> None:
    assert metering_mod.check_budget(10.0, 100.0)[0] == "ok"
    assert metering_mod.check_budget(80.0, 100.0)[0] == "soft"  # 80% alert
    assert metering_mod.check_budget(99.99, 100.0)[0] == "soft"
    assert metering_mod.check_budget(100.0, 100.0)[0] == "hard"  # 100% stop
    assert metering_mod.check_budget(150.0, 100.0)[0] == "hard"


def test_usage_endpoint_tracks_spend(client: TestClient) -> None:
    raw, _ = make_tenant(client, monthly_budget_usd=50.0)
    before = client.get("/v1/usage",
                        headers={"Authorization": f"Bearer {raw}"}).json()
    assert before["month_spend_usd"] == 0.0
    assert before["remaining_usd"] == 50.0
    client.post("/v1/chat/completions",
                json={"model": "triage-cheap",
                      "messages": [{"role": "user", "content": "hello world"}]},
                headers=auth_headers(raw))
    after = client.get("/v1/usage",
                       headers={"Authorization": f"Bearer {raw}"}).json()
    assert after["month_spend_usd"] > 0.0
    assert after["remaining_usd"] < 50.0


def test_hard_budget_stops_calls(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="broke", monthly_budget_usd=0.000001)
    client.post("/v1/chat/completions",
                json={"model": "triage-cheap",
                      "messages": [{"role": "user", "content": "spend it all"}]},
                headers=auth_headers(raw))
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap",
                          "messages": [{"role": "user", "content": "one more"}]},
                    headers=auth_headers(raw))
    assert r.status_code == 402
    assert r.json()["error"] == "budget_exceeded"
