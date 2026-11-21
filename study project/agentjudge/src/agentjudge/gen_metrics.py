"""Mock generation metrics: keyword-overlap faithfulness (offline, no LLM).

Faithfulness = grounded claims / total claims in the answer.
A claim (sentence) is grounded if it shares at least one meaningful keyword
with the retrieved context. See docs/faithfulness_example.md for a worked example.
"""

import re
from typing import TypedDict

STOPWORDS = frozenset(
    "a an the and or but if then else when while of at by for with about into "
    "through during before after above below to from up down in out on off over "
    "under again further once here there all any both each few more most other "
    "some such no nor not only own same so than too very can will just should "
    "now is are was were be been being has have had do does did s t d ll m re ve "
    "it its this that these those as i you he she we they them his her our your "
    "their what which who whom how why where when whether also per via general "
    "follow best practices check".split()
)

_TOKEN = re.compile(r"[a-z0-9]+")


class ClaimDetail(TypedDict):
    claim: str
    grounded: bool


class FaithfulnessResult(TypedDict):
    score: float
    grounded: int
    total: int
    details: list[ClaimDetail]


def keywords(text: str) -> set[str]:
    """Lowercase alphanumeric tokens minus stopwords."""
    return {t for t in _TOKEN.findall(text.lower())} - STOPWORDS


def split_claims(answer: str) -> list[str]:
    """Naive claim splitter: one claim per sentence."""
    parts = re.split(r"[.!?]+", answer)
    return [p.strip() for p in parts if p.strip()]


def claim_grounded(claim: str, context_keywords: set[str]) -> bool:
    """A claim is grounded if it shares >=1 keyword with the context."""
    return len(keywords(claim) & context_keywords) > 0


def faithfulness(answer: str, contexts: list[str]) -> FaithfulnessResult:
    """Keyword-overlap faithfulness stub.

    Returns {"score": float, "grounded": int, "total": int, "details": [...]}.
    Empty answers score 0.0; refusal-style answers with no context score 1.0
    only when there is genuinely no context (nothing to be unfaithful to).
    """
    claims = split_claims(answer)
    if not claims:
        return {"score": 0.0, "grounded": 0, "total": 0, "details": []}
    ctx_kw: set[str] = set()
    for c in contexts:
        ctx_kw |= keywords(c)
    if not ctx_kw:
        # No context: answers that refuse are fine, others are ungrounded.
        lowered = answer.lower()
        if "can't answer" in lowered or "must refuse" in lowered or "no supporting" in lowered:
            return {"score": 1.0, "grounded": len(claims), "total": len(claims), "details": []}
        return {"score": 0.0, "grounded": 0, "total": len(claims), "details": []}
    details: list[ClaimDetail] = [
        {"claim": cl, "grounded": claim_grounded(cl, ctx_kw)} for cl in claims
    ]
    grounded = sum(1 for d in details if d["grounded"])
    return {
        "score": grounded / len(claims),
        "grounded": grounded,
        "total": len(claims),
        "details": details,
    }
