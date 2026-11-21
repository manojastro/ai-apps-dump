"""API tests with a tiny injected store (no corpus files needed)."""

from fastapi.testclient import TestClient

import opscopilot.app as appmod
from opscopilot.chunk import chunk_corpus
from opscopilot.models import Document


def _client() -> TestClient:
    docs = [
        Document(
            doc_id="KB0001", doc_type="kedb", title="Outlook password MFA",
            service="outlook", status="active", updated_at="2025-07-10",
            content="# Outlook password MFA\n\n## Workaround\n\nClear Credential Manager entries.\n",
            path="",
        ),
        Document(
            doc_id="KB0002", doc_type="kedb", title="VPN 809",
            service="vpn", status="active", updated_at="2025-06-20",
            content="# VPN 809\n\n## Symptoms\n\nVPN fails ERR_VPN_809 on home broadband.\n",
            path="",
        ),
    ]
    appmod.set_store(docs, chunk_corpus(docs), source="test")
    return TestClient(appmod.app)


def test_health() -> None:
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json()["chunks"] >= 2


def test_search_returns_hits_and_debug() -> None:
    r = _client().post("/v1/search", json={"question": "Outlook password MFA"})
    assert r.status_code == 200
    body = r.json()
    assert body["hits"]
    assert "keyword_ranking" in body["retrieval_debug"]


def test_ask_answer_has_citation_or_refusal() -> None:
    c = _client()
    r = c.post("/v1/ask", json={"question": "Outlook keeps asking password after MFA reset"})
    assert r.status_code == 200
    body = r.json()
    if body["refused"]:
        assert "No matching article" in body["answer"]
    else:
        assert "§" in body["answer"]
        assert body["citations"]


def test_ask_refuses_unknown_topic() -> None:
    c = _client()
    r = c.post("/v1/ask", json={"question": "How do I bake sourdough on Mars?"})
    assert r.status_code == 200
    assert r.json()["refused"] is True


def test_sources_roundtrip_and_404() -> None:
    c = _client()
    assert c.get("/v1/sources/KB0001").status_code == 200
    assert c.get("/v1/sources/NOPE").status_code == 404
