"""Assemble an agent from configuration. Local: in-memory data, local retriever, SQLite
stores under INVOICEFLOW_STATE_DIR. Databricks: Unity Catalog reader, AI Search retriever."""

from pathlib import Path

from invoiceflow.adapters.erp import InProcessERP
from invoiceflow.adapters.llm import build_chat_model
from invoiceflow.agent.cases import CaseStore
from invoiceflow.agent.graph import AgentDeps, Budget
from invoiceflow.agent.runner import AgentRunner, sqlite_checkpointer
from invoiceflow.audit.chain import AuditLog
from invoiceflow.backends import DOCS_DIR, data_reader, workspace_client
from invoiceflow.config import Settings
from invoiceflow.data.dataset import Dataset
from invoiceflow.policy.matrix import load_matrix
from invoiceflow.ports.llm import ChatModel
from invoiceflow.ports.retrieval import Retriever
from invoiceflow.retrieval.chunking import load_chunks
from invoiceflow.retrieval.local import LocalHybridRetriever
from invoiceflow.services.erp_sandbox.store import ErpStore
from invoiceflow.tools.drafts import DraftStore
from invoiceflow.tools.executor import Executor


def build_retriever(settings: Settings) -> Retriever:
    if settings.invoiceflow_backend == "databricks" and settings.ai_search_index:
        from invoiceflow.adapters.databricks.retrieval import AISearchRetriever, SdkIndex

        return AISearchRetriever(SdkIndex(workspace_client(settings), settings.ai_search_index))
    return LocalHybridRetriever(load_chunks(DOCS_DIR))


def build_deps(
    settings: Settings,
    state_dir: Path | None = None,
    dataset: Dataset | None = None,
    llm: ChatModel | None = None,
) -> AgentDeps:
    root = state_dir or Path(settings.invoiceflow_state_dir)
    return AgentDeps(
        reader=data_reader(settings, dataset),
        retriever=build_retriever(settings),
        llm=llm or build_chat_model(settings),
        matrix=load_matrix(),
        executor=Executor(InProcessERP(ErpStore(root / "erp_sandbox.db"))),
        audit=AuditLog(root / "audit.db"),
        cases=CaseStore(root / "cases.db"),
        drafts=DraftStore(root / "drafts.db"),
        evidence_dir=root / "evidence",
        budget=Budget(
            max_tool_steps=settings.agent_max_tool_steps,
            max_tokens=settings.agent_max_tokens,
            max_seconds=settings.agent_max_seconds,
            max_tool_retries=settings.agent_max_tool_retries,
        ),
        # Re-read on every case: flipping INVOICEFLOW_KILL_SWITCH needs no redeploy.
        kill_switch=lambda: Settings().invoiceflow_kill_switch,
    )


def build_runner(
    settings: Settings,
    state_dir: Path | None = None,
    dataset: Dataset | None = None,
    llm: ChatModel | None = None,
) -> AgentRunner:
    root = state_dir or Path(settings.invoiceflow_state_dir)
    deps = build_deps(settings, root, dataset, llm)
    return AgentRunner(deps, sqlite_checkpointer(root / "checkpoints.db"))
