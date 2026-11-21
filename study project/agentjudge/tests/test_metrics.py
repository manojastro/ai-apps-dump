"""Tests for retrieval metrics (pure code)."""

from agentjudge.metrics import (
    citation_validity,
    context_precision,
    context_recall,
    hit_rate_at_k,
    mrr,
    recall_at_k,
    reciprocal_rank,
    refusal_accuracy,
)


def test_hit_rate_at_k_hit_and_miss() -> None:
    assert hit_rate_at_k(["A", "B", "C"], ["B"], 5) == 1.0
    assert hit_rate_at_k(["A", "B", "C"], ["Z"], 5) == 0.0


def test_hit_rate_respects_k() -> None:
    assert hit_rate_at_k(["A", "B", "C"], ["C"], 2) == 0.0
    assert hit_rate_at_k(["A", "B", "C"], ["C"], 3) == 1.0


def test_recall_at_k_partial() -> None:
    assert recall_at_k(["A", "B"], ["A", "B", "C", "D"], 5) == 0.5


def test_reciprocal_rank_positions() -> None:
    assert reciprocal_rank(["A", "B"], ["A"]) == 1.0
    assert reciprocal_rank(["A", "B"], ["B"]) == 0.5
    assert reciprocal_rank(["A", "B"], ["Z"]) == 0.0


def test_mrr_averages() -> None:
    assert mrr([["A"], ["X", "A"]], [["A"], ["A"]]) == 0.75


def test_context_precision_recall() -> None:
    assert context_precision(["A", "B", "X"], ["A", "B"]) == 2 / 3
    assert context_recall(["A"], ["A", "B"]) == 0.5


def test_refusal_accuracy() -> None:
    assert refusal_accuracy([True, False, True], [True, False, False]) == 2 / 3


def test_citation_validity() -> None:
    assert citation_validity(["A", "Z"], ["A", "B"]) == 0.5
    assert citation_validity([], ["A"]) == 1.0


def test_empty_expected_edge_cases() -> None:
    assert hit_rate_at_k([], [], 5) == 1.0
    assert recall_at_k(["A"], [], 5) == 0.0
