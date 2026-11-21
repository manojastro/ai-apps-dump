"""Mock answer composer: extractive, cited, with refusal / conflict / retired handling."""

from opscopilot.citations import validate_citations
from opscopilot.models import Citation, Confidence, ScoredChunk
from opscopilot.rerank import mock_rerank, should_refuse


def _first_sentences(text: str, limit: int = 2) -> str:
    body = " ".join(text.split())
    # strip the "Title > Section" prefix line for the extract
    if "\n" in text:
        parts = text.split("\n", 1)
        if ">" in parts[0]:
            body = " ".join(parts[1].split())
    sentences: list[str] = []
    current = ""
    for ch in body:
        current += ch
        if ch in ".!?" and len(current.strip()) > 20:
            sentences.append(current.strip())
            current = ""
            if len(sentences) >= limit:
                break
    if current.strip() and len(sentences) < limit:
        sentences.append(current.strip())
    out = " ".join(sentences).strip()
    return out[:600] if out else body[:600]


def compose_answer(
    question: str,
    hits: list[ScoredChunk],
    refuse_threshold: float = 0.029,
    rerank_enabled: bool = True,
) -> tuple[str, list[Citation], Confidence, bool]:
    """Build a mock grounded answer from retrieval hits.

    Returns (answer_text, citations, confidence, refused).
    - Refuses when hits are empty or best score < threshold.
    - Prefers active chunks over retired ones.
    - Flags close-call conflicts between two different active docs.
    """
    ranked = mock_rerank(hits, enabled=rerank_enabled)
    if should_refuse(ranked, refuse_threshold):
        answer = (
            "No matching article found in the Acme Retail Ltd knowledge base "
            f"for: '{question.strip()}'. Try rephrasing or contact the service desk."
        )
        return answer, [], "LOW", True

    active = [h for h in ranked if h.status == "active"]
    usable = active if active else ranked
    retired_only = not active

    primary = usable[0]
    citations: list[Citation] = [Citation(doc_id=primary.doc_id, section=primary.section)]

    # Conflict / near-dup heuristic: top-2 from different active docs with very
    # close fused scores (relative gap <= 3%). Wording stays neutral because the
    # pair may be conflicting guidance OR near-duplicate articles.
    conflict_note = ""
    if len(usable) >= 2:
        second = usable[1]
        if second.doc_id != primary.doc_id and second.status == "active":
            gap = abs(primary.score - second.score)
            close = primary.score > 0 and (gap / primary.score) <= 0.03
            if close:
                citations.append(Citation(doc_id=second.doc_id, section=second.section))
                conflict_note = (
                    f" Note: closely related guidance also exists in "
                    f"[{second.doc_id} §{second.section}] — compare both before acting."
                )

    extract = _first_sentences(
        next((h for h in usable if h.chunk_id == primary.chunk_id), primary).snippet
        or primary.doc_id
    )
    # snippet is truncated; prefer fuller guidance line when available
    answer = (
        f"Based on [{primary.doc_id} §{primary.section}]: {extract}"
        f"{conflict_note} "
        f"See [{primary.doc_id} §{primary.section}] for the full steps."
    )
    if retired_only:
        answer = (
            f"Only a retired article matches [{primary.doc_id} §{primary.section}]: "
            f"{extract} Verify with the service owner before acting."
        )
        # re-validate citations below still holds
    if len(citations) > 1:
        confidence: Confidence = "MEDIUM"
    elif retired_only:
        confidence = "MEDIUM"
    elif primary.score >= refuse_threshold * 1.1:
        # Both-lists agreement with margin (RRF max is 2/(k+1) ≈ 0.0328).
        # Score-margin heuristic only — NOT calibrated probability (see README limits).
        confidence = "HIGH"
    else:
        confidence = "MEDIUM"

    # Self-check: every citation must be in the retrieved set (deterministic guard).
    retrieved_ids = {h.doc_id for h in ranked}
    check = validate_citations(answer, retrieved_ids)
    if not check.is_valid:
        # Strip hallucinated markers (should not happen with this composer) and lower confidence.
        for bad in check.invalid:
            answer = answer.replace(f"[{bad} ", "[UNKNOWN ")
        confidence = "LOW"

    return answer, citations, confidence, False
