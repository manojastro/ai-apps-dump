"""Run, pause and resume cases. One case per invoice; the case id is the LangGraph thread id.

Locally the checkpointer is SQLite (durable across process restarts, no Docker). The
LangGraph Postgres checkpointer (or Lakebase) plugs in the same way for a hosted setup.
"""

import sqlite3
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from invoiceflow.agent.graph import AgentDeps, AgentState, build_graph
from invoiceflow.data.models import Frozen


class RunOutcome(Frozen):
    case_id: str
    status: str
    interrupt: dict[str, Any] | None = None
    fail_reason: str = ""
    state: dict[str, Any]


def sqlite_checkpointer(path: Path) -> SqliteSaver:
    path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(path), check_same_thread=False))


class AgentRunner:
    def __init__(self, deps: AgentDeps, checkpointer: BaseCheckpointSaver[Any]) -> None:
        self.deps = deps
        self.graph = build_graph(deps).compile(checkpointer=checkpointer)

    @staticmethod
    def _config(case_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": case_id}}

    def _outcome(self, case_id: str, result: Any) -> RunOutcome:
        interrupts = result.get("__interrupt__") or ()
        payload = interrupts[0].value if interrupts else None
        state = {k: v for k, v in result.items() if k != "__interrupt__"}
        status = "AWAITING_APPROVAL" if payload is not None else state.get("status", "UNKNOWN")
        return RunOutcome(
            case_id=case_id,
            status=status,
            interrupt=payload,
            fail_reason=state.get("fail_reason", ""),
            state=state,
        )

    def start(self, invoice_id: str, case_id: str | None = None) -> RunOutcome:
        case_id = case_id or invoice_id
        initial = AgentState(case_id=case_id, invoice_id=invoice_id)
        return self._outcome(case_id, self.graph.invoke(initial, self._config(case_id)))

    def resume(self, case_id: str, approval: dict[str, Any]) -> RunOutcome:
        command: Command[Any] = Command(resume=approval)
        return self._outcome(case_id, self.graph.invoke(command, self._config(case_id)))

    def state(self, case_id: str) -> dict[str, Any]:
        return dict(self.graph.get_state(self._config(case_id)).values)
