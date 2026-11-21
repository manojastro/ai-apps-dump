from app.agents.graph import run_pipeline
from app.models.profile import HouseholdProfile


def test_plan_is_versioned(household_2: HouseholdProfile):
    plan = run_pipeline(household_2, household_2.existing_holdings)
    assert plan.version == 1
    plan.selected = "balance"
    plan.version += 1
    assert plan.version == 2
    assert plan.snapshot_id
    assert plan.rules_version
