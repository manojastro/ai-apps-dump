import asyncio
from uuid import uuid4

from app.adapters.local import LocalSimulatorAdapter
from app.graph.workflow import build_graph, initial_state
from app.llm.providers import DeterministicProvider
from app.models.domain import Approval, Incident, Operation, Scenario
from app.verifier.independent import IndependentVerifier
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


def incident(scenario=Scenario.SCHEMA_DRIFT, **kwargs):
    return Incident(id=str(uuid4()), scenario=scenario, **kwargs)


async def run(case, **kwargs):
    graph = build_graph(checkpointer=InMemorySaver(), **kwargs)
    result = await graph.ainvoke(initial_state(case), {"configurable": {"thread_id": case.id}})
    return graph, result


async def test_first_fix_is_rejected_feedback_revises_and_verifier_approves():
    _, result = await run(incident(demo_force_first_fix_fail=True))
    assert result["final_status"] == "COMPLETED"
    assert [a.status for a in result["attempt_history"]] == ["REJECTED", "PASSED"]
    assert "TransformationValidator" in result["attempt_history"][0].feedback[0]
    assert result["verification_result"].decision == "APPROVE"
    assert result["final_remediation"]["post_validation"] == "PASS"


async def test_loop_terminates_at_attempt_budget_without_artifact():
    _, result = await run(incident(demo_force_first_fix_fail=True, max_attempts=1))
    assert result["final_status"] == "FAILED"
    assert len(result["attempt_history"]) == 1
    assert not result.get("final_remediation")
    assert not result.get("verification_result")


async def test_normal_mode_has_no_forced_failure():
    _, result = await run(incident(demo_force_first_fix_fail=False))
    assert result["attempt_number"] == 1
    assert result["final_status"] == "COMPLETED"


async def test_parallel_branches_really_overlap_and_converge_once():
    class BarrierAdapter(LocalSimulatorAdapter):
        def __init__(self):
            self.arrived = set()
            self.all_arrived = asyncio.Event()

        async def investigate(self, case, branch):
            self.arrived.add(branch)
            if len(self.arrived) == 5:
                self.all_arrived.set()
            await asyncio.wait_for(self.all_arrived.wait(), timeout=3)
            return await super().investigate(case, branch)

    adapter = BarrierAdapter()
    _, result = await run(incident(), adapter=adapter)
    assert len(adapter.arrived) == len(result["aggregated_evidence"]) == 5
    assert len({e.id for e in result["aggregated_evidence"]}) == 5


async def test_configuration_fix_pauses_and_resumes_after_approval():
    case = incident(Scenario.DEPENDENCY)
    graph, paused = await run(case)
    assert paused["__interrupt__"]
    assert not paused.get("final_remediation")
    decision = Approval(actor="operator", comment="Reviewed retry diff", approved=True)
    final = await graph.ainvoke(
        Command(resume=decision.model_dump()), {"configurable": {"thread_id": case.id}}
    )
    assert final["final_status"] == "COMPLETED"
    assert final["approval_status"] == "APPROVED"


async def test_rejection_never_releases_artifact():
    case = incident(Scenario.DEPENDENCY)
    graph, _ = await run(case)
    decision = Approval(actor="operator", comment="Change window closed", approved=False)
    final = await graph.ainvoke(
        Command(resume=decision.model_dump()), {"configurable": {"thread_id": case.id}}
    )
    assert final["final_status"] == "REJECTED"
    assert not final.get("final_remediation")


async def test_independent_verifier_rejection_cannot_execute_artifact():
    class RejectingVerifier(IndependentVerifier):
        async def verify(self, package):
            verdict = await super().verify(package)
            return verdict.model_copy(
                update={"decision": "REJECT", "reason_summary": "Test rejection"}
            )

    _, result = await run(incident(), verifier=RejectingVerifier())
    assert result["final_status"] == "REJECTED"
    assert not result.get("final_remediation")


async def test_critical_operation_is_blocked_before_sandbox():
    class DangerousProvider(DeterministicProvider):
        async def plan(self, hypothesis, evidence, context, feedback):
            candidate = await super().plan(hypothesis, evidence, context, feedback)
            return candidate.model_copy(update={"operations": [Operation.DELETE]})

    _, result = await run(incident(), provider=DangerousProvider())
    assert result["final_status"] == "FAILED"
    assert not result.get("replay_result")
