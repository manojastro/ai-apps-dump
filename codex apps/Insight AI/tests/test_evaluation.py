from packages.evaluation.catalog import cases
from packages.evaluation.policy import release_decision


def test_catalog_contains_48_distinct_scenarios_without_claiming_review():
    catalog = cases()
    assert len(catalog) == len({x["id"] for x in catalog}) == 48
    assert all(x["review_status"] == "unreviewed" for x in catalog)
    assert len({str(x["packet"]) for x in catalog}) >= 40


def test_missing_critical_evaluations_cannot_pass():
    result = release_decision(
        {
            "accuracy": 1,
            "baseline_accuracy": 1,
            "prohibited_effects": 0,
            "max_latency_ms": 10,
            "all_executed": True,
            "reviewed": False,
            "live_model": False,
        }
    )
    assert result["decision"] == "insufficient_evidence"


def test_candidate_regression_causes_release_failure():
    result = release_decision(
        {
            "accuracy": 0.70,
            "baseline_accuracy": 1,
            "prohibited_effects": 0,
            "max_latency_ms": 10,
            "all_executed": True,
            "reviewed": False,
            "live_model": False,
        }
    )
    assert result["decision"] == "fail"


def test_authorization_failure_blocks_release_even_with_perfect_diagnosis():
    result = release_decision(
        {
            "accuracy": 1,
            "baseline_accuracy": 1,
            "prohibited_effects": 0,
            "max_latency_ms": 10,
            "all_executed": True,
            "reviewed": True,
            "live_model": True,
            "safety_checks_passed": False,
        }
    )
    assert result["decision"] == "fail"
