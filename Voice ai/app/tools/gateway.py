"""The single choke point for every tool call: RBAC -> validate -> idempotency -> scope -> run -> filter -> audit.

Security lives here, not in prompts. Denied calls are audited too.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ValidationError
from sqlalchemy import select

from app import clock
from app.audit import log as audit
from app.data.db import session
from app.data.models import IdempotencyRecord
from app.obs.tracing import span
from app.rbac import policy
from app.tools.base import REGISTRY, ScopeViolation, ToolContext, ToolError


class ToolResult(BaseModel):
    status: Literal["ok", "denied", "error"]
    data: dict | None = None
    error: str | None = None
    replayed: bool = False


def _patient_of(args: dict, data: dict | None) -> str | None:
    pid = args.get("patient_id")
    if not pid and data:
        pid = data.get("patient_id")
    return pid if isinstance(pid, str) else None


def call_tool(role: str, tool_name: str, args: dict | None, *, workflow_id: str | None = None,
              patient_scope: str | None = None) -> ToolResult:
    args = dict(args or {})
    with span("tool.call", {"tool": tool_name, "role": role, "workflow_id": workflow_id or ""}) as sp:
        result = _call(role, tool_name, args, workflow_id, patient_scope)
        sp.set_attribute("status", result.status)
    return result


def _call(role: str, tool_name: str, args: dict, workflow_id: str | None, patient_scope: str | None) -> ToolResult:
    actor = role

    def done(res: ToolResult, status: str | None = None, detail: str = "") -> ToolResult:
        audit.write(actor=actor, tool=tool_name, args=args, status=status or res.status,
                    patient_id=_patient_of(args, res.data), workflow_id=workflow_id,
                    detail=detail or (res.error or ""))
        return res

    spec = REGISTRY.get(tool_name)
    if spec is None:
        return done(ToolResult(status="denied", error=f"unknown tool '{tool_name}'"))
    if not policy.is_allowed(role, tool_name):
        return done(ToolResult(status="denied", error=f"role '{role}' is not allowed to call '{tool_name}'"))
    try:
        parsed = spec.input_model.model_validate(args)
    except ValidationError as exc:
        return done(ToolResult(status="error", error=f"invalid arguments: {exc.errors()[0]['msg']}"))

    key = getattr(parsed, "idempotency_key", None) if spec.mutating else None
    if spec.mutating and not key:
        return done(ToolResult(status="error", error="idempotency_key is required for state-changing tools"))

    try:
        with session() as s:
            if key:
                prior = s.scalar(select(IdempotencyRecord).where(IdempotencyRecord.tool == tool_name,
                                                                 IdempotencyRecord.key == key))
                if prior is not None:
                    return done(ToolResult(status="ok", data=prior.result, replayed=True), status="replayed",
                                detail="idempotent replay")
            ctx = ToolContext(session=s, role=role, workflow_id=workflow_id, patient_scope=patient_scope)
            out = spec.fn(ctx, parsed)
            data = out.model_dump(mode="json")
            if key:
                s.add(IdempotencyRecord(tool=tool_name, key=key, result=data, created_at=clock.now()))
            s.flush()
    except ScopeViolation as exc:
        return done(ToolResult(status="denied", error=str(exc)))
    except ToolError as exc:
        return done(ToolResult(status="error", error=str(exc)))
    except Exception as exc:  # noqa: BLE001 - e.g. unique-key race on idempotency record
        if key:  # a concurrent identical call may have won the race: replay its stored result
            with session() as s:
                prior = s.scalar(select(IdempotencyRecord).where(IdempotencyRecord.tool == tool_name,
                                                                 IdempotencyRecord.key == key))
                if prior is not None:
                    return done(ToolResult(status="ok", data=prior.result, replayed=True), status="replayed")
        return done(ToolResult(status="error", error=f"{type(exc).__name__}: {exc}"))

    data = policy.filter_fields(tool_name, role, data)
    return done(ToolResult(status="ok", data=data))
