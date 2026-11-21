import pytest
from app.models.domain import Candidate, Operation, Scenario
from app.validators.engine import all_passed, validate

from simulator.pipeline import load_fixture, replay


@pytest.mark.parametrize("scenario", list(Scenario))
def test_original_pipeline_fails_mandatory_validation(scenario):
    fixture = load_fixture(scenario)
    result = replay(fixture, Candidate(summary="Unchanged pipeline"))
    assert not all_passed(validate(fixture, result))


@pytest.mark.parametrize(
    "scenario,operations",
    [
        (Scenario.SCHEMA_DRIFT, [Operation.MAP_CUSTOMER]),
        (Scenario.NULL_SPIKE, [Operation.RESTORE_CUSTOMER]),
        (Scenario.DUPLICATES, [Operation.DEDUPLICATE]),
        (Scenario.TRANSFORMATION, [Operation.CORRECT_AMOUNT]),
        (Scenario.DEPENDENCY, [Operation.RETRY_DEPENDENCY]),
    ],
)
def test_acceptable_remediation_passes_all_ten_checks(scenario, operations):
    fixture = load_fixture(scenario)
    result = replay(fixture, Candidate(summary="Recovery", operations=operations))
    checks = validate(fixture, result)
    assert len(checks) == 10
    assert all_passed(checks), [c.model_dump() for c in checks if c.status == "FAIL"]


def test_wrong_units_are_rejected_even_after_schema_is_fixed():
    fixture = load_fixture(Scenario.SCHEMA_DRIFT)
    candidate = Candidate(
        summary="Wrong units", operations=[Operation.MAP_CUSTOMER], amount_divisor=1
    )
    checks = validate(fixture, replay(fixture, candidate))
    assert next(c for c in checks if c.validator == "TransformationValidator").status == "FAIL"


def test_sandbox_does_not_change_input_or_accumulate_failed_edits():
    fixture = load_fixture(Scenario.SCHEMA_DRIFT)
    before = fixture.model_dump_json()
    replay(fixture, Candidate(summary="Wrong", amount_divisor=1))
    assert fixture.model_dump_json() == before


def test_empty_or_missing_validator_results_cannot_pass():
    assert not all_passed([])
