"""Agent runtime: tracing, tool access, LLM access and execution boundaries.

Each agent is a plain class with a typed ``Output`` model, an explicit tool allowlist, and a
``run(ctx, state)`` method. ``execute_agent`` wraps it to persist an ``AgentExecution`` row,
emit workflow events, account for tokens/cost, and validate the output schema.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.db import session_scope
from app.core.types import utcnow
from app.llm.base import LLMProvider, LLMValidationError, StructuredTask, T
from app.llm.factory import build_provider
from app.models.enums import AgentStatus
from app.models.workflow import AgentExecution, WorkflowEvent, WorkflowRun
from app.observability.logging import workflow_id_var
from app.security.auth import Principal
from app.security.redaction import redact, truncate
from app.tools import catalog as _catalog  # noqa: F401  (registers tools)
from app.tools.registry import ToolContext, registry

log = logging.getLogger("aegis.agents")

# Agents act under a dedicated read-only service identity: they can never invoke mutating tools.
AGENT_PRINCIPAL = Principal("agent-runtime", "agents@aegis.local", "Aegis Agent Runtime", "viewer", ["read"])


class AgentFailure(Exception):
    """Non-retryable agent failure (bad input, schema violation)."""


@dataclass
class AgentContext:
    db: Session
    run_id: str
    execution: AgentExecution
    agent_name: str
    allowed_tools: set[str]
    provider: LLMProvider | None = None
    llm_calls: list[dict[str, Any]] = field(default_factory=list)

    def tool(self, name: str, **args: Any) -> dict[str, Any]:
        ctx = ToolContext(self.db, AGENT_PRINCIPAL, self.agent_name, self.run_id, self.execution.id)
        return registry.call(name, args, ctx, self.allowed_tools)

    def llm(self, task: StructuredTask[T]) -> T:
        provider = self.provider or build_provider()
        result = provider.generate(task)
        u = result.usage
        ex = self.execution
        ex.model_provider, ex.model_name = u.provider, u.model
        if u.prompt_tokens is not None:
            ex.prompt_tokens = (ex.prompt_tokens or 0) + u.prompt_tokens
            ex.completion_tokens = (ex.completion_tokens or 0) + (u.completion_tokens or 0)
        if u.estimated_cost_usd is not None:
            ex.estimated_cost_usd = (ex.estimated_cost_usd or 0) + u.estimated_cost_usd
        if u.validation_errors:
            ex.validation_errors = [*(ex.validation_errors or []), *u.validation_errors]
        self.llm_calls.append(
            {
                "task": task.name,
                "provider": u.provider,
                "model": u.model,
                "attempts": u.attempts,
                "latency_ms": u.latency_ms,
                "prompt_tokens": u.prompt_tokens,
                "completion_tokens": u.completion_tokens,
            }
        )
        return result.output

    def event(self, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
        emit_event(self.db, self.run_id, event_type, message, self.execution.node_name, payload)


class Agent:
    name: ClassVar[str]
    node: ClassVar[str]
    description: ClassVar[str]
    tools: ClassVar[set[str]] = set()
    boundary: ClassVar[str] = "Read-only analysis; no external writes."
    retry: ClassVar[str] = "Up to 3 attempts with exponential backoff on transient errors."
    evaluation: ClassVar[list[str]] = []
    uses_llm: ClassVar[bool] = False
    Output: ClassVar[type[BaseModel]]

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> BaseModel:  # pragma: no cover - interface
        raise NotImplementedError

    @classmethod
    def describe(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "node": cls.node,
            "description": cls.description,
            "tools": sorted(cls.tools),
            "boundary": cls.boundary,
            "retry_policy": cls.retry,
            "uses_llm": cls.uses_llm,
            "evaluation_criteria": cls.evaluation,
            "output_schema": cls.Output.model_json_schema() if hasattr(cls, "Output") else None,
        }


def emit_event(
    db: Session, run_id: str, event_type: str, message: str, node: str | None = None, payload: dict[str, Any] | None = None
) -> None:
    db.add(
        WorkflowEvent(
            workflow_run_id=run_id,
            event_type=event_type,
            node=node,
            message=message,
            payload=truncate(redact(payload or {}), 2000),
        )
    )


def _summarize_input(state: dict[str, Any]) -> dict[str, Any]:
    keys = ("finding_id", "plan_id", "approval_request_id", "route")
    out: dict[str, Any] = {k: state.get(k) for k in keys if state.get(k) is not None}
    out["available_context"] = sorted(k for k, v in state.items() if v is not None and k not in keys)
    return out


def execute_agent(agent: Agent, run_id: str, state: dict[str, Any], provider: LLMProvider | None = None) -> dict[str, Any]:
    """Run one agent inside its own transaction with full tracing. Raises on failure (for retries)."""
    workflow_id_var.set(run_id)
    started = time.monotonic()
    with session_scope() as db:
        attempt = 1 + sum(
            1
            for _ in db.query(AgentExecution.id).filter(
                AgentExecution.workflow_run_id == run_id,
                AgentExecution.node_name == agent.node,
                AgentExecution.status == AgentStatus.FAILED,
            )
        )
        execution = AgentExecution(
            workflow_run_id=run_id,
            agent_name=agent.name,
            node_name=agent.node,
            status=AgentStatus.RUNNING,
            attempt=attempt,
            input_summary=_summarize_input(state),
            started_at=utcnow(),
        )
        db.add(execution)
        run = db.get(WorkflowRun, run_id)
        if run is not None:
            run.current_node = agent.node
            run.status = "running"
            run.waiting_reason = None
        emit_event(db, run_id, "agent_started", f"{agent.name} started", agent.node, {"attempt": attempt})
    exec_id = execution.id

    try:
        with session_scope() as db:
            found = db.get(AgentExecution, exec_id)
            assert found is not None
            execution = found
            ctx = AgentContext(db, run_id, execution, agent.name, agent.tools, provider)
            output = agent.run(ctx, state)
            try:
                validated = agent.Output.model_validate(output.model_dump())
            except ValidationError as exc:  # pragma: no cover - agents return typed models
                raise AgentFailure(f"{agent.name} produced invalid output: {exc}") from exc
            data = validated.model_dump(mode="json")
            execution.status = AgentStatus.COMPLETED
            execution.output = truncate(redact(data | ({"llm_calls": ctx.llm_calls} if ctx.llm_calls else {})), 3000)
            execution.completed_at = utcnow()
            execution.latency_ms = int((time.monotonic() - started) * 1000)
            run = db.get(WorkflowRun, run_id)
            if run is not None:
                run.prompt_tokens += execution.prompt_tokens or 0
                run.completion_tokens += execution.completion_tokens or 0
                if execution.estimated_cost_usd is not None:
                    run.estimated_cost_usd = (run.estimated_cost_usd or 0) + execution.estimated_cost_usd
                if execution.model_name:
                    run.model = execution.model_name
            emit_event(
                db,
                run_id,
                "agent_completed",
                f"{agent.name} completed",
                agent.node,
                {"latency_ms": execution.latency_ms, "summary": _headline(data)},
            )
            return data
    except Exception as exc:
        with session_scope() as db:
            failed = db.get(AgentExecution, exec_id)
            if failed is not None:
                failed.status = AgentStatus.FAILED
                failed.error = f"{type(exc).__name__}: {str(exc)[:1500]}"
                failed.completed_at = utcnow()
                failed.latency_ms = int((time.monotonic() - started) * 1000)
                if isinstance(exc, LLMValidationError):
                    failed.validation_errors = exc.errors
            emit_event(
                db, run_id, "agent_failed", f"{agent.name} failed: {type(exc).__name__}", agent.node, {"error": str(exc)[:500]}
            )
        log.exception("agent failed", extra={"agent": agent.name, "run_id": run_id})
        raise


def _headline(data: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "status",
        "risk_score",
        "risk_level",
        "priority",
        "known_exploited",
        "epss_probability",
        "cve_id",
        "hostname",
        "data_quality",
        "route",
        "plan_id",
        "verification_state",
        "records",
        "affected_services",
    )
    return {k: data[k] for k in keys if k in data}
