"""End-to-end API: health, chat happy path, streaming stub, admin usage."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import auth_headers, make_tenant


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_chat_happy_path_openai_shape(client: TestClient) -> None:
    raw, _ = make_tenant(client)
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap",
                          "messages": [{"role": "user",
                                        "content": "vpn down for acme store 12"}]},
                    headers=auth_headers(raw, task="triage"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["usage"]["total_tokens"] > 0
    assert body["cache_hit"] is False


def test_chat_streaming_stub(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="streamer")
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap", "stream": True,
                          "messages": [{"role": "user", "content": "stream me"}]},
                    headers=auth_headers(raw))
    assert r.status_code == 200
    assert "data: [DONE]" in r.text
    assert "chat.completion.chunk" in r.text


def test_admin_usage_lists_rows(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="metered")
    client.post("/v1/chat/completions",
                json={"model": "triage-cheap",
                      "messages": [{"role": "user", "content": "hi"}]},
                headers=auth_headers(raw))
    r = client.get("/admin/usage", headers={"X-Admin-Key": "test-admin-key"})
    assert r.status_code == 200
    rows = r.json()
    assert any(row["tenant"] == "metered" for row in rows)


def test_xtask_drives_routing(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="router")
    r = client.post("/v1/chat/completions",
                    json={"model": "general-default",
                          "messages": [{"role": "user", "content": "disk full db"}]},
                    headers=auth_headers(raw, task="rca"))
    assert r.status_code == 200
    assert r.json()["model"] == "rca-strong"  # X-Task rca -> strong primary
