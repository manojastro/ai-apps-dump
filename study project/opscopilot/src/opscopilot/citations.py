"""Deterministic citation validator: every [DOC §Section] must come from retrieved set."""

import re

from opscopilot.models import CitationCheck

_CITE_RE = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9\-]*)\s*§([^\]]+)\]")


def parse_citations(answer: str) -> list[tuple[str, str]]:
    """Extract (doc_id, section) pairs from `[DOCID §Section]` markers."""
    return [(m.group(1).strip(), m.group(2).strip()) for m in _CITE_RE.finditer(answer)]


def validate_citations(answer: str, retrieved_ids: set[str]) -> CitationCheck:
    """Check that every cited doc_id was actually retrieved.

    Returns CitationCheck with cited_ids (deduped, in order), valid, invalid.
    An answer with no citations yields empty lists (caller decides if that is OK).
    """
    seen: list[str] = []
    for doc_id, _section in parse_citations(answer):
        if doc_id not in seen:
            seen.append(doc_id)
    valid = [d for d in seen if d in retrieved_ids]
    invalid = [d for d in seen if d not in retrieved_ids]
    return CitationCheck(cited_ids=seen, valid=valid, invalid=invalid)
