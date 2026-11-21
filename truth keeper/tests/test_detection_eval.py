"""Detection quality gates against planted ground truth (the guide's target: recall >= 0.95)."""

from evals.detection_eval import evaluate


def test_default_dataset_recall_and_precision(dataset):
    root, gt, _ = dataset
    r = evaluate(root, gt)
    for t, m in r["per_type"].items():
        assert m["recall"] >= 0.95, (t, m)
        assert m["precision"] >= 0.95, (t, m)
    assert r["unmatched"] == {"billing": 0, "marketing": 0}


def test_hard_dataset_recall(hard_dataset):
    root, gt, _ = hard_dataset
    r = evaluate(root, gt)
    assert r["overall"]["recall"] >= 0.95, r["overall"]


def test_every_conflict_has_evidence_and_impact(dataset):
    from app.core.detection import detect_dir

    root, _, _ = dataset
    for c in detect_dir(root).conflicts:
        assert c.evidence["crm_account_id"] == c.customer_key
        assert c.impact is not None and c.impact.formula


def test_name_only_matching_hurts_precision(dataset):
    """Debugging exercise 1: matching on name only drops precision on EMAIL_MISMATCH and DUPLICATE_CUSTOMER."""
    root, gt, _ = dataset
    good, bad = evaluate(root, gt), evaluate(root, gt, strategy="name_only")
    for t in ("EMAIL_MISMATCH", "DUPLICATE_CUSTOMER"):
        assert bad["per_type"][t]["precision"] < good["per_type"][t]["precision"] - 0.3
