"""Routing policy, fallback on mock failure, per-tenant TTL cache."""

from __future__ import annotations

from fastapi.testclient import TestClient

from gateway import routing as routing_mod

from .conftest import auth_headers, make_tenant


def test_route_maps_tasks() -> None:
    policy = routing_mod.load_routing_policy("config/routing_policy.yaml")
    assert routing_mod.route("triage", policy)[0] == "triage-cheap"
    assert routing_mod.route("rca", policy)[0] == "rca-strong"
    assert routing_mod.route("unknown-task-xyz", policy)[0] == "general-default"


def test_fallback_on_mock_failure_is_logged(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="fallback")
    # Marker fails only the named primary -> gateway must use fallback.
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap",
                          "messages": [{"role": "user",
                                        "content": "please fail [FAIL:triage-cheap]"}]},
                    headers=auth_headers(raw, task="triage"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("fallback_used") is True
    conn = client.app.state.conn  # type: ignore[attr-defined]
    row = conn.execute(
        "SELECT * FROM audit_log WHERE event='provider_fallback'").fetchone()
    assert row is not None


def test_cache_hit_second_call(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="cached")
    payload = {"model": "triage-cheap",
               "messages": [{"role": "user", "content": "deterministic hello"}],
               "temperature": 0}
    first = client.post("/v1/chat/completions", json=payload,
                        headers=auth_headers(raw))
    second = client.post("/v1/chat/completions", json=payload,
                         headers=auth_headers(raw))
    assert first.json()["cache_hit"] is False
    assert second.json()["cache_hit"] is True


def test_cache_never_crosses_tenants(client: TestClient) -> None:
    raw_a, _ = make_tenant(client, name="tenant-a")
    raw_b, _ = make_tenant(client, name="tenant-b")
    payload = {"model": "triage-cheap",
               "messages": [{"role": "user", "content": "same prompt"}],
               "temperature": 0}
    client.post("/v1/chat/completions", json=payload, headers=auth_headers(raw_a))
    other = client.post("/v1/chat/completions", json=payload,
                        headers=auth_headers(raw_b))
    assert other.json()["cache_hit"] is False  # tenant B must not see A's entry


def test_cache_ttl_expiry() -> None:
    cache = routing_mod.ExactCache(ttl_s=10)
    cache.set("k", {"text": "v"}, now=1000.0)
    assert cache.get("k", now=1005.0) is not None
    assert cache.get("k", now=1011.0) is None
