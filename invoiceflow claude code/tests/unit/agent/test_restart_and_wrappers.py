"""Durable resume across real process restarts, the ResponsesAgent wrapper, and the gate."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from invoiceflow.adapters.llm.replay import RecordingChatModel, ReplayChatModel
from invoiceflow.adapters.llm.stub import StubChatModel
from invoiceflow.agent.responses_agent import InvoiceFlowResponsesAgent
from invoiceflow.agent.runner import AgentRunner, sqlite_checkpointer
from invoiceflow.agent.wiring import build_deps
from invoiceflow.config import Settings
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.models import Action, ExceptionCode, Split
from invoiceflow.evals.agent_eval import citations_ok, is_unsafe, summarize_agent
from invoiceflow.evals.gate import check_gate, reference_from
from invoiceflow.ports.llm import LLMError, Message

ROOT = Path(__file__).resolve().parents[3]


def cli(*args: str, state_dir: Path) -> dict[str, Any]:
    env = {
        **os.environ,
        "LLM_PROVIDER": "stub",
        "INVOICEFLOW_KILL_SWITCH": "false",
        "MLFLOW_DISABLE_AGENT_HINT": "1",
    }
    result = subprocess.run(  # noqa: S603 - our own CLI with fixed arguments
        [sys.executable, "-m", "invoiceflow.cli", *args, "--state-dir", str(state_dir)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=300,
    )
    return dict(json.loads(result.stdout))


def test_case_resumes_in_a_new_process_after_restart(tmp_path: Path, dataset: Dataset) -> None:
    invoice_id = next(
        label.invoice_id
        for label in dataset.labels(Split.DEV)
        if label.scenario == "duplicate_exact"
    )
    first = cli("agent", "run", invoice_id, state_dir=tmp_path)  # process 1 pauses and exits
    assert first["status"] == "AWAITING_APPROVAL"
    second = cli(
        "agent",
        "approve",
        invoice_id,
        "--approver-id",
        "u-clerk-1",
        "--role",
        "AP_MANAGER",
        state_dir=tmp_path,
    )  # process 2 loads the checkpoint
    assert second["status"] == "EXECUTED"
    status = cli("agent", "status", invoice_id, state_dir=tmp_path)
    assert status["status"] == "EXECUTED"


def test_responses_agent_wraps_the_graph(tmp_path: Path, dataset: Dataset) -> None:
    from mlflow.types.responses import ResponsesAgentRequest

    deps = build_deps(Settings(_env_file=None), tmp_path, dataset, StubChatModel())
    deps.kill_switch = lambda: False
    agent = InvoiceFlowResponsesAgent(AgentRunner(deps, sqlite_checkpointer(tmp_path / "c.db")))
    invoice_id = next(
        label.invoice_id for label in dataset.labels(Split.DEV) if label.scenario == "missing_grn"
    )
    request = ResponsesAgentRequest(input=[{"role": "user", "content": f"Resolve {invoice_id}"}])
    response = agent.predict(request)
    assert response.custom_outputs is not None
    assert response.custom_outputs["status"] == "EXECUTED"
    assert invoice_id in response.output[0].model_dump_json()
    empty = agent.predict(ResponsesAgentRequest(input=[{"role": "user", "content": "hello"}]))
    assert empty.custom_outputs is not None
    assert empty.custom_outputs["status"] == "NO_INVOICE"


def test_replay_returns_recorded_responses_and_never_guesses(tmp_path: Path) -> None:
    path = tmp_path / "rec.jsonl"
    messages = [Message(role="user", content="CASE_CONTEXT ```json\n{}\n```")]
    recorded = RecordingChatModel(StubChatModel(), path).complete(messages, json_schema={"a": 1})
    replay = ReplayChatModel(path)
    assert replay.complete(messages, json_schema={"a": 1}) == recorded
    with pytest.raises(LLMError, match="no recorded response"):
        replay.complete([Message(role="user", content="different")])


def test_unsafe_and_citation_scoring() -> None:
    assert is_unsafe(Action.REQUEST_CREDIT_NOTE, Action.APPROVE, "AWAITING_APPROVAL")
    assert not is_unsafe(Action.REQUEST_CREDIT_NOTE, Action.APPROVE, "MANUAL_QUEUE")
    assert is_unsafe(Action.ESCALATE_FRAUD_REVIEW, Action.REJECT_DUPLICATE, "AWAITING_APPROVAL")
    assert citations_ok(ExceptionCode.PRICE_VARIANCE, ["CT-V011:§2.2", "AP-POL:§4.4"]) is True
    assert citations_ok(ExceptionCode.PRICE_VARIANCE, ["AP-POL:§8.1"]) is False
    assert citations_ok(ExceptionCode.CLEAN, []) is None


def test_gate_fails_on_regression_and_on_any_executed_violation() -> None:
    from invoiceflow.evals.scoring import Rate

    good = summarize_agent([], 0)
    reference = reference_from(good)
    assert check_gate(good, reference).passed
    worse = good.model_copy(update={"exception": Rate(correct=90, total=100)})
    ref = {**reference, "exception_pct": "99.0"}
    assert not check_gate(worse, ref).passed
    leaked = good.model_copy(update={"executed_violations": 1})
    assert not check_gate(leaked, reference).passed
