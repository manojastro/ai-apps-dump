from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def parse_structured(raw: Any, model: type[T]) -> tuple[T | None, str | None]:
    """Validate agent output. One structured repair, then mark failure. Never regex-parse finances."""
    payload = raw
    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                try:
                    payload = json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    return None, "malformed_json"
            else:
                return None, "malformed_json"
    try:
        return model.model_validate(payload), None
    except ValidationError:
        if isinstance(payload, dict):
            try:
                return model.model_validate(payload), None
            except ValidationError:
                return None, "schema_mismatch"
        return None, "schema_mismatch"
