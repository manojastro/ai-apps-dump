"""M6 tests: SLA lookup + SSE stream."""

from datetime import timedelta

from fastapi.testclient import TestClient

from ticketsort.api.main import create_app
from ticketsort.config import Settings
from ticketsort.domain.models import Priority
from ticketsort.domain.sla import sla_for


def test_sla_values() -> None:
    assert sla_for(Priority.P1) == timedelta(hours=1)
    assert sla_for(Priority.P5) == timedelta(hours=48)


def test_reply_stream() -> None:
    client = TestClient(create_app(Settings(llm_provider="mock")))
    r = client.post(
        "/v1/reply/stream",
        json={
            "ticket_id": "T-0001",
            "short_description": "VPN not connecting",
            "description": "All 15 users cannot connect to VPN. Work stopped.",
            "caller_department": "Sales",
            "channel": "portal",
        },
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    joined = r.text.replace("\n", " ")
    for word in ("Target", "first", "response", "Acme"):
        assert word in joined
    assert "data: [DONE]" in r.text
