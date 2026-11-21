"""Shared fixtures: gateway app on a temp SQLite DB, admin + tenant helpers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gateway.app import create_app
from gateway.settings import Settings


@pytest.fixture()
def settings(tmp_path):  # type: ignore[no-untyped-def]
    return Settings(
        admin_api_key="test-admin-key",
        database_path=str(tmp_path / "test.db"),
    )


@pytest.fixture()
def app(settings):  # type: ignore[no-untyped-def]
    return create_app(settings)


@pytest.fixture()
def client(app):  # type: ignore[no-untyped-def]
    return TestClient(app)


def make_tenant(client: TestClient, name: str = "ticketsort",
                **over: object) -> tuple[str, dict[str, object]]:
    body = {
        "name": name,
        "monthly_budget_usd": 10.0,
        "rpm": 60,
        "tpm": 20000,
        "allowed_models": ["triage-cheap", "general-default", "rca-strong"],
        "guardrail_profile": "standard",
    }
    body.update(over)  # type: ignore[typeddict-item]
    r = client.post("/admin/tenants", json=body,
                    headers={"X-Admin-Key": "test-admin-key"})
    assert r.status_code == 200, r.text
    data = r.json()
    return str(data["api_key"]), data


def auth_headers(key: str, task: str = "triage") -> dict[str, str]:
    return {"Authorization": f"Bearer {key}", "X-Task": task}
