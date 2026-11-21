"""A fixed diagnostic baseline; replay success is not LLM reasoning evidence."""

from packages.agent.contracts import Diagnosis, Evidence


def diagnose(evidence: list[Evidence], variant="script-v1") -> Diagnosis:
    usable = [e for e in evidence if not e.stale and not e.truncated]
    sources = {e.source_type: e for e in usable}
    metrics = sources.get("metrics")
    category, explanation = (
        "inconclusive",
        "Current independent evidence is insufficient to identify a cause.",
    )
    ids = []
    if metrics:
        m = metrics.payload
        trace = sources.get("traces")
        logs = sources.get("logs")
        config = sources.get("config")
        logtext = " ".join(str(x.get("message", "")) for x in logs.payload.get("records", [])) if logs else ""
        t = trace.payload if trace else {}
        if m.get("error_rate", 1) < 0.02 and m.get("p95_ms", 9999) < 300 and t.get("status") == "ok":
            category, explanation, ids = (
                "healthy",
                "Metrics and the representative trace are within the replay healthy baseline.",
                [metrics.id, trace.id],
            )
        elif m.get("payment_ms", 0) > 900 and t.get("payment_ms", 0) > 900:
            category, explanation, ids = (
                "payment_delay",
                "Elevated payment dependency latency coincides with checkout timeouts in metrics and traces.",
                [metrics.id, trace.id],
            )
        elif m.get("pool_usage", 0) >= 0.95 and m.get("pool_wait_ms", 0) > 500 and "PoolTimeout" in logtext:
            category, explanation, ids = (
                "pool_exhaustion",
                "Database pool pressure and acquisition timeouts independently support connection pool exhaustion.",
                [metrics.id, logs.id],
            )
        elif m.get("cpu", 0) >= 0.9 and t.get("compute_ms", 0) > 500:
            category, explanation, ids = (
                "cpu_saturation",
                "High CPU utilization and long checkout compute spans support CPU contention.",
                [metrics.id, trace.id],
            )
        elif (
            "ValidationError" in logtext
            and config
            and config.payload.get("previous") != config.payload.get("current")
        ):
            category, explanation, ids = (
                "config_regression",
                "Validation errors and an incompatible configuration change support a configuration regression.",
                [logs.id, config.id],
            )
    # Deliberately flawed candidate for demonstrating an independently detected regression.
    if variant == "script-regression" and category == "pool_exhaustion":
        category, explanation, ids = (
            "inconclusive",
            "Candidate omitted the pool-pressure diagnostic rule.",
            [],
        )
    return Diagnosis(
        category=category,
        confidence="inconclusive" if category == "inconclusive" else "supported",
        explanation=explanation,
        evidence_ids=ids,
        missing=["Comparable current metrics and corroborating dependency evidence"]
        if category == "inconclusive"
        else [],
        alternatives=[
            "A nearby deployment alone does not establish causality.",
            "Other dependencies may contribute; the sampled trace is not exhaustive.",
        ],
    )
