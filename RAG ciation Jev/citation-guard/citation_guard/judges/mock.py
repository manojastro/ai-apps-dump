"""MockJudge: deterministic and offline. For tests and MOCK runs only.

Its numbers are a crude word-overlap + RFC 2119 keyword heuristic. They say nothing about
Jev or any real model. Every result it returns is marked mock=True, judge="mock".
"""

from __future__ import annotations

import re
import time

from .base import JudgeResult, normalise_probs

MOCK_MODEL = "mock-heuristic-v1"

STOP = set(
    "a an the of to in on for and or is are be by with as that this it its which when "
    "than then if any each must may should not shall can will only from at into".split()
)
# RFC 2119 keyword -> strength bucket
KEYWORDS = [
    ("MUST NOT", "prohibited"), ("SHALL NOT", "prohibited"), ("SHOULD NOT", "discouraged"),
    ("NOT RECOMMENDED", "discouraged"), ("MUST", "required"), ("REQUIRED", "required"),
    ("SHALL", "required"), ("SHOULD", "recommended"), ("RECOMMENDED", "recommended"),
    ("MAY", "optional"), ("OPTIONAL", "optional"),
]


def _keywords(text: str) -> set[str]:
    found, rest = set(), text
    for kw, bucket in KEYWORDS:
        pat = re.compile(rf"\b{kw}\b", re.IGNORECASE)
        if pat.search(rest):
            found.add(bucket)
            rest = pat.sub(" ", rest)
    lowered = text.lower()
    if re.search(r"\b(required|mandatory)\b", lowered):
        found.add("required")
    if re.search(r"\boptional\b", lowered):
        found.add("optional")
    return found


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1}


class MockJudge:
    name = "mock"
    model = MOCK_MODEL
    is_live = False

    def __init__(self, script: dict[str, dict[str, float]] | None = None):
        self.script = script or {}
        self.calls = 0

    async def __aenter__(self) -> "MockJudge":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    def heuristic(self, claim: str, quote: str, passage: str) -> dict[str, float]:
        claim_kw, quote_kw = _keywords(claim), _keywords(quote)
        if claim_kw and quote_kw and not (claim_kw & quote_kw):
            return {"supports": 0.10, "contradicts": 0.70, "says_nothing": 0.20}
        cw = _words(claim)
        coverage = len(cw & _words(passage)) / len(cw) if cw else 0.0
        if coverage >= 0.85:
            return {"supports": 0.85, "contradicts": 0.05, "says_nothing": 0.10}
        if coverage >= 0.6:
            return {"supports": 0.55, "contradicts": 0.05, "says_nothing": 0.40}
        return {"supports": 0.20, "contradicts": 0.05, "says_nothing": 0.75}

    async def judge(self, claim: str, quote: str, passage: str) -> JudgeResult:
        self.calls += 1
        t0 = time.perf_counter()
        probs = normalise_probs(self.script.get(claim) or self.heuristic(claim, quote, passage))
        return JudgeResult(
            judge=self.name,
            model=self.model,
            mock=True,
            probabilities=probs,
            confidence=max(probs.values()),
            latency_ms=(time.perf_counter() - t0) * 1000,
            input_tokens=None,
            estimated_cost_usd=0.0,
            raw={"mock": True, "scripted": claim in self.script},
        )
