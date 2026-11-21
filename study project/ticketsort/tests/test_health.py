"""M1 health tests — uses FastAPI TestClient, no server needed."""

from fastapi.testclient import TestClient

from ticketsort.api.main import create_app
from ticketsort.config import Settings


def make_client(**overrides):  # type: ignore[no-untyped-def]
    settings = Settings(
        llm_provider=overrides.get("llm_provider", "openai"),
        prompt_version=overrides.get("prompt_version", "v1"),
    )
    return TestClient(create_app(settings))


def test_health_ok() -> None:
    client = make_client()
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok", "llm_provider": "openai", "prompt_version": "v1"}


def test_health_never_leaks_key() -> None:
    client = make_client()
    body = client.get("/health").json()
    dumped = str(body).lower()
    assert "sk-" not in dumped
    assert "key" not in dumped


def test_health_request_id_header() -> None:
    client = make_client()
    r = client.get("/health")
    assert "x-request-id" in {k.lower() for k in r.headers}
