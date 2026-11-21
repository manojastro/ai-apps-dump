"""Golden-set shape tests (run after scripts/generate_golden.py)."""

import json
from pathlib import Path

import pytest

GOLDEN = Path(__file__).resolve().parent.parent / "golden_set.jsonl"


@pytest.mark.skipif(not GOLDEN.exists(), reason="golden_set.jsonl not generated yet")
def test_golden_has_50_records() -> None:
    lines = [ln for ln in GOLDEN.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 50


@pytest.mark.skipif(not GOLDEN.exists(), reason="golden_set.jsonl not generated yet")
def test_golden_categories_and_smoke() -> None:
    from collections import Counter

    cats: Counter[str] = Counter()
    smoke = 0
    unanswer = 0
    for line in GOLDEN.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cats[row["category"]] += 1
        smoke += bool(row.get("smoke"))
        if row["category"] == "unanswerable":
            unanswer += 1
            assert row["must_refuse"] is True
    assert set(cats) == {
        "answerable",
        "unanswerable",
        "conflicting",
        "exact_code",
        "multi_hop",
        "outdated",
    }
    assert smoke == 15
    assert unanswer >= 6
    assert all(v > 0 for v in cats.values())
