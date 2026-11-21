"""Tests for mock hybrid retrieval (keyword + hash-embedding, no external DB)."""

from opscopilot.chunk import chunk_corpus
from opscopilot.models import Document
from opscopilot.retrieval import (
    cosine,
    hash_embedding,
    hybrid_search,
    keyword_ranking,
    vector_ranking,
)


def _docs() -> list[Document]:
    return [
        Document(
            doc_id="KB0001", doc_type="kedb", title="Outlook password MFA",
            service="outlook", status="active", updated_at="2025-07-10",
            content="# T\n\n## Symptoms\n\nOutlook asks password after MFA reset 0x80070005.\n",
            path="",
        ),
        Document(
            doc_id="KB0002", doc_type="kedb", title="VPN 809",
            service="vpn", status="active", updated_at="2025-06-20",
            content="# T\n\n## Symptoms\n\nVPN fails ERR_VPN_809 on home broadband NAT.\n",
            path="",
        ),
    ]


def test_keyword_finds_exact_code() -> None:
    chunks = chunk_corpus(_docs())
    ranked, _ = keyword_ranking("ERR_VPN_809", chunks)
    assert ranked, "exact code should match something"
    top = next(c for c in chunks if c.chunk_id == ranked[0])
    assert top.doc_id == "KB0002"


def test_vector_ranking_nonempty() -> None:
    chunks = chunk_corpus(_docs())
    ranked, scores = vector_ranking("password prompt outlook", chunks)
    assert ranked
    assert all(scores[c] > 0 for c in ranked)


def test_hybrid_search_service_filter() -> None:
    chunks = chunk_corpus(_docs())
    hits, debug = hybrid_search("VPN ERR_VPN_809 broadband", chunks, top_k=5, service="vpn")
    assert hits, "expected at least one vpn hit for a vpn-matching query"
    assert all(h.service == "vpn" for h in hits)
    assert debug.fused_ranking


def test_hash_embedding_deterministic_and_cosine() -> None:
    a = hash_embedding("hello world")
    b = hash_embedding("hello world")
    assert a == b
    assert abs(cosine(a, b) - 1.0) < 1e-9
    assert cosine(a, [0.0] * len(a)) == 0.0
