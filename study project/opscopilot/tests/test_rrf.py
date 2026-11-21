"""Tests for RRF fusion: RRF(d) = sum 1/(k + rank), ranks start at 1."""

from opscopilot.retrieval import rrf_fuse


def test_both_lists_beats_one() -> None:
    fused = dict(rrf_fuse([["A", "B"], ["B", "C"]], k=60))
    # B is rank 2 + rank 1; A is rank 1 only; C is rank 2 only
    assert fused["B"] > fused["A"] > fused["C"]


def test_empty_handled() -> None:
    assert rrf_fuse([]) == []
    assert rrf_fuse([[], []]) == []
    assert rrf_fuse([["A"]], k=60)[0][0] == "A"


def test_rank1_score_math() -> None:
    # rank 1 in both lists with k=60 -> 2/61
    fused = dict(rrf_fuse([["X"], ["X"]], k=60))
    assert abs(fused["X"] - 2 / 61) < 1e-9
    # rank 1 in one list only -> 1/61
    fused2 = dict(rrf_fuse([["X"], ["Y"]], k=60))
    assert abs(fused2["X"] - 1 / 61) < 1e-9


def test_ties_deterministic() -> None:
    a = rrf_fuse([["A", "B"], ["B", "A"]], k=60)
    b = rrf_fuse([["B", "A"], ["A", "B"]], k=60)
    assert a == b
