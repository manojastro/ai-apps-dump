from __future__ import annotations

from .engine import compare_runs
from .models import GateConfig, RunReport


def apply_gate(
    candidate: RunReport, config: GateConfig, baseline: RunReport | None = None
) -> dict:
    failures: list[dict] = []
    for metric, threshold in config.absolute_thresholds.items():
        actual = candidate.aggregate.get(metric)
        if actual is None:
            failures.append({"type": "missing_metric", "metric": metric})
        elif actual < threshold:
            failures.append({
                "type": "absolute_threshold", "metric": metric,
                "actual": actual, "threshold": threshold,
            })
    latency = candidate.aggregate.get("latency_p95_ms", 0)
    if latency > config.max_p95_latency_ms:
        failures.append({
            "type": "latency", "metric": "latency_p95_ms", "actual": latency,
            "threshold": config.max_p95_latency_ms,
        })
    cost = candidate.aggregate.get("cost_per_request_usd", 0)
    if cost > config.max_cost_per_request_usd:
        failures.append({
            "type": "cost", "metric": "cost_per_request_usd", "actual": cost,
            "threshold": config.max_cost_per_request_usd,
        })
    unsafe_count = candidate.aggregate.get("unsafe_tool_calls", 0)
    if config.forbid_unsafe_tools and unsafe_count:
        failures.append({"type": "unsafe_tool", "count": unsafe_count})
    comparison = compare_runs(candidate, baseline) if baseline else None
    if comparison:
        for metric, regression in comparison["regressions"].items():
            if regression > config.max_relative_regression:
                failures.append({
                    "type": "relative_regression", "metric": metric,
                    "regression": regression, "threshold": config.max_relative_regression,
                })
    return {
        "passed": not failures, "failures": failures, "comparison": comparison,
        "candidate_id": candidate.id, "baseline_id": baseline.id if baseline else None,
    }

