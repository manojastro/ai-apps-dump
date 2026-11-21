"""Retrieval eval: recall@k over hand-written questions, abstention, and access control."""

from pathlib import Path
from typing import Any

import yaml

from invoiceflow.data.models import Frozen, Role
from invoiceflow.ports.retrieval import Retriever
from invoiceflow.retrieval.models import AccessScope

QUESTIONS_PATH = Path("evals/datasets/retrieval_questions.yaml")
KS = (1, 3, 5)


class QuestionResult(Frozen):
    id: str
    retrieved: tuple[str, ...]
    expected: tuple[str, ...]
    hit_at: dict[int, bool]
    abstained: bool
    abstain_expected: bool
    access_violation: bool


class RetrievalReport(Frozen):
    questions: int
    answerable: int
    recall_at: dict[int, float]
    abstention_correct: int
    abstention_cases: int
    access_violations: int
    results: tuple[QuestionResult, ...]


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(data["questions"])


def run_retrieval_eval(retriever: Retriever, questions: list[dict[str, Any]]) -> RetrievalReport:
    results = []
    for q in questions:
        vendors = q.get("vendors")
        scope = AccessScope(
            role=Role(q["role"]), vendor_ids=frozenset(vendors) if vendors else None
        )
        result = retriever.search(q["q"], scope, k=max(KS))
        ids = result.chunk_ids
        expected = tuple(q.get("expected", ()))
        forbidden_docs = set(q.get("forbidden_docs", ()))
        forbidden_types = set(q.get("forbidden_doc_types", ()))
        violation = any(
            h.chunk.doc_id in forbidden_docs
            or h.chunk.doc_type in forbidden_types
            or not scope.allows(h.chunk)
            for h in result.hits
        )
        results.append(
            QuestionResult(
                id=q["id"],
                retrieved=ids,
                expected=expected,
                hit_at={k: any(e in ids[:k] for e in expected) for k in KS},
                abstained=result.abstained,
                abstain_expected=q.get("expect") == "abstain",
                access_violation=violation,
            )
        )
    answerable = [r for r in results if r.expected]
    abstain_cases = [r for r in results if r.abstain_expected]
    return RetrievalReport(
        questions=len(results),
        answerable=len(answerable),
        recall_at={
            k: round(sum(r.hit_at[k] for r in answerable) / len(answerable), 3)
            if answerable
            else 0.0
            for k in KS
        },
        abstention_correct=sum(r.abstained for r in abstain_cases),
        abstention_cases=len(abstain_cases),
        access_violations=sum(r.access_violation for r in results),
        results=tuple(results),
    )
