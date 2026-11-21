import pytest

from citation_guard.gate import (
    AnswerResult,
    Thresholds,
    Verdict,
    answer_result,
    claim_verdict,
    stringmatch_verdict,
)
from citation_guard.quote_match import QuoteStatus

TH = Thresholds(pass_supports=0.80, fail_contradicts=0.50)
FOUND = QuoteStatus.FOUND_IN_CITED_SECTION


def p(s, c, n):
    return {"supports": s, "contradicts": c, "says_nothing": n}


def test_supports_boundary():
    assert claim_verdict(FOUND, p(0.80, 0.10, 0.10), TH) == Verdict.PASS
    assert claim_verdict(FOUND, p(0.79, 0.10, 0.11), TH) == Verdict.HUMAN_REVIEW


def test_contradicts_boundary():
    assert claim_verdict(FOUND, p(0.20, 0.50, 0.30), TH) == Verdict.FAIL_CONTRADICTED
    assert claim_verdict(FOUND, p(0.21, 0.49, 0.30), TH) == Verdict.HUMAN_REVIEW


def test_found_elsewhere_still_judged():
    assert claim_verdict(QuoteStatus.FOUND_ELSEWHERE, p(0.9, 0.05, 0.05), TH) == Verdict.PASS


def test_not_found_is_fabricated_regardless_of_probs():
    assert claim_verdict(QuoteStatus.NOT_FOUND, p(1, 0, 0), TH) == Verdict.FAIL_FABRICATED_QUOTE
    assert claim_verdict(QuoteStatus.NOT_FOUND, None, TH) == Verdict.FAIL_FABRICATED_QUOTE


def test_too_short_and_missing_probs_go_to_review():
    assert claim_verdict(QuoteStatus.QUOTE_TOO_SHORT, p(1, 0, 0), TH) == Verdict.HUMAN_REVIEW
    assert claim_verdict(FOUND, None, TH) == Verdict.HUMAN_REVIEW


def test_stringmatch_baseline():
    assert stringmatch_verdict(FOUND) == Verdict.PASS
    assert stringmatch_verdict(QuoteStatus.FOUND_ELSEWHERE) == Verdict.PASS
    assert stringmatch_verdict(QuoteStatus.NOT_FOUND) == Verdict.FAIL_FABRICATED_QUOTE
    assert stringmatch_verdict(QuoteStatus.QUOTE_TOO_SHORT) == Verdict.HUMAN_REVIEW


@pytest.mark.parametrize(
    "verdicts,expected",
    [
        ([Verdict.PASS, Verdict.PASS], AnswerResult.DELIVER),
        ([Verdict.PASS, Verdict.HUMAN_REVIEW], AnswerResult.REVIEW),
        ([Verdict.PASS, Verdict.FAIL_CONTRADICTED], AnswerResult.BLOCK),
        ([Verdict.HUMAN_REVIEW, Verdict.FAIL_FABRICATED_QUOTE], AnswerResult.BLOCK),
        ([], AnswerResult.REVIEW),
    ],
)
def test_answer_aggregation(verdicts, expected):
    assert answer_result(verdicts) == expected
