"""OpenTelemetry tracing, exported to a local Arize Phoenix instance when configured.

Phoenix accepts standard OTLP over HTTP at <endpoint>/v1/traces. When
PHOENIX_COLLECTOR_ENDPOINT is unset, tracing stays a no-op (zero overhead, no network), which
is what tests and MOCK runs use. LLM spans use OpenInference attribute names so Phoenix shows
them as LLM calls with inputs, outputs and token counts.
"""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.trace import Tracer, TracerProvider

log = logging.getLogger(__name__)
_provider: TracerProvider | None = None
_configured = False


def setup_tracing(endpoint: str | None, project_name: str = "truthkeeper") -> bool:
    """Configure OTLP export once. Returns True if an exporter was installed."""
    global _provider, _configured
    if _configured or not endpoint:
        return False
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": project_name, "openinference.project.name": project_name})
    provider = SDKTracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces")))
    _provider = provider
    _configured = True
    log.info("tracing enabled -> %s", endpoint)
    return True


def use_provider(provider: TracerProvider | None) -> None:
    """Swap the provider (tests use an in-memory exporter)."""
    global _provider
    _provider = provider


def get_tracer() -> Tracer:
    if _provider is not None:
        return _provider.get_tracer("truthkeeper")
    return trace.get_tracer("truthkeeper")
