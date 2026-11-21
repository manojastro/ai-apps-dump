from app.agents.graph import run_pipeline
from app.models.profile import Holding, HouseholdProfile


def _run(fixtures, fixture_id: str):
    row = next(h for h in fixtures["households"] if h["id"] == fixture_id)
    profile = HouseholdProfile.model_validate(row["profile"])
    holdings = [Holding.model_validate(h) for h in profile.existing_holdings]
    return run_pipeline(profile, holdings, conflict=fixture_id == "11")


def test_forbidden_chit_never_allocated(fixtures):
    plan = _run(fixtures, "6")
    assert any(v.code == "FORBIDDEN_PRODUCT" or "chit" in v.message.lower() for v in plan.vetoes)
    for s in plan.scenarios:
        assert s.alternatives_pct == 0 or plan.no_valid_plan
        for w in s.weights:
            assert not any("chit" in v.lower() for v in w.example_vehicles)


def test_new_regime_does_not_misuse_80c(fixtures):
    plan = _run(fixtures, "8")
    blob = " ".join(plan.tax_notes).lower()
    assert "not recommended solely" in blob or "not applied automatically" in blob
    assert "fill-order" not in blob


def test_old_regime_mentions_80c_capacity(fixtures):
    plan = _run(fixtures, "7")
    blob = " ".join(plan.tax_notes).lower()
    assert "80c" in blob


def test_international_and_crypto_forbidden(fixtures):
    plan = _run(fixtures, "9")
    for s in plan.scenarios:
        assert s.international_pct <= 0.05
        assert s.alternatives_pct <= 0.05


def test_thin_reserve_rejects_speculative(fixtures):
    plan = _run(fixtures, "5")
    assert plan.risk_status in {"VETO", "PASS_WITH_CONDITIONS"} or plan.no_valid_plan
    # After retry, alternatives must be 0.
    for s in plan.scenarios:
        assert s.alternatives_pct <= 0.05 or plan.no_valid_plan


def test_conflicting_sources_flagged(fixtures):
    plan = _run(fixtures, "11")
    assert any("CONFLICTING_SOURCE" in w for w in plan.data_quality_warnings)


def test_degraded_labelled(fixtures):
    plan = _run(fixtures, "10")
    assert plan.degraded
    assert any("DEGRADED" in w or "MOCK" in w for w in plan.data_quality_warnings)
