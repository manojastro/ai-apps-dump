import json
import logging
from logging import LogRecord

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class JsonLogFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        return json.dumps(
            {
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "incident_id": getattr(record, "incident_id", None),
                "node": getattr(record, "node", None),
                "kind": getattr(record, "kind", None),
            }
        )


def configure_telemetry(endpoint: str | None):
    logger = logging.getLogger("recoverygraph")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    # Configure once per process; tests may enter multiple app lifespans.
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        provider = TracerProvider(resource=Resource.create({"service.name": "recoverygraph"}))
        if endpoint:
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces"))
            )
        trace.set_tracer_provider(provider)
