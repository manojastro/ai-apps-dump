"""Isolated scripted-agent entry point. Input contains no expected outcomes."""

import json
import sys
import time

from packages.agent.contracts import Budget
from packages.agent.scripted import diagnose
from packages.connectors.replay import ConnectorError, ReplayConnector


def execute(value):
    packet = value["packet"]
    packet["observed_at"] = time.time()
    adapter = ReplayConnector(packet)
    evidence, calls, denied = [], [], False
    budget = Budget()
    if value.get("probe"):
        try:
            adapter.call(value["probe"]["tool"], "evaluation", value["probe"]["parameters"])
        except ConnectorError:
            denied = True
    for tool in (
        "query_metrics",
        "search_traces",
        "search_logs",
        "get_deployments",
        "compare_config",
        "search_runbooks",
    ):
        budget.reserve_tool()
        start = time.perf_counter()
        try:
            observation = adapter.call(tool, "evaluation")
            evidence.append(observation)
            output = observation.model_dump()
            status = "success"
        except ConnectorError as exc:
            output, status = {"error": exc.code}, "error"
        calls.append(
            {
                "tool": tool,
                "inputs": {},
                "output": output,
                "status": status,
                "duration_ms": round((time.perf_counter() - start) * 1000, 3),
            }
        )
    diagnosis = diagnose(evidence, value["method"])
    diagnosis.validate_evidence(evidence, "evaluation")
    return {
        "diagnosis": diagnosis.model_dump(),
        "tools": calls,
        "probe_denied": denied,
        "budget": budget.model_dump(),
        "prohibited_effects": 0,
        "tokens": 0,
        "cost": None,
    }


if __name__ == "__main__":
    print(json.dumps(execute(json.loads(sys.stdin.read()))))
