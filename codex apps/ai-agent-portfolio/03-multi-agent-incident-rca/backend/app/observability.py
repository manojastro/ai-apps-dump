from __future__ import annotations

from contextlib import nullcontext


def request_span(name: str):
    """Return an OpenTelemetry span when the SDK/API is installed, otherwise a safe no-op."""

    try:
        from opentelemetry import trace

        return trace.get_tracer("multi-agent-incident-rca").start_as_current_span(name)
    except ImportError:
        return nullcontext()

