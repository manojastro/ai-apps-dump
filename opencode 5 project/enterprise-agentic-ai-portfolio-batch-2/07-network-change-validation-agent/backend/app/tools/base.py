"""Typed tool framework with permissions, timeouts, schema validation and audit."""
from __future__ import annotations

import threading
import time
from typing import Any, ClassVar

from pydantic import BaseModel

from app.db import session_scope
from app.models.entities import AuditEvent
from app.repositories.repo import AuditRepository
from app.services.metrics import METRICS


class ToolPermission:
    SAFE = "safe"
    MUTATING = "mutating"


class ToolError(RuntimeError):
    pass


class ToolApprovalRequired(ToolError):
    pass


class BaseTool:
    name: ClassVar[str]
    description: ClassVar[str]
    permission: ClassVar[str] = ToolPermission.SAFE
    timeout_s: ClassVar[float] = 30.0

    def input_model(self) -> type[BaseModel]:
        raise NotImplementedError

    def output_model(self) -> type[BaseModel]:
        raise NotImplementedError

    def execute(self, validated_input: BaseModel) -> BaseModel:
        raise NotImplementedError

    def run(self, raw_input: dict[str, Any], change_id: int | None = None,
            approved: bool = False) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            model = self.input_model()
            payload = model.model_validate(raw_input)
            if self.permission == ToolPermission.MUTATING and not approved:
                raise ToolApprovalRequired(
                    f"tool {self.name} is mutating and requires approval gate"
                )
            result: dict[str, Any] | None = None
            error_holder: list[BaseException] = []

            def target() -> None:
                nonlocal result
                try:
                    result = self.execute(payload).model_dump()
                except BaseException as exc:
                    error_holder.append(exc)

            worker = threading.Thread(target=target, daemon=True)
            worker.start()
            worker.join(timeout=self.timeout_s)
            if worker.is_alive():
                raise ToolError(f"tool {self.name} exceeded timeout {self.timeout_s}s")
            if error_holder:
                raise error_holder[0]
            assert result is not None
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._audit(raw_input, result, True, duration_ms, None, change_id)
            METRICS.incr("tool_calls_total", {"tool": self.name})
            return result
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._audit(raw_input, {}, False, duration_ms, str(exc), change_id)
            METRICS.incr("tool_calls_total", {"tool": self.name, "error": "true"})
            raise

    def _audit(self, tool_input: Any, output: Any, ok: bool, duration_ms: int,
               error: str | None, change_id: int | None) -> None:
        with session_scope() as session:
            AuditRepository(session).tool_call(
                tool=self.name,
                permission=self.permission,
                input_json=tool_input if isinstance(tool_input, dict) else {},
                output_json=output if isinstance(output, dict) else {},
                ok=ok,
                duration_ms=duration_ms,
                error=error,
                change_id=change_id,
            )


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ToolError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ToolError(f"unknown tool: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> list[dict[str, str]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "permission": t.permission,
                "timeout_s": str(t.timeout_s),
            }
            for t in self._tools.values()
        ]


REGISTRY = ToolRegistry()
