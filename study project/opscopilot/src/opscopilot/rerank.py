"""Mock cross-encoder reranker stub + refusal helper (offline, deterministic)."""

from opscopilot.models import ScoredChunk


def mock_rerank(hits: list[ScoredChunk], enabled: bool = True) -> list[ScoredChunk]:
    """Stub for a cross-encoder reranker.

    Mock behaviour: keep the RRF order unchanged (scores untouched) so the
    pipeline, evals, and refusal logic can be exercised without a model.
    A real cross-encoder would re-score (query, chunk) pairs here.
    """
    _ = enabled  # flag exists so config can disable reranking; mock keeps order either way
    return list(hits)


def should_refuse(hits: list[ScoredChunk], threshold: float) -> bool:
    """Refuse when there is nothing retrieved or the best score is below threshold."""
    if not hits:
        return True
    return hits[0].score < threshold
