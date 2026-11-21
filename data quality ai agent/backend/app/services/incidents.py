import asyncio
import logging
from typing import Any

from langgraph.types import Command

from app.config import Settings
from app.db.repository import Repository
from app.graph.state import RecoveryState
from app.graph.workflow import build_graph, initial_state
from app.llm.online import StructuredProvider
from app.llm.providers import DeterministicProvider
from app.models.domain import Approval, Incident, Status
from app.rag.retrieval import HybridKnowledge

logger = logging.getLogger("recoverygraph.workflow")


class ConflictError(ValueError):
    pass


class IncidentService:
    def __init__(
        self, settings: Settings, repository: Repository, saver, knowledge: HybridKnowledge
    ):
        self.settings, self.repository, self.saver, self.knowledge = (
            settings,
            repository,
            saver,
            knowledge,
        )
        self.tasks: dict[str, asyncio.Task] = {}
        self.guard = asyncio.Lock()
        self.capacity = asyncio.Semaphore(4)

    def config(self, incident_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": incident_id}, "recursion_limit": 128}

    async def event(self, incident_id, kind, node, payload):
        await asyncio.to_thread(self.repository.event, incident_id, kind, node, payload)
        logger.info(
            "workflow_event", extra={"incident_id": incident_id, "kind": kind, "node": node}
        )

    async def snapshot(self, incident_id: str):
        graph = build_graph(self.saver)
        return await graph.aget_state(self.config(incident_id))

    async def start(self, incident_id: str, decision: Approval | None = None, wait: bool = False):
        async with self.guard:
            if incident_id in self.tasks:
                raise ConflictError("This incident is already running")
            row = await asyncio.to_thread(self.repository.get, incident_id)
            snapshot = await self.snapshot(incident_id)
            if decision is not None:
                if not any(task.interrupts for task in snapshot.tasks):
                    raise ConflictError("This incident has no pending human decision")
            elif any(task.interrupts for task in snapshot.tasks):
                raise ConflictError("Resume this incident through approve or reject")
            elif row["status"] != Status.CREATED and not snapshot.next:
                raise ConflictError("This incident has already terminated; create a new incident")
            await asyncio.to_thread(self.repository.status, incident_id, Status.RUNNING)
            task = asyncio.create_task(self.execute(incident_id, row, snapshot, decision))
            self.tasks[incident_id] = task
            task.add_done_callback(lambda _: self.tasks.pop(incident_id, None))
        if wait:
            await task
        return await asyncio.to_thread(self.repository.get, incident_id)

    async def execute(self, incident_id, row, snapshot, decision):
        provider = (
            DeterministicProvider()
            if self.settings.llm_provider == "mock"
            else (StructuredProvider(self.settings))
        )
        try:
            async with self.capacity:
                graph = build_graph(
                    self.saver, provider=provider, knowledge=self.knowledge, event=self.event
                )
                graph_input: Command | RecoveryState | None
                if decision:
                    graph_input = Command(resume=decision.model_dump())
                    await self.event(
                        incident_id, "human_decision", "approval", decision.model_dump()
                    )
                elif snapshot.values:
                    graph_input = None
                else:
                    graph_input = initial_state(
                        Incident.model_validate(row["input"]),
                        self.settings.max_remediation_attempts,
                        self.settings.demo_force_first_fix_fail,
                    )
                async for state in graph.astream(
                    graph_input, self.config(incident_id), stream_mode="values"
                ):
                    await asyncio.to_thread(self.repository.project, state)
                final = await graph.aget_state(self.config(incident_id))
                if any(task.interrupts for task in final.tasks):
                    await asyncio.to_thread(self.repository.status, incident_id, Status.WAITING)
                    await self.event(incident_id, "workflow_waiting", "approval", {})
                else:
                    await self.event(
                        incident_id,
                        "workflow_finished",
                        "workflow",
                        {"status": final.values.get("final_status", Status.FAILED)},
                    )
        except asyncio.CancelledError:
            await self.event(incident_id, "workflow_interrupted", "workflow", {})
            raise
        except Exception as error:
            reason = f"Workflow stopped safely: {type(error).__name__}"
            logger.error(reason, extra={"incident_id": incident_id}, exc_info=True)
            await asyncio.to_thread(self.repository.status, incident_id, Status.FAILED, reason)
            await self.event(
                incident_id, "workflow_failed", "workflow", {"error_type": type(error).__name__}
            )
        finally:
            if isinstance(provider, StructuredProvider):
                await provider.close()

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
