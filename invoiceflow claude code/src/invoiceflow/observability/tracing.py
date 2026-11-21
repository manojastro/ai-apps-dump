"""MLflow tracing for agent steps, off unless MLFLOW_TRACING=true.

Span inputs and outputs pass through `mask` so bank numbers never reach a trace. When
tracing is off, `span` is a no-op, so tests and CI need no tracking server.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from invoiceflow.observability.masking import mask


def tracing_enabled() -> bool:
    return os.environ.get("MLFLOW_TRACING", "").lower() in {"1", "true", "yes"}


@contextmanager
def span(name: str, inputs: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Yields a dict; whatever the caller puts in it becomes the span's outputs."""
    outputs: dict[str, Any] = {}
    if not tracing_enabled():
        yield outputs
        return
    import mlflow

    with mlflow.start_span(name=name) as active:
        if inputs:
            active.set_inputs(mask(inputs))
        yield outputs
        active.set_outputs(mask(outputs))
