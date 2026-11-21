from __future__ import annotations

import pytest

from app.evaluation import evaluate_cases, load_cases
from app.fixtures import SCENARIOS
from app.repository import Repository
from app.workflow import InvestigationEngine
from conftest import make_incident


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", list(SCENARIOS))
async def test_each_incident_category_replays_exactly(scenario):
    repository = Repository("sqlite:///:memory:")
    engine = InvestigationEngine(repository)
    incident = make_incident(scenario, scenario.upper()[:8])
    repository.save_incident(incident)
    result = await engine.investigate(incident)
    assert result.hypotheses[0].category == SCENARIOS[scenario]["category"]
    assert result.hypotheses[0].component == SCENARIOS[scenario]["component"]


def test_dataset_contains_60_unique_ground_truth_cases():
    cases = load_cases()
    assert len(cases) == 60
    assert len({case["id"] for case in cases}) == 60
    assert {case["scenario"] for case in cases} == set(SCENARIOS)


@pytest.mark.asyncio
async def test_full_evaluation_fails_no_unsupported_claims():
    summary, rows = await evaluate_cases(load_cases())
    assert summary.passed is True
    assert summary.exact_root_cause_accuracy == 1
    assert summary.evidence_citation_coverage == 1
    assert summary.unsupported_claim_rate == 0
    assert all(row["citation_gate_passed"] for row in rows)

