"""Read-only, bounded adapters. Destinations are server configuration, never tool input."""

import json
import math
import os
import re
import time

import httpx

from packages.agent.contracts import Evidence
from packages.connectors.replay import TOOLS, ConnectorError


def bounded_get(base, path, params=None):
    if not base:
        raise ConnectorError("SOURCE_NOT_CONFIGURED")
    for attempt in range(3):
        try:
            with httpx.Client(timeout=8, follow_redirects=False, trust_env=False) as client:
                with client.stream("GET", base.rstrip("/") + path, params=params) as response:
                    if response.status_code != 200:
                        raise ConnectorError(f"SOURCE_HTTP_{response.status_code}")
                    data = b""
                    for part in response.iter_bytes():
                        data += part
                        if len(data) > 32768:
                            raise ConnectorError("SOURCE_RESPONSE_TOO_LARGE")
                    return json.loads(data)
        except httpx.TimeoutException:
            if attempt == 2:
                raise ConnectorError("TIMEOUT") from None
            time.sleep(0.1 * 2**attempt)
        except (httpx.HTTPError, json.JSONDecodeError):
            raise ConnectorError("CONNECTION_OR_MALFORMED_RESPONSE") from None


class LiveConnector:
    def call(self, tool, run_id, parameters=None):
        parameters = parameters or {}
        if tool not in TOOLS or set(parameters) - {"service", "trace_id"}:
            raise ConnectorError("TOOL_SCOPE_DENIED")
        service = parameters.get("service", "checkout")
        if service not in {"checkout", "payment", "inventory"}:
            raise ConnectorError("SERVICE_SCOPE_DENIED")
        now = time.time()
        if tool == "query_metrics":
            # Fixed 2-minute window and a baseline 5 minutes earlier; no generated PromQL.
            templates = {
                "samples": f'sum(increase(demo_requests_total{{service="{service}"}}[2m]))',
                "error_rate": f'sum(rate(demo_errors_total{{service="{service}"}}[2m])) / clamp_min(sum(rate(demo_requests_total{{service="{service}"}}[2m])), 0.001)',
                "p95_ms": f'histogram_quantile(0.95, sum by (le) (rate(demo_duration_seconds_bucket{{service="{service}"}}[2m]))) * 1000',
                "cpu": f'max(demo_cpu_ratio{{service="{service}"}})',
                "pool_usage": 'max(demo_pool_usage{service="checkout"})',
                "pool_wait_ms": 'max(demo_pool_wait_seconds{service="checkout"}) * 1000',
            }
            payload = {}
            for key, query in templates.items():
                response = bounded_get(
                    os.environ.get("PROMETHEUS_URL"),
                    "/api/v1/query",
                    {"query": query, "timeout": "5s", "limit": 10},
                )
                try:
                    result = response["data"]["result"]
                    value = float(result[0]["value"][1])
                    if not math.isfinite(value):
                        raise ValueError()
                    payload[key] = value
                except (KeyError, IndexError, ValueError, TypeError):
                    raise ConnectorError("METRICS_EMPTY_OR_MALFORMED") from None
            baseline_query = templates["p95_ms"].replace("[2m]", "[2m] offset 5m")
            payload["baseline"] = bounded_get(
                os.environ.get("PROMETHEUS_URL"),
                "/api/v1/query",
                {"query": baseline_query, "timeout": "5s", "limit": 10},
            )
            source, summary, record = (
                "metrics",
                "Live Prometheus metrics, fixed two-minute scope",
                "prometheus/query",
            )
        elif tool in {"search_traces", "get_trace"}:
            trace = parameters.get("trace_id", "")
            if tool == "get_trace" and not re.fullmatch("[0-9a-f]{16,32}", trace):
                raise ConnectorError("TRACE_ID_INVALID")
            path = f"/api/traces/{trace}" if tool == "get_trace" else "/api/traces"
            payload = bounded_get(
                os.environ.get("JAEGER_URL"),
                path,
                {"service": service, "limit": 5, "start": int((now - 120) * 1e6), "end": int(now * 1e6)},
            )
            source, summary, record = "traces", "Live Jaeger trace observations", "jaeger" + path
        else:
            paths = {
                "search_logs": "/telemetry/logs",
                "get_deployments": "/telemetry/deployments",
                "compare_config": "/telemetry/config",
                "get_service_dependencies": "/telemetry/dependencies",
                "search_runbooks": "/telemetry/runbooks",
            }
            source = {
                "search_logs": "logs",
                "get_deployments": "deployments",
                "compare_config": "config",
                "get_service_dependencies": "dependencies",
                "search_runbooks": "runbooks",
            }[tool]
            payload = bounded_get(os.environ.get("DEMO_TELEMETRY_URL"), paths[tool])
            summary, record = "Live local demo " + source, "demo" + paths[tool]
        if not isinstance(payload, dict):
            raise ConnectorError("MALFORMED_RESPONSE")
        return Evidence.make(
            run_id, source, payload, summary, service=service, query=parameters, source_record_id=record
        )
