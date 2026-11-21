"""The gate: code turns quote status + judge probabilities into the final verdict.

Judges only supply probabilities. Every decision rule lives here, with thresholds from config.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from .quote_match import QuoteStatus


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL_FABRICATED_QUOTE = "FAIL_FABRICATED_QUOTE"
    FAIL_CONTRADICTED = "FAIL_CONTRADICTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"

    @property
    def is_fail(self) -> bool:
        return self.value.startswith("FAIL")


class AnswerResult(str, Enum):
    DELIVER = "DELIVER"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"


class Thresholds(BaseModel):
    pass_supports: float = 0.80
    fail_contradicts: float = 0.50


def claim_verdict(
    quote_status: QuoteStatus,
    probabilities: dict[str, float] | None,
    th: Thresholds,
) -> Verdict:
    if quote_status == QuoteStatus.NOT_FOUND:
        return Verdict.FAIL_FABRICATED_QUOTE
    if quote_status == QuoteStatus.QUOTE_TOO_SHORT:
        return Verdict.HUMAN_REVIEW
    if not probabilities:  # judge error or no judgment available
        return Verdict.HUMAN_REVIEW
    if probabilities.get("supports", 0.0) >= th.pass_supports:
        return Verdict.PASS
    if probabilities.get("contradicts", 0.0) >= th.fail_contradicts:
        return Verdict.FAIL_CONTRADICTED
    return Verdict.HUMAN_REVIEW


def stringmatch_verdict(quote_status: QuoteStatus) -> Verdict:
    """Baseline: Check A alone. Every found quote passes."""
    if quote_status == QuoteStatus.NOT_FOUND:
        return Verdict.FAIL_FABRICATED_QUOTE
    if quote_status == QuoteStatus.QUOTE_TOO_SHORT:
        return Verdict.HUMAN_REVIEW
    return Verdict.PASS


def answer_result(verdicts: list[Verdict]) -> AnswerResult:
    """All PASS -> DELIVER; any FAIL -> BLOCK; otherwise REVIEW.
    An answer with no claims has nothing verified, so it goes to REVIEW."""
    if not verdicts:
        return AnswerResult.REVIEW
    if any(v.is_fail for v in verdicts):
        return AnswerResult.BLOCK
    if all(v == Verdict.PASS for v in verdicts):
        return AnswerResult.DELIVER
    return AnswerResult.REVIEW
