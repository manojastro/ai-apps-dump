"""Target protocol + adapters.

The Target protocol lets one harness test many systems (OpsCopilot today,
Incident Commander in P4, red-team suites in P5): the runner only talks to
search()/ask(), never to HTTP details.
"""

from typing import Protocol

import httpx

from agentjudge.schemas import GoldenRecord, TargetAnswer


class Target(Protocol):
    """Anything AgentJudge can evaluate must implement search() + ask()."""

    name: str

    def search(self, query: str, top_k: int = 5) -> list[str]:
        """Return up to top_k doc IDs for a query."""
        ...

    def ask(self, question: str, top_k: int = 5) -> TargetAnswer:
        """Return retrieved doc IDs + generated answer + cost/latency."""
        ...


class OpsCopilotTarget:
    """HTTP adapter for OpsCopilot /v1/search and /v1/ask (httpx, sync)."""

    def __init__(self, base_url: str, timeout_s: float = 30.0) -> None:
        self.name = "opscopilot"
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout_s)

    def search(self, query: str, top_k: int = 5) -> list[str]:
        r = self._client.post("/v1/search", json={"query": query, "top_k": top_k})
        r.raise_for_status()
        data = r.json()
        ids = data.get("doc_ids", data.get("results", []))
        return [str(x) for x in ids][:top_k]

    def ask(self, question: str, top_k: int = 5) -> TargetAnswer:
        r = self._client.post("/v1/ask", json={"question": question, "top_k": top_k})
        r.raise_for_status()
        return TargetAnswer.model_validate(r.json())


REFUSAL_TEXT = (
    "I can't answer that from the Acme Retail knowledge base. "
    "No supporting document was found, so I must refuse rather than guess."
)


class StubTarget:
    """Offline canned target for tests/CI. Deterministic, costs $0.

    When given the golden records it plays a 'good but imperfect' system:
    mostly the right docs/answers, with small deterministic misses so the
    metrics show realistic (non-1.0) numbers.
    """

    def __init__(self, records: list[GoldenRecord] | None = None) -> None:
        self.name = "stub"
        self._by_question: dict[str, GoldenRecord] = {}
        for rec in records or []:
            self._by_question[rec.question] = rec

    def _record(self, question: str) -> GoldenRecord | None:
        return self._by_question.get(question)

    def search(self, query: str, top_k: int = 5) -> list[str]:
        rec = self._record(query)
        if rec is None:
            return [f"DOC-GEN-{i:03d}" for i in range(1, top_k + 1)]
        ids = list(rec.expected_doc_ids)
        if not ids:  # unanswerable: nothing relevant exists
            return []
        n = int(rec.id.split("-")[1])
        if n % 7 == 0 and len(ids) > 1:
            ids = ids[:-1]  # deterministic miss -> hit_rate stays < 1.0
        elif n % 5 == 0:
            ids = ids[1:] + ids[:1]  # deterministic reorder -> MRR < 1.0
        return ids[:top_k]

    def ask(self, question: str, top_k: int = 5) -> TargetAnswer:
        doc_ids = self.search(question, top_k)
        rec = self._record(question)
        if rec is None:
            return TargetAnswer(doc_ids=doc_ids, answer="Stub answer.", latency_ms=5.0)
        if rec.must_refuse:
            return TargetAnswer(doc_ids=[], answer=REFUSAL_TEXT, citations=[], latency_ms=5.0)
        n = int(rec.id.split("-")[1])
        if rec.category == "conflicting":
            answer = (
                f"Sources disagree. {rec.reference_answer} "
                "Flagging conflict: verify against the primary SOP before acting."
            )
        elif n % 9 == 0:
            # Deterministic weak answer: off-topic filler -> faithfulness drops.
            answer = "In general, follow ITIL best practices and check the wiki."
        else:
            answer = rec.reference_answer
        return TargetAnswer(
            doc_ids=doc_ids,
            answer=answer,
            citations=doc_ids[:2],
            latency_ms=5.0 + (n % 4),
            cost_usd=0.0,
        )
