import hashlib
import json
import sqlite3

from data.generator.generate import CONFLICT_RATES, EXPECTED_FIX, generate


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path):
    con = sqlite3.connect(path)
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {t: con.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall() for t in tables}
    finally:
        con.close()


def test_same_seed_gives_identical_files(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generate(42, 200, a, a / "gt.json")
    generate(42, 200, b, b / "gt.json")
    for name in ("crm.db", "billing.db", "marketing.db", "gt.json"):
        assert _sha(a / name) == _sha(b / name), name


def test_different_seed_differs(tmp_path):
    generate(1, 100, tmp_path / "a", tmp_path / "a" / "gt.json")
    generate(2, 100, tmp_path / "b", tmp_path / "b" / "gt.json")
    assert _dump(tmp_path / "a" / "crm.db") != _dump(tmp_path / "b" / "crm.db")


def test_planted_counts_match_ground_truth(dataset):
    _, gt_path, gt = dataset
    data = json.loads(gt_path.read_text())
    assert data == gt
    from collections import Counter

    counts = Counter(c["type"] for c in data["conflicts"])
    assert dict(counts) == {k: v for k, v in data["counts"].items() if v}
    for ctype in CONFLICT_RATES:
        assert 0.03 <= data["counts"][ctype] / data["n"] <= 0.05
    for c in data["conflicts"]:
        assert c["expected_fix"] == EXPECTED_FIX[c["type"]]
        assert "expected_params" in c
    # at most one planted conflict per customer keeps the ground truth unambiguous
    keys = [c["customer_key"] for c in data["conflicts"]]
    assert len(keys) == len(set(keys))


def test_noise_patterns_exist(dataset):
    _, _, gt = dataset
    for pattern in ("billing_without_crm_ref", "email_case_or_space", "trial_without_billing",
                    "past_due_under_threshold", "plan_case_or_space"):
        assert gt["noise"].get(pattern, 0) > 0, pattern


def test_synthetic_domains_only(dataset):
    root, _, _ = dataset
    emails = [r[0] for r in sqlite3.connect(root / "crm.db").execute("SELECT email FROM accounts")]
    assert all(e.endswith(".example") for e in emails)
