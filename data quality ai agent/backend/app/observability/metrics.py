from datetime import datetime
from typing import Any

from app.graph.state import RecoveryState


def state_metrics(state: RecoveryState) -> dict[str, Any]:
    timings = state.get("latency_metrics", [])
    branches = [t for t in timings if t["node"].endswith("_investigator")]
    started = min((t["started_at"] for t in timings), default=None)
    ended = max((t["ended_at"] for t in timings), default=None)

    def seconds(first, last):
        return (datetime.fromisoformat(last) - datetime.fromisoformat(first)).total_seconds()

    diagnoses = [t for t in timings if t["node"] == "root_cause_synthesis"]
    attempts = state.get("attempt_history", [])
    checks = [r for a in attempts for r in a.validations]
    return {
        "graph_nodes_executed": len(timings),
        "attempts": state.get("attempt_number", 0),
        "time_to_detection_input_seconds": None,
        "detection_note": "Detection occurs in the external monitor before incident intake",
        "time_to_diagnosis_seconds": seconds(started, diagnoses[-1]["ended_at"])
        if started and diagnoses
        else None,
        "workflow_duration_seconds": seconds(started, ended) if started and ended else 0,
        "active_node_seconds": sum(t["duration_seconds"] for t in timings),
        "parallel_branch_seconds": seconds(
            min(b["started_at"] for b in branches), max(b["ended_at"] for b in branches)
        )
        if branches
        else 0,
        "validator_pass_count": sum(r.status == "PASS" for r in checks),
        "validator_fail_count": sum(r.status == "FAIL" for r in checks),
        "verifier_outcome": state["verification_result"].decision
        if state.get("verification_result")
        else None,
        **state.get("cost_metrics", {}),
    }
