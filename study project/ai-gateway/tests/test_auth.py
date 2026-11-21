"""Tenant keys: hash storage, wrong key, deleted key, disallowed model."""

from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from gateway import auth as auth_mod
from gateway import db as db_mod

from .conftest import auth_headers, make_tenant


def test_key_shown_once_and_stored_as_hash(client: TestClient) -> None:
    raw, data = make_tenant(client, name="opscopilot")
    assert raw.startswith("sk-gw-")
    conn = client.app.state.conn  # type: ignore[attr-defined]
    row = db_mod.find_tenant_by_name(conn, "opscopilot")
    assert row is not None
    assert row["key_hash"] != raw  # never store the raw key
    assert auth_mod.verify_key(raw, str(row["key_hash"]))


def test_generate_hash_verify_roundtrip() -> None:
    raw = auth_mod.generate_api_key()
    assert auth_mod.verify_key(raw, auth_mod.hash_key(raw))
    assert not auth_mod.verify_key(raw + "x", auth_mod.hash_key(raw))


def test_wrong_key_rejected(client: TestClient) -> None:
    make_tenant(client)
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap",
                          "messages": [{"role": "user", "content": "hi"}]},
                    headers=auth_headers("sk-gw-wrongkey"))
    assert r.status_code == 401


def test_deleted_key_rejected(client: TestClient) -> None:
    raw, _ = make_tenant(client, name="doomed")
    conn: sqlite3.Connection = client.app.state.conn  # type: ignore[attr-defined]
    db_mod.soft_delete_tenant(conn, "doomed")
    r = client.post("/v1/chat/completions",
                    json={"model": "triage-cheap",
                          "messages": [{"role": "user", "content": "hi"}]},
                    headers=auth_headers(raw))
    assert r.status_code == 401


def test_disallowed_model_blocked(client: TestClient) -> None:
    raw, _ = make_tenant(client, allowed_models=["triage-cheap"])
    r = client.post("/v1/chat/completions",
                    json={"model": "rca-strong",
                          "messages": [{"role": "user", "content": "hi"}]},
                    headers=auth_headers(raw, task="rca"))
    assert r.status_code == 403
    assert "model_not_allowed" in r.json()["error"]
