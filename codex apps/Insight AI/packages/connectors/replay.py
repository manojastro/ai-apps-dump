"""Synthetic, versioned telemetry. No scenario labels are passed into the agent."""

import copy
import time

from packages.agent.contracts import Evidence

TOOLS = {
    "query_metrics": "Compare checkout error rate, p95 latency, CPU and pool pressure to a healthy baseline",
    "search_traces": "Find representative checkout dependency spans",
    "get_trace": "Read a previously returned trace",
    "search_logs": "Search bounded structured service logs",
    "get_deployments": "Read deployment and configuration change history",
    "compare_config": "Compare previous and current checkout configuration",
    "get_service_dependencies": "Read the checkout dependency graph",
    "search_runbooks": "Find read-only demo recovery guidance",
}


def snapshot(family="payment_delay"):
    now = time.time()
    data = {
        "version": "telemetry-v1",
        "observed_at": now,
        "metrics": {
            "samples": 240,
            "error_rate": 0.003,
            "p95_ms": 140,
            "payment_ms": 70,
            "pool_usage": 0.3,
            "pool_wait_ms": 2,
            "cpu": 0.24,
            "baseline": {"samples": 240, "error_rate": 0.003, "p95_ms": 140},
        },
        "traces": {
            "trace_id": "replay-trace-001",
            "checkout_ms": 130,
            "payment_ms": 70,
            "inventory_ms": 22,
            "status": "ok",
        },
        "logs": {
            "records": [
                {
                    "service": "checkout",
                    "severity": "INFO",
                    "message": "Order accepted",
                    "trace_id": "replay-trace-001",
                    "span_id": "span-001",
                    "timestamp": now,
                }
            ]
        },
        "deployments": {
            "records": [
                {
                    "service": "checkout",
                    "revision": "checkout-042",
                    "timestamp": now - 1800,
                    "change": "Request handling update",
                }
            ]
        },
        "config": {
            "previous": {"validation": "v1", "pool_size": 10},
            "current": {"validation": "v1", "pool_size": 10},
        },
        "dependencies": {"checkout": ["payment", "inventory", "demo-db"]},
        "runbooks": {
            "text": "Collect metrics and independent traces or logs before proposing a demo environment reset. Human review is required."
        },
    }
    if family == "payment_delay":
        data["metrics"].update(error_rate=0.284, p95_ms=2450, payment_ms=2300)
        data["traces"].update(checkout_ms=2510, payment_ms=2300, status="deadline_exceeded")
        data["logs"]["records"][0].update(severity="ERROR", message="Payment upstream deadline exceeded")
    elif family == "config_regression":
        data["metrics"].update(error_rate=0.42, p95_ms=430)
        data["logs"]["records"][0].update(
            severity="ERROR", message="ValidationError: incompatible request schema"
        )
        data["config"]["current"]["validation"] = "v2"
        data["traces"].update(status="validation_error", checkout_ms=410)
        data["deployments"]["records"][0]["timestamp"] = now - 120
    elif family == "pool_exhaustion":
        data["metrics"].update(error_rate=0.22, p95_ms=1880, pool_usage=1, pool_wait_ms=1600)
        data["logs"]["records"][0].update(
            severity="ERROR", message="PoolTimeout: connection acquisition exceeded 1500ms"
        )
        data["traces"].update(status="db_wait", checkout_ms=1840)
    elif family == "cpu_saturation":
        data["metrics"].update(error_rate=0.14, p95_ms=970, cpu=0.98)
        data["traces"].update(status="compute_slow", checkout_ms=940, compute_ms=840)
        data["logs"]["records"][0].update(severity="WARN", message="Event loop lag above 800ms")
    elif family == "missing_evidence":
        data["metrics"].update(error_rate=0.18, p95_ms=810)
        data["traces"] = {"unavailable": True}
        data["logs"] = {"unavailable": True}
    elif family != "healthy":
        raise ValueError("Unknown replay fixture")
    return data


class ConnectorError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class ReplayConnector:
    def __init__(self, packet: dict):
        self.packet = copy.deepcopy(packet)

    def call(self, tool: str, run_id: str, parameters: dict | None = None) -> Evidence:
        parameters = parameters or {}
        if tool not in TOOLS or set(parameters) - {"service", "trace_id"}:
            raise ConnectorError("TOOL_SCOPE_DENIED")
        if parameters.get("service", "checkout") not in {"checkout", "payment", "inventory"}:
            raise ConnectorError("SERVICE_SCOPE_DENIED")
        source = {
            "query_metrics": "metrics",
            "search_traces": "traces",
            "get_trace": "traces",
            "search_logs": "logs",
            "get_deployments": "deployments",
            "compare_config": "config",
            "get_service_dependencies": "dependencies",
            "search_runbooks": "runbooks",
        }[tool]
        payload = self.packet.get(source, {"unavailable": True})
        if not isinstance(payload, dict):
            raise ConnectorError("MALFORMED_RESPONSE")
        if payload.get("error"):
            raise ConnectorError(payload["error"])
        if payload.get("unavailable"):
            raise ConnectorError("SOURCE_UNAVAILABLE")
        summary = {
            "metrics": f"Checkout: {payload.get('samples', 0)} requests; {payload.get('error_rate', 0):.1%} errors; p95 {payload.get('p95_ms', 0)}ms",
            "traces": f"Representative trace: {payload.get('status', 'unknown')}",
            "logs": f"{len(payload.get('records', []))} structured log records",
            "deployments": f"{len(payload.get('records', []))} deployment events; correlation alone is not a diagnosis",
            "config": "Previous and current demo configuration",
            "dependencies": "Checkout calls payment, inventory and demo-db",
            "runbooks": "Read-only recovery procedure",
        }[source]
        observed = self.packet.get("observed_at", time.time())
        return Evidence.make(
            run_id,
            source,
            payload,
            summary,
            query=parameters,
            observed_at=observed,
            stale=time.time() - observed > 3600 or bool(payload.get("stale")),
            truncated=bool(payload.get("truncated")),
        )
