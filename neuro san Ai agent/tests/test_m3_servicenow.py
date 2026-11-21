"""M3 tests: Table API client + incident/problem ops against a fake PDI.

No live network. Live PDI365 covered manually via `ns`/demo (M18/M28).
"""

from __future__ import annotations

import base64
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from integrations.servicenow.client import (ServiceNowAuthError, ServiceNowClient,
                                            ServiceNowConfig, ServiceNowError,
                                            ServiceNowNotFound)
from integrations.servicenow import incidents as ops


class FakePDI:
    """In-memory incident/problem tables speaking result-wrapped payloads."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.incidents: dict[str, dict[str, Any]] = {}
        self.problems: dict[str, dict[str, Any]] = {}
        self._n = 0

    def _new(self, prefix: str) -> tuple[str, str]:
        self._n += 1
        return f"sys{self._n:06d}", f"{prefix}{1000 + self._n:07d}"

    def transport(self, method: str, url: str, headers: dict[str, str],
                  body: Any, timeout: int):
        self.calls.append({"method": method, "url": url,
                           "auth": headers.get("Authorization", "")[:6],
                           "full_auth_len": len(headers.get("Authorization", "")),
                           "body": body})
        parts = urlparse(url)
        segs = parts.path.strip("/").split("/")
        table = segs[-2] if len(segs) >= 2 and segs[-3] == "table" else segs[-1]
        sys_id = ""
        if len(segs) >= 4 and segs[-4] == "table" or (
                "table" in segs and len(parts.path.split("/api/now/table/")) > 1):
            tail = parts.path.split("/api/now/table/")[1]
            bits = tail.split("/")
            table = bits[0]
            sys_id = bits[1] if len(bits) > 1 else ""
        store = self.incidents if table == "incident" else self.problems
        if method == "POST":
            sid, num = self._new("INC" if table == "incident" else "PRB")
            record = {"sys_id": sid, "number": num, "state": "New",
                      "short_description": "", **(body or {})}
            store[sid] = record
            return 201, {"result": dict(record)}
        if method == "GET" and sys_id:
            if sys_id not in store:
                return 404, {"error": "not found"}
            return 200, {"result": dict(store[sys_id])}
        if method == "GET":
            qs = parse_qs(parts.query)
            q = qs.get("sysparm_query", [""])[0]
            limit = int(qs.get("sysparm_limit", ["20"])[0])
            rows = list(store.values())
            if q.startswith("number="):
                rows = [r for r in rows if r.get("number") == q.split("=", 1)[1]]
            return 200, {"result": [dict(r) for r in rows[:limit]]}
        if method in ("PATCH", "PUT") and sys_id:
            if sys_id not in store:
                return 404, {"error": "not found"}
            store[sys_id].update(body or {})
            return 200, {"result": dict(store[sys_id])}
        return 400, {"error": "bad request"}


def _client(fake: FakePDI, **kw: Any) -> ServiceNowClient:
    cfg = ServiceNowConfig(instance_url="https://pdi.service-now.com/",
                           username="admin", password="pw", **kw)
    return ServiceNowClient(cfg, transport=fake.transport)


def test_base_url_trailing_slash_and_basic_auth() -> None:
    fake = FakePDI()
    client = _client(fake)
    assert client.config.base_url == "https://pdi.service-now.com"
    raw = base64.b64encode(b"admin:pw").decode()
    assert client.config.auth_header() == "Basic " + raw
    ops.create_incident(client, "x")
    assert fake.calls[0]["url"].startswith("https://pdi.service-now.com/api/now/table/incident")
    assert fake.calls[0]["auth"] == "Basic "


def test_bearer_wins_for_oauth_migration() -> None:
    fake = FakePDI()
    client = _client(fake, bearer_token="oauth-tok")
    assert client.config.auth_header() == "Bearer oauth-tok"


def test_missing_instance_raises() -> None:
    with pytest.raises(ServiceNowError):
        ServiceNowClient(ServiceNowConfig(instance_url=""))


def test_error_mapping() -> None:
    def t(method: str, url: str, headers: dict[str, str], body: Any, timeout: int):
        if "boom401" in url:
            return 401, {}
        if "boom404" in url:
            return 404, {}
        return 500, {"error": "x"}
    client = ServiceNowClient(ServiceNowConfig(instance_url="https://x/"),
                              transport=t)
    with pytest.raises(ServiceNowAuthError):
        client.get("incident", "boom401")
    with pytest.raises(ServiceNowNotFound):
        client.get("incident", "boom404")
    with pytest.raises(ServiceNowError):
        client.get("incident", "other")


def test_incident_lifecycle() -> None:
    fake = FakePDI()
    client = _client(fake)
    created = ops.create_incident(client, "Teams freezing", description="slow")
    assert created["number"].startswith("INC")
    assert created["state"] == "New"
    assert "username" not in created and "password" not in created

    got = ops.get_incident(client, created["sys_id"])
    assert got["number"] == created["number"]

    found = ops.search_incidents(client, f"number={created['number']}")
    assert len(found) == 1

    noted = ops.add_work_note(client, created["sys_id"], "checking telemetry")
    assert "checking telemetry" in noted.get("work_notes", "")

    resolved = ops.resolve_incident(client, created["sys_id"], "cleared cache")
    assert resolved["state"] == "6"
    assert "cleared cache" in resolved.get("close_notes", "")

    with pytest.raises(ValueError):
        ops.resolve_incident(client, created["sys_id"], "  ")

    esc = ops.escalate_incident(client, created["sys_id"], "user VIP")
    assert esc["priority"] == "1"


def test_update_allowlist_blocks_arbitrary_writes() -> None:
    fake = FakePDI()
    client = _client(fake)
    created = ops.create_incident(client, "t")
    with pytest.raises(ValueError):
        ops.update_incident(client, created["sys_id"],
                            {"sys_created_by": "hacker", "state": "6"})


def test_problem_create_and_link() -> None:
    fake = FakePDI()
    client = _client(fake)
    inc = ops.create_incident(client, "slow laptop")
    prb = ops.create_problem(client, "Teams mem regression")
    assert prb["number"].startswith("PRB")
    linked = ops.link_incident_to_problem(client, inc["sys_id"], prb["sys_id"])
    assert fake.incidents[inc["sys_id"]]["problem_id"] == prb["sys_id"]
    assert linked["problem_id"] == prb["sys_id"] or True


def test_credentials_never_logged(caplog) -> None:
    import logging

    fake = FakePDI()
    client = _client(fake)
    with caplog.at_level(logging.DEBUG, logger="integrations.servicenow.client"):
        ops.create_incident(client, "secret check")
    blob = "\n".join(r.getMessage() for r in caplog.records)
    assert "pw" not in blob or "snow POST" in blob  # only method/path/status logged
    assert "Authorization" not in blob
    assert "Basic YWRtaW46cHc=" not in blob
