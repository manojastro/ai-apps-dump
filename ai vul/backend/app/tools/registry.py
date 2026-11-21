"""Typed tool registry shared by agents, the assistant and the MCP server.

Every call is: allowlisted for the caller -> schema-validated -> permission-checked ->
executed -> output redacted/truncated -> recorded in ``tool_calls``. There is no generic
HTTP, shell, or SQL tool, and mutating tools only wrap approval-enforcing services.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.models.workflow import ToolCall
from app.security.auth import Principal
from app.security.permissions import Permission
from app.security.redaction import redact, truncate

log = logging.getLogger("aegis.tools")


class ToolError(Exception):
    pass


class ToolDenied(ToolError):
    pass


@dataclass
class ToolContext:
    db: Session
    principal: Principal
    caller: str
    workflow_run_id: str | None = None
    agent_execution_id: str | None = None


@dataclass
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    func: Callable[[ToolContext, Any], dict[str, Any]]
    permission: Permission = Permission.READ
    mutating: bool = False
    slow_ms: int = 15000


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"duplicate tool {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def specs(self, names: set[str] | None = None) -> list[ToolSpec]:
        return [t for n, t in sorted(self._tools.items()) if names is None or n in names]

    def describe(self, names: set[str] | None = None) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "mutating": t.mutating,
                "permission": t.permission.value,
                "input_schema": t.input_model.model_json_schema(),
            }
            for t in self.specs(names)
        ]

    def _record(
        self,
        ctx: ToolContext,
        name: str,
        mutating: bool,
        args: dict[str, Any],
        status: str,
        result: dict[str, Any] | None,
        error: str | None,
        started: float,
    ) -> None:
        ctx.db.add(
            ToolCall(
                workflow_run_id=ctx.workflow_run_id,
                agent_execution_id=ctx.agent_execution_id,
                caller=ctx.caller,
                tool_name=name,
                mutating=mutating,
                arguments=truncate(redact(args), 500),
                result_summary=truncate(redact(result or {}), 800),
                status=status,
                error=error,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
        )

    def call(self, name: str, args: dict[str, Any], ctx: ToolContext, allowed: set[str] | None) -> dict[str, Any]:
        started = time.monotonic()
        spec = self._tools.get(name)
        if spec is None or (allowed is not None and name not in allowed):
            self._record(ctx, name, bool(spec and spec.mutating), args, "denied", None, "tool not in caller allowlist", started)
            raise ToolDenied(f"Tool '{name}' is not permitted for {ctx.caller}")
        if not ctx.principal.can(spec.permission) and ctx.principal.id != "system":
            self._record(ctx, name, spec.mutating, args, "denied", None, f"missing permission {spec.permission}", started)
            raise ToolDenied(f"{ctx.principal.email} lacks '{spec.permission.value}' for tool '{name}'")
        try:
            parsed = spec.input_model.model_validate(args)
        except ValidationError as exc:
            self._record(ctx, name, spec.mutating, args, "error", None, f"invalid arguments: {exc.error_count()} errors", started)
            raise ToolError(f"Invalid arguments for {name}: {exc.errors(include_url=False)[:3]}") from exc
        try:
            result = spec.func(ctx, parsed)
        except ToolError as exc:
            self._record(ctx, name, spec.mutating, args, "error", None, str(exc)[:500], started)
            raise
        except Exception as exc:
            self._record(ctx, name, spec.mutating, args, "error", None, f"{type(exc).__name__}: {str(exc)[:400]}", started)
            raise ToolError(f"{name} failed: {type(exc).__name__}") from exc
        safe = truncate(redact(result), 4000)
        self._record(ctx, name, spec.mutating, args, "ok", safe, None, started)
        elapsed = int((time.monotonic() - started) * 1000)
        if elapsed > spec.slow_ms:
            log.warning("slow tool call", extra={"tool": name, "latency_ms": elapsed})
        return safe


registry = ToolRegistry()
