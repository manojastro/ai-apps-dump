"""Structured JSON logs with redaction, correlation IDs and OpenTelemetry-compatible tracing.

Uploaded financial content never goes into general application logs: log calls pass identifiers
and counts, and the redaction filter drops any field whose name suggests secrets or document text.
"""

from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)

REDACT_KEYS = re.compile(r"(password|secret|token|authorization|cookie|api[_-]?key|raw_text|label|text|content|payload)", re.I)
_configured = False


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:16]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": correlation_id.get(),
        }
        span = trace.get_current_span().get_span_context()
        if span.is_valid:
            data["trace_id"] = format(span.trace_id, "032x")
            data["span_id"] = format(span.span_id, "016x")
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            data.update(redact(fields))
        if record.exc_info:
            data["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(data, default=str)


def redact(fields: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in fields.items():
        out[k] = "[redacted]" if REDACT_KEYS.search(k) else v
    return out


def configure(level: str = "INFO", otlp_endpoint: str | None = None) -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel("WARNING")
    logging.getLogger("pdfminer").setLevel("ERROR")
    provider = TracerProvider(resource=Resource.create({"service.name": "spreadlens-engine"}))
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)
    _configured = True


def log(logger: logging.Logger, level: int, msg: str, **fields: Any) -> None:
    logger.log(level, msg, extra={"fields": fields})


tracer = trace.get_tracer("spreadlens")


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[Any]:
    with tracer.start_as_current_span(name) as s:
        for k, v in attrs.items():
            if v is not None and not REDACT_KEYS.search(k):
                s.set_attribute(k, v if isinstance(v, (str, int, float, bool)) else str(v))
        cid = correlation_id.get()
        if cid:
            s.set_attribute("correlation_id", cid)
        yield s
