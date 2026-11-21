"""Pydantic v2 schemas for the golden set and run results."""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "answerable", "unanswerable", "conflicting", "exact_code", "multi_hop", "outdated"
]


class GoldenRecord(BaseModel):
    """One frozen eval question. All data is synthetic (Acme Retail Ltd)."""

    id: str
    question: str
    service: str = "opscopilot"
    category: Category
    expected_doc_ids: list[str] = Field(default_factory=list)
    reference_answer: str = ""
    must_refuse: bool = False
    smoke: bool = False
    author: Literal["human", "llm_draft_reviewed"] = "human"
    notes: str = ""


class TargetAnswer(BaseModel):
    """What a target returned for one golden question."""

    doc_ids: list[str] = Field(default_factory=list)
    answer: str = ""
    citations: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


class ScoredRecord(BaseModel):
    """Per-question scores written into the run report."""

    id: str
    category: str
    hit_at_5: float
    recall_at_5: float
    reciprocal_rank: float
    context_precision: float
    context_recall: float
    faithfulness: float
    judge_correctness: int
    judge_completeness: int
    judge_safety: int
    refused: bool
    refusal_correct: bool
    citation_validity: float
    latency_ms: float
    cost_usd: float
