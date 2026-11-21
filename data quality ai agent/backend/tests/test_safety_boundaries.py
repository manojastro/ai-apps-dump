from copy import deepcopy
from uuid import uuid4

import pytest
from app.graph.workflow import build_graph, initial_state
from app.models.domain import Candidate, Incident, Operation, Scenario
from app.validators.engine import all_passed, validate
from app.verifier.independent import IndependentVerifier
from langgraph.checkpoint.memory import InMemorySaver

from simulator.pipeline import load_fixture, replay


async def test_verifier_package_excludes_scenario_labels_and_demo_controls():
    class InspectingVerifier(IndependentVerifier):
        async def verify(self, package):
            serialized = package.incident.model_dump()
            assert set(serialized) == {"id", "pipeline_id", "environment", "title"}
            return await super().verify(package)

    case = Incident(id=str(uuid4()), scenario=Scenario.SCHEMA_DRIFT)
    graph = build_graph(InMemorySaver(), verifier=InspectingVerifier())
    result = await graph.ainvoke(initial_state(case), {"configurable": {"thread_id": case.id}})
    assert result["final_status"] == "COMPLETED"


def test_conflicting_duplicate_cannot_be_dropped_to_make_reconciliation_pass():
    fixture = load_fixture(Scenario.DUPLICATES)
    wrong = deepcopy(fixture.source_rows[0])
    wrong["amount_cents"] = 999999
    fixture.source_rows.insert(0, wrong)
    result = replay(
        fixture, Candidate(summary="Drop duplicate", operations=[Operation.DEDUPLICATE])
    )
    assert not all_passed(validate(fixture, result))
    assert "conflicting" in " ".join(result.errors)


@pytest.mark.parametrize("corrupt", ["duplicate", "missing", "warning", "failed"])
def test_critical_inventory_tampering_never_passes(corrupt):
    fixture = load_fixture(Scenario.SCHEMA_DRIFT)
    result = replay(fixture, Candidate(summary="Map", operations=[Operation.MAP_CUSTOMER]))
    checks = validate(fixture, result)
    if corrupt == "duplicate":
        checks.append(checks[0])
    elif corrupt == "missing":
        checks.pop()
    elif corrupt == "warning":
        checks[0].severity = "warning"
    else:
        checks[0].status = "FAIL"
    assert not all_passed(checks)
