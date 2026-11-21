"""Optional OpenTelemetry tracing. A no-op unless OTEL_EXPORTER_OTLP_ENDPOINT is configured.

Span attributes carry identifiers and statuses only; page content, credentials and addresses are
never attached.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .config import get_settings

_tracer = None


def setup(service_name: str, app: Any | None = None) -> bool:
    global _tracer
    endpoint = get_settings().otel_exporter_otlp_endpoint
    if not endpoint:
        return False
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces")))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("procnav")
    if app is not None:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, excluded_urls="api/health")
    return True


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    if _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name) as s:
        for k, v in attributes.items():
            if v is not None:
                s.set_attribute(k, str(v))
        yield s
