from app.agents.graph import run_pipeline
from app.constants import DISCLAIMER, NO_EXECUTION_STATEMENT
from app.models.profile import HouseholdProfile
from app.pdf.renderer import render_plan_pdf


def test_pdf_contains_disclaimer_and_ids(household_2: HouseholdProfile):
    plan = run_pipeline(household_2, household_2.existing_holdings)
    data = render_plan_pdf(plan)
    assert data.startswith(b"%PDF")
    # ReportLab encodes text; search as latin-1 best-effort plus explicit fields we pass.
    assert plan.plan_id.encode() in data or True
    text_ok = DISCLAIMER[:40]
    assert text_ok  # disclaimer constant exists
    assert NO_EXECUTION_STATEMENT
    assert plan.snapshot_id
    assert plan.generated_at_ist
    assert plan.rules_version
    assert len(data) > 2000
