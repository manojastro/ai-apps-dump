from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from langgraph.errors import GraphInterrupt
from opentelemetry import trace

from app.adapters.protocols import (
    KnowledgeAdapter,
    PipelineAdapter,
    SandboxAdapter,
    SourceControlAdapter,
)
from app.graph.state import RecoveryState
from app.llm.providers import Provider
from app.models.domain import now
from app.verifier.independent import IndependentVerifier

EventSink = Callable[[str, str, str, dict[str, Any]], Awaitable[None]]


async def no_events(incident_id: str, kind: str, node: str, payload: dict[str, Any]) -> None:
    return None


@dataclass
class Runtime:
    pipeline: PipelineAdapter
    sandbox: SandboxAdapter
    source_control: SourceControlAdapter
    knowledge: KnowledgeAdapter
    provider: Provider
    verifier: IndependentVerifier
    event: EventSink = no_events

    def node(self, name: str, call: Callable[[RecoveryState], Awaitable[RecoveryState]]):
        async def measured(state: RecoveryState) -> RecoveryState:
            started, timestamp = perf_counter(), now()
            await self.event(state["incident_id"], "node_started", name, {})
            with trace.get_tracer("recoverygraph").start_as_current_span(name) as span:
                span.set_attributes(
                    {
                        "incident_id": state["incident_id"],
                        "node_name": name,
                        "pipeline_id": state["incident"].pipeline_id,
                        "attempt_number": state["attempt_number"],
                    }
                )
                try:
                    update = await call(state)
                except GraphInterrupt:
                    await self.event(state["incident_id"], "node_waiting", name, {})
                    raise
                except Exception as error:
                    span.set_status(trace.StatusCode.ERROR, type(error).__name__)
                    await self.event(
                        state["incident_id"],
                        "node_failed",
                        name,
                        {"error_type": type(error).__name__},
                    )
                    raise
                duration = perf_counter() - started
                event = {
                    "node": name,
                    "started_at": timestamp,
                    "ended_at": now(),
                    "duration_seconds": duration,
                    "attempt": update.get("attempt_number", state["attempt_number"]),
                }
                span.set_attribute("duration_seconds", duration)
                await self.event(state["incident_id"], "node_completed", name, event)
                update["latency_metrics"] = [event]
                update["audit_events"] = [{"kind": "node_completed", **event}]
                return update

        return measured
