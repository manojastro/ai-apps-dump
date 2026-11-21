"""Structured JSON logging (one run_id per run) and OpenTelemetry spans per agent node."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

run_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("run_id", default=None)
node_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("node", default=None)

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "run_id": run_id_var.get(),
            "node": node_var.get(),
        }
        for k, v in record.__dict__.items():
            if k not in _RESERVED and not k.startswith("_"):
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured = False


def configure_logging(level: str = "INFO", otel_console: bool = False) -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("schemaguard")
    root.handlers[:] = [handler]
    root.setLevel(level)
    root.propagate = False
    if otel_console:
        _provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)
    _configured = True


def add_span_processor(processor: SpanProcessor) -> None:
    """Attach an extra exporter (e.g. OTLP in Azure, or in-memory in tests)."""
    _provider.add_span_processor(processor)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"schemaguard.{name}")


_provider = TracerProvider()
tracer = _provider.get_tracer("schemaguard")
log = get_logger("agent")


@contextmanager
def run_context(run_id: str) -> Iterator[None]:
    token = run_id_var.set(run_id)
    try:
        yield
    finally:
        run_id_var.reset(token)


def instrument_node(
    name: str, fn: Callable[[dict[str, Any]], dict[str, Any]]
) -> Callable[[dict[str, Any]], Any]:
    """Wrap a LangGraph node: JSON log line with duration/tokens/cost, plus an OTel span."""

    def wrapper(state: dict[str, Any]) -> Any:
        run_id = state.get("run_id") or run_id_var.get()
        rid_token = run_id_var.set(run_id)
        node_token = node_var.set(name)
        before = dict(state.get("cost_tracking") or {})
        start = time.perf_counter()
        status = "ok"
        after: dict[str, Any] = before
        try:
            with tracer.start_as_current_span(f"node.{name}") as span:
                span.set_attribute("schemaguard.run_id", str(run_id))
                span.set_attribute("schemaguard.node", name)
                try:
                    result = fn(state)
                    if isinstance(result, dict) and isinstance(result.get("cost_tracking"), dict):
                        after = result["cost_tracking"]
                    return result
                except Exception as exc:
                    # GraphInterrupt (human approval) is control flow, not an error.
                    if type(exc).__name__ in {"GraphInterrupt", "ParentCommand"}:
                        status = "interrupted"
                    else:
                        status = "error"
                        span.record_exception(exc)
                    raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info(
                "node finished",
                extra={
                    "event": "node_end",
                    "status": status,
                    "duration_ms": duration_ms,
                    "tokens": (after.get("tokens_in", 0) + after.get("tokens_out", 0))
                    - (before.get("tokens_in", 0) + before.get("tokens_out", 0)),
                    "cost_usd": round(after.get("usd", 0.0) - before.get("usd", 0.0), 6),
                },
            )
            node_var.reset(node_token)
            run_id_var.reset(rid_token)

    wrapper.__name__ = name
    return wrapper
