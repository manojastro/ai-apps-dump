"""Typed tool framework with permissions, timeouts and audit logging."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.models.entities import ToolCall
from backend.app.repositories.decision_repo import AuditRepository


class ToolPermission(str, Enum):
    SAFE = "safe"
    MUTATING = "mutating"


I = TypeVar("I", bound=BaseModel)
O = TypeVar("O", bound=BaseModel)


@dataclass
class Tool:
    """A typed agent tool with permission level and timeout metadata."""

    name: str
    description: str
    permission: ToolPermission
    timeout_s: float
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: Callable[[Session, BaseModel], BaseModel]
    tags: list[str] = field(default_factory=list)

    def invoke(self, session: Session, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate input, execute the handler and persist an audit record."""
        validated_input = self.input_model.model_validate(payload)
        started = time.perf_counter()
        error: str | None = None
        output_model_dump: dict[str, Any] | None = None
        try:
            result = self.handler(session, validated_input)
            output_model_dump = jsonable(result)
            return output_model_dump
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000.0
            AuditRepository.record(
                session,
                ToolCall(
                    tool_name=self.name,
                    permission=self.permission.value,
                    input_payload=jsonable(validated_input),
                    output_payload=output_model_dump,
                    success=error is None,
                    error=error,
                    duration_ms=round(duration_ms, 3),
                ),
            )


def jsonable(value: Any) -> Any:
    """Convert pydantic models to JSON-safe dicts."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    return value


class ToolRegistry:
    """Named registry of typed tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def invoke(self, session: Session, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.get(name).invoke(session, payload)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "permission": t.permission.value,
                "timeout_s": t.timeout_s,
                "input": list(t.input_model.model_fields.keys()),
                "output": list(t.output_model.model_fields.keys()),
                "tags": t.tags,
            }
            for t in self._tools.values()
        ]

    def __contains__(self, name: str) -> bool:
        return name in self._tools
