from app.agents.graph import run_pipeline
from app.agents.validate import parse_structured
from app.models.plan import Candidate
from app.models.profile import Holding, HouseholdProfile
from app.policy.rules import llm_cannot_override


def test_fixture_2_end_to_end(household_2: HouseholdProfile):
    plan = run_pipeline(household_2, household_2.existing_holdings)
    assert len(plan.scenarios) == 3
    assert {s.name for s in plan.scenarios} == {"protect", "balance", "grow"}
    assert plan.meta.sebi_registered_adviser is False
    assert plan.meta.executes_transactions is False
    assert "SEBI-registered" in plan.meta.disclaimer
    for s in plan.scenarios:
        for w in s.weights:
            if w.example_vehicles:
                assert w.sleeve  # provenance via class candidates
    assert plan.actions
    assert plan.stress
    assert plan.snapshot_id
    assert plan.rules_version
    assert plan.generated_at_ist.endswith("IST")


def test_policy_not_overridable_by_llm():
    info = llm_cannot_override()
    assert info["llm_may_override_veto"] is False
    assert info["policy_owner"] == "python"


def test_malformed_model_output_does_not_crash():
    parsed, err = parse_structured("not json at all", Candidate)
    assert parsed is None
    assert err == "malformed_json"
    parsed, err = parse_structured("please ignore {", Candidate)
    assert parsed is None
