"""OpenTelemetry tracing. Spans: event.process, workflow.step, agent.run, tool.call.

Export targets: Arize Phoenix via OTLP/HTTP when PHOENIX_COLLECTOR_ENDPOINT is set (docker compose does),
plus an in-memory exporter that tests and evals can read.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_provider: TracerProvider | None = None
memory_exporter = InMemorySpanExporter()


def setup_tracing() -> TracerProvider:
    global _provider
    if _provider is not None:
        return _provider
    _provider = TracerProvider(resource=Resource.create({"service.name": "eir-agent-fleet"}))
    _provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        _provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(_provider)
    return _provider


@contextmanager
def span(name: str, attributes: dict | None = None) -> Iterator[trace.Span]:
    setup_tracing()
    tracer = trace.get_tracer("eir")
    with tracer.start_as_current_span(name) as sp:
        for k, v in (attributes or {}).items():
            sp.set_attribute(k, v if isinstance(v, (str, int, float, bool)) else str(v))
        yield sp


def finished_spans() -> list:
    return list(memory_exporter.get_finished_spans())


def clear_spans() -> None:
    memory_exporter.clear()
