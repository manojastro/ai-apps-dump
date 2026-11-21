"""Measured golden evaluation; no business-level MTTR claims or paid calls by default."""

import argparse
import asyncio
import json
from pathlib import Path
from statistics import mean
from time import perf_counter
from uuid import uuid4

from app.config import Settings
from app.db.models import EvaluationRow
from app.db.repository import Repository
from app.graph.workflow import build_graph, initial_state
from app.llm.online import StructuredProvider
from app.models.domain import Candidate, Incident, Operation, Scenario, now
from app.security.policy import Role, authorize
from app.validators.engine import all_passed, validate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from sqlalchemy.orm import Session

from simulator.pipeline import load_fixture, replay

GOLDEN_PATH = Path(__file__).parent / "golden" / "incidents.json"


async def evaluate(online: bool = False) -> dict:
    cases = json.loads(GOLDEN_PATH.read_text())
    results = []
    for case in cases:
        provider = StructuredProvider(Settings()) if online else None
        incident = Incident(
            id=str(uuid4()),
            scenario=case["scenario"],
            title=case["incident_title"],
            demo_force_first_fix_fail=case["force_first_fail"],
            max_attempts=case["max_attempts"],
        )
        tool_events: list[tuple[str, str]] = []

        async def capture(incident_id, kind, node, payload, events=tool_events):
            if kind == "tool_called":
                events.append((node, payload["role"]))

        started = perf_counter()
        try:
            graph = build_graph(InMemorySaver(), provider=provider, event=capture)
            config = {"configurable": {"thread_id": incident.id}, "recursion_limit": 128}
            state = await graph.ainvoke(initial_state(incident), config)
            interrupted = bool(state.get("__interrupt__"))
            risk = state.get("risk_level")
            if interrupted:
                state = await graph.ainvoke(
                    Command(
                        resume={
                            "actor": "golden-evaluator",
                            "comment": "Fixture policy allows artifact release",
                            "approved": True,
                        }
                    ),
                    config,
                )
            attempts = state.get("attempt_history", [])
            evidence_ids = {e.id for e in state["aggregated_evidence"]}
            operations = state["candidate_remediation"].operations
            hypotheses = state.get("root_cause_hypotheses", [])
            refs = [ref for h in hypotheses for ref in h.evidence_ids]
            valid_tools = 0
            for tool, role in tool_events:
                try:
                    authorize(Role(role), tool)
                    valid_tools += 1
                except PermissionError:
                    pass  # Explicitly counted below as incorrect tool selection.
            results.append(
                {
                    "case_id": case["id"],
                    "scenario": case["scenario"],
                    "expected_status": case["expected_status"],
                    "status": state["final_status"],
                    "top_1_correct": bool(
                        hypotheses and hypotheses[0].cause == case["known_root_cause"]
                    ),
                    "top_k_correct": any(
                        h.cause == case["known_root_cause"] for h in hypotheses[:3]
                    ),
                    "evidence_coverage": len(evidence_ids & set(case["important_evidence"]))
                    / len(case["important_evidence"]),
                    "unsupported_claims": sum(ref not in evidence_ids for ref in refs),
                    "claim_count": len(refs),
                    "attempts": len(attempts),
                    "validation_passed": bool(attempts and all_passed(attempts[-1].validations)),
                    "risk_correct": risk == case["risk"],
                    "escalation_correct": interrupted == case["requires_approval"],
                    "operations_correct": case["acceptable_operation"] in operations,
                    "branches_correct": {e.branch for e in state["aggregated_evidence"]}
                    == set(case["investigation_branches"]),
                    "tools_correct": valid_tools,
                    "tool_count": len(tool_events),
                    "mandatory_checks_executed": all(
                        {r.validator for r in a.validations} == set(case["required_validators"])
                        for a in attempts
                    ),
                    "attempt_statuses": [a.status for a in attempts],
                    "duration_seconds": perf_counter() - started,
                }
            )
        finally:
            if provider:
                await provider.close()
    # Independent adversarial probes: known wrong output, no-op and wrong unit candidates.
    accepted_bad, bad_count = 0, 0
    operation_by_scenario = {
        "schema_drift": Operation.MAP_CUSTOMER,
        "null_spike": Operation.RESTORE_CUSTOMER,
        "duplicates": Operation.DEDUPLICATE,
        "transformation_regression": Operation.CORRECT_AMOUNT,
        "dependency_failure": Operation.RETRY_DEPENDENCY,
    }
    for scenario in Scenario:
        fixture = load_fixture(scenario)
        for candidate in [
            Candidate(summary="No remediation"),
            Candidate(
                summary="Wrong amount units",
                operations=[operation_by_scenario[scenario]],
                amount_divisor=1,
            ),
        ]:
            bad_count += 1
            accepted_bad += all_passed(validate(fixture, replay(fixture, candidate)))
    metrics = {
        "incident_count": len(results),
        "root_cause_top_1_accuracy": mean(r["top_1_correct"] for r in results),
        "root_cause_top_3_recall": mean(r["top_k_correct"] for r in results),
        "evidence_coverage": mean(r["evidence_coverage"] for r in results),
        "unsupported_claim_rate": sum(r["unsupported_claims"] for r in results)
        / max(sum(r["claim_count"] for r in results), 1),
        "remediation_validation_pass_rate": mean(r["validation_passed"] for r in results),
        "false_remediation_acceptance_rate": accepted_bad / bad_count,
        "adversarial_candidates": bad_count,
        "false_acceptances": accepted_bad,
        "average_loop_attempts": mean(r["attempts"] for r in results),
        "human_escalation_accuracy": mean(r["escalation_correct"] for r in results),
        "risk_classification_accuracy": mean(r["risk_correct"] for r in results),
        "tool_selection_correctness": sum(r["tools_correct"] for r in results)
        / max(sum(r["tool_count"] for r in results), 1),
        "workflow_completion_rate": mean(r["status"] == "COMPLETED" for r in results),
        "expected_outcome_accuracy": mean(r["status"] == r["expected_status"] for r in results),
        "average_analysis_seconds": mean(r["duration_seconds"] for r in results),
    }
    return {
        "id": str(uuid4()),
        "created_at": now(),
        "provider": "online" if online else "deterministic",
        "metrics": metrics,
        "cases": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--output", default="evals/results/latest.json")
    args = parser.parse_args()
    if args.online and Settings().llm_provider == "mock":
        parser.error("--online requires a configured real provider")
    report = asyncio.run(evaluate(args.online))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    if args.persist:
        repo = Repository(Settings())
        repo.migrate()
        with Session(repo.engine) as session, session.begin():
            session.add(
                EvaluationRow(**{k: report[k] for k in ("id", "created_at", "metrics", "cases")})
            )
        repo.close()
    print(json.dumps(report["metrics"], indent=2))
    if report["metrics"]["false_remediation_acceptance_rate"] > 0 or (
        report["metrics"]["expected_outcome_accuracy"] < 1
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
