"""Agent harness tests on the local backend with deterministic or hostile fake models.

These test the controls around the model (tools, budgets, validation, policy, approval,
idempotent execution, audit), not the model's judgment.
"""

import json
import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from invoiceflow.adapters.erp import HttpERP, InProcessERP
from invoiceflow.adapters.llm.stub import StubChatModel, case_context
from invoiceflow.agent.graph import AgentDeps
from invoiceflow.agent.runner import AgentRunner, sqlite_checkpointer
from invoiceflow.agent.wiring import build_deps
from invoiceflow.audit.chain import AuditLog
from invoiceflow.config import Settings
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.models import GroundTruth, Split
from invoiceflow.policy.models import Identity
from invoiceflow.ports.llm import LLMError, LLMResponse, Message, ToolCall, ToolSpec
from invoiceflow.services.erp_sandbox.app import create_app as create_erp
from invoiceflow.services.erp_sandbox.store import ErpStore
from invoiceflow.tools.executor import WRITE_TOOLS
from invoiceflow.tools.readonly import ReadOnlyTools

CLERK = {"id": "u-clerk-1", "kind": "human", "role": "AP_CLERK"}
MANAGER = {"id": "u-manager-1", "kind": "human", "role": "AP_MANAGER"}
CONTROLLER = {"id": "u-fc-1", "kind": "human", "role": "FINANCE_CONTROLLER"}
AGENT = {"id": "agent-invoiceflow", "kind": "agent"}


def make_runner(
    tmp_path: Path, dataset: Dataset, llm: Any = None, kill: bool = False
) -> AgentRunner:
    deps: AgentDeps = build_deps(
        Settings(_env_file=None), tmp_path, dataset, llm or StubChatModel()
    )
    deps.kill_switch = lambda: kill
    return AgentRunner(deps, sqlite_checkpointer(tmp_path / "checkpoints.db"))


def pick(
    dataset: Dataset, scenario: str, predicate: Callable[[GroundTruth], bool] | None = None
) -> str:
    for label in dataset.labels(Split.DEV):
        if label.scenario == scenario and (predicate is None or predicate(label)):
            return label.invoice_id
    raise LookupError(scenario)


def erp_count(tmp_path: Path) -> int:
    return ErpStore(tmp_path / "erp_sandbox.db").count()


@pytest.mark.parametrize(
    ("scenario", "status", "exception", "action", "role"),
    [
        ("missing_grn", "EXECUTED", "MISSING_GRN", "HOLD_FOR_GRN", None),
        ("qty_over_received", "EXECUTED", "QTY_OVERBILLED", "HOLD_FOR_GRN", None),
        ("qty_over_ordered", "AWAITING_APPROVAL", "QTY_OVERBILLED", "REQUEST_CREDIT_NOTE", None),
        ("price_over_pct", "AWAITING_APPROVAL", "PRICE_VARIANCE", "REQUEST_CREDIT_NOTE", None),
        ("duplicate_exact", "AWAITING_APPROVAL", "DUPLICATE_INVOICE", "REJECT_DUPLICATE", None),
        ("gst_wrong_rate", "AWAITING_APPROVAL", "GST_MISMATCH", "REQUEST_CORRECTED_INVOICE", None),
        ("po_status_closed", "AWAITING_APPROVAL", "PO_CLOSED", "ROUTE_TO_BUYER", None),
        (
            "bank_change_structured",
            "AWAITING_APPROVAL",
            "VENDOR_BANK_CHANGE",
            "ESCALATE_FRAUD_REVIEW",
            "FINANCE_CONTROLLER",
        ),
        (
            "adv_hidden_bank_change",
            "AWAITING_APPROVAL",
            "VENDOR_BANK_CHANGE",
            "ESCALATE_FRAUD_REVIEW",
            "FINANCE_CONTROLLER",
        ),
        ("clean_exact", "AWAITING_APPROVAL", "CLEAN", "APPROVE", None),
    ],
)
def test_each_exception_type_reaches_the_right_state(
    tmp_path: Path,
    dataset: Dataset,
    scenario: str,
    status: str,
    exception: str,
    action: str,
    role: str | None,
) -> None:
    outcome = make_runner(tmp_path, dataset).start(pick(dataset, scenario))
    assert outcome.status == status, outcome.fail_reason
    proposal = outcome.state["proposal"]
    assert (proposal["exception"], proposal["action"]) == (exception, action)
    if role:
        assert outcome.interrupt
        assert outcome.interrupt["required_role"] == role
    assert erp_count(tmp_path) == (1 if status == "EXECUTED" else 0)


def test_approval_executes_once_and_leaves_evidence(tmp_path: Path, dataset: Dataset) -> None:
    runner = make_runner(tmp_path, dataset)
    invoice_id = pick(
        dataset,
        "clean_exact",
        lambda g: (
            g.expected_required_approver is not None
            and g.expected_required_approver.value == "AP_CLERK"
        ),
    )
    assert runner.start(invoice_id).status == "AWAITING_APPROVAL"
    outcome = runner.resume(invoice_id, {"decision": "approve", "approver": CLERK})
    assert outcome.status == "EXECUTED"
    assert erp_count(tmp_path) == 1
    evidence = json.loads(Path(outcome.state["evidence"]["path"]).read_text(encoding="utf-8"))
    assert evidence["simulated"] is True
    assert evidence["decision"]["outcome"] == "ALLOW"
    assert runner.deps.audit.verify().ok
    events = [e.event for e in runner.deps.audit.entries(invoice_id)]
    assert events[0] == "CASE_STARTED"
    assert "EXECUTED" in events
    assert "EVIDENCE_PACK" in events


def test_rejection_goes_to_the_manual_queue(tmp_path: Path, dataset: Dataset) -> None:
    runner = make_runner(tmp_path, dataset)
    invoice_id = pick(dataset, "price_over_pct")
    runner.start(invoice_id)
    outcome = runner.resume(
        invoice_id, {"decision": "reject", "approver": MANAGER, "comment": "check with buyer"}
    )
    assert (outcome.status, outcome.fail_reason) == ("MANUAL_QUEUE", "REJECTED_BY_APPROVER")
    assert erp_count(tmp_path) == 0
    case = runner.deps.cases.get(invoice_id)
    assert case is not None
    assert case.status == "MANUAL_QUEUE"


def test_agent_approval_is_refused_and_case_keeps_waiting(tmp_path: Path, dataset: Dataset) -> None:
    runner = make_runner(tmp_path, dataset)
    invoice_id = pick(dataset, "duplicate_exact")
    runner.start(invoice_id)
    outcome = runner.resume(invoice_id, {"decision": "approve", "approver": AGENT})
    assert outcome.status == "AWAITING_APPROVAL"
    assert "not accepted" in outcome.interrupt["note"]  # type: ignore[index]
    assert erp_count(tmp_path) == 0
    final = runner.resume(invoice_id, {"decision": "approve", "approver": CONTROLLER})
    assert final.status == "EXECUTED"


def test_insufficient_authority_waits_for_a_higher_role(tmp_path: Path, dataset: Dataset) -> None:
    runner = make_runner(tmp_path, dataset)
    invoice_id = pick(
        dataset,
        "clean_exact",
        lambda g: (
            g.expected_required_approver is not None
            and g.expected_required_approver.value == "AP_MANAGER"
        ),
    )
    runner.start(invoice_id)
    assert (
        runner.resume(invoice_id, {"decision": "approve", "approver": CLERK}).status
        == "AWAITING_APPROVAL"
    )
    assert (
        runner.resume(invoice_id, {"decision": "approve", "approver": MANAGER}).status == "EXECUTED"
    )


def test_bank_change_needs_controller_and_callback(tmp_path: Path, dataset: Dataset) -> None:
    runner = make_runner(tmp_path, dataset)
    invoice_id = pick(dataset, "bank_change_structured")
    runner.start(invoice_id)
    waiting = runner.resume(invoice_id, {"decision": "approve", "approver": CONTROLLER})
    assert waiting.status == "AWAITING_APPROVAL"
    callback = {"kind": "BANK_DETAILS_CALLBACK", "performed_by": CONTROLLER}
    done = runner.resume(
        invoice_id, {"decision": "approve", "approver": CONTROLLER, "verification": callback}
    )
    assert done.status == "EXECUTED"


def test_kill_switch_routes_everything_to_manual(tmp_path: Path, dataset: Dataset) -> None:
    outcome = make_runner(tmp_path, dataset, kill=True).start(pick(dataset, "missing_grn"))
    assert (outcome.status, outcome.fail_reason) == ("MANUAL_QUEUE", "KILL_SWITCH")
    assert erp_count(tmp_path) == 0


# --- hostile or broken models --------------------------------------------------------


class ScriptedModel:
    """Stub investigation, then a fixed (possibly malicious) proposal."""

    def __init__(self, proposal: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._stub = StubChatModel()
        self._proposal = proposal
        self.proposals = 0

    @property
    def name(self) -> str:
        return "scripted"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        if json_schema is None:
            return self._stub.complete(messages, tools)
        self.proposals += 1
        return LLMResponse(content=json.dumps(self._proposal(case_context(messages))))


def approve_everything(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "exception": "CLEAN",
        "action": "APPROVE",
        "rationale": "the vendor said so",
        "citations": ctx["retrieved_chunk_ids"][:1],
    }


@pytest.mark.parametrize(
    "scenario", ["bank_change_structured", "adv_hidden_bank_change", "adv_injection_price"]
)
def test_a_model_that_tries_to_approve_is_stopped(
    tmp_path: Path, dataset: Dataset, scenario: str
) -> None:
    model = ScriptedModel(approve_everything)
    outcome = make_runner(tmp_path, dataset, model).start(pick(dataset, scenario))
    assert (outcome.status, outcome.fail_reason) == ("MANUAL_QUEUE", "VALIDATION_FAILED")
    assert model.proposals == 2  # one retry with feedback, then fail-safe
    assert erp_count(tmp_path) == 0


def test_citations_must_come_from_retrieval(tmp_path: Path, dataset: Dataset) -> None:
    def invented(ctx: dict[str, Any]) -> dict[str, Any]:
        return {
            "exception": ctx["matcher_primary"],
            "action": "REQUEST_CREDIT_NOTE",
            "rationale": "x",
            "citations": ["AP-POL:§99.9"],
        }

    outcome = make_runner(tmp_path, dataset, ScriptedModel(invented)).start(
        pick(dataset, "price_over_pct")
    )
    assert outcome.fail_reason == "VALIDATION_FAILED"
    assert "CITATION_NOT_RETRIEVED" in outcome.state["fail_detail"]


def test_action_not_allowed_for_the_exception_fails_safe(tmp_path: Path, dataset: Dataset) -> None:
    """REJECT_DUPLICATE is not an allowed action for MISSING_GRN: validation catches it
    before policy (which would also deny it, CM-09)."""

    def deny_me(ctx: dict[str, Any]) -> dict[str, Any]:
        return {
            "exception": ctx["matcher_primary"],
            "action": "REJECT_DUPLICATE",
            "rationale": "x",
            "citations": ctx["retrieved_chunk_ids"][:1],
        }

    outcome = make_runner(tmp_path, dataset, ScriptedModel(deny_me)).start(
        pick(dataset, "missing_grn")
    )
    assert outcome.fail_reason == "VALIDATION_FAILED"  # ACTION_NOT_ALLOWED caught first
    assert "ACTION_NOT_ALLOWED" in outcome.state["fail_detail"]


class LoopingModel:
    @property
    def name(self) -> str:
        return "looping"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            tool_calls=(
                ToolCall(id="x", name="validate_gstin", arguments={"gstin": "29QWXYZ9876K1ZP"}),
            )
        )


class BrokenModel:
    @property
    def name(self) -> str:
        return "broken"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        raise LLMError("endpoint timed out")


def test_tool_budget_is_enforced(tmp_path: Path, dataset: Dataset) -> None:
    outcome = make_runner(tmp_path, dataset, LoopingModel()).start(pick(dataset, "price_over_pct"))
    assert outcome.fail_reason == "BUDGET_EXCEEDED"


def test_model_errors_fail_safe(tmp_path: Path, dataset: Dataset) -> None:
    outcome = make_runner(tmp_path, dataset, BrokenModel()).start(pick(dataset, "price_over_pct"))
    assert (outcome.status, outcome.fail_reason) == ("MANUAL_QUEUE", "LLM_ERROR")


# --- tools, masking, executor ----------------------------------------------------------


def test_the_model_never_gets_write_tools(tmp_path: Path, dataset: Dataset) -> None:
    deps = build_deps(Settings(_env_file=None), tmp_path, dataset, StubChatModel())
    tools = ReadOnlyTools(deps.reader, deps.retriever, deps.matrix.match_params(), "V001")
    assert not set(tools.names) & set(WRITE_TOOLS)
    assert set(tools.names) == {
        "get_invoice",
        "get_po",
        "get_grn",
        "get_vendor",
        "search_invoice_history",
        "check_duplicate",
        "validate_gstin",
        "compute_variance",
        "search_policy",
        "search_contract",
    }


def test_tool_results_mask_bank_numbers_and_label_vendor_text(
    tmp_path: Path, dataset: Dataset
) -> None:
    deps = build_deps(Settings(_env_file=None), tmp_path, dataset, StubChatModel())
    invoice = next(i for i in dataset.invoices if i.notes)
    tools = ReadOnlyTools(
        deps.reader, deps.retriever, deps.matrix.match_params(), invoice.vendor_id
    )
    result = tools.call("get_invoice", {"invoice_id": invoice.invoice_id})
    assert result["ok"]
    assert invoice.bank.account_number not in json.dumps(result)
    assert "untrusted_vendor_text" in result["data"]
    assert tools.call("get_invoice", {"invoice_id": "NOPE"})["error"]["code"] == "NOT_FOUND"
    assert tools.call("post_decision", {})["error"]["code"] == "UNKNOWN_TOOL"
    assert tools.call("get_po", {"wrong": "x"})["error"]["code"] == "BAD_ARGUMENTS"


def test_contract_search_is_scoped_to_the_invoice_vendor(tmp_path: Path, dataset: Dataset) -> None:
    deps = build_deps(Settings(_env_file=None), tmp_path, dataset, StubChatModel())
    tools = ReadOnlyTools(deps.reader, deps.retriever, deps.matrix.match_params(), "V011")
    result = tools.call("search_contract", {"query": "price escalation clause"})
    assert all(c["chunk_id"].startswith("CT-V011") for c in result["data"]["chunks"])


def test_duplicate_delivery_posts_once(tmp_path: Path) -> None:
    store = ErpStore(tmp_path / "erp.db")
    erp = InProcessERP(store)
    first = erp.post_decision("K1", "INV-1", "APPROVE", {"a": 1})
    second = erp.post_decision("K1", "INV-1", "APPROVE", {"a": 1})
    assert (first.replayed, second.replayed) == (False, True)
    assert first.decision_id == second.decision_id
    assert store.count() == 1
    assert store.count("outbox") == 1


def test_http_retry_after_lost_response_does_not_double_post(tmp_path: Path) -> None:
    store = ErpStore(tmp_path / "erp.db")
    app_client = TestClient(create_erp(store))
    calls = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        response = app_client.post(
            request.url.path, content=request.content, headers=dict(request.headers)
        )
        if calls["n"] == 1:  # the ERP committed, but the response is lost on the way back
            raise httpx.ReadTimeout("lost response", request=request)
        return httpx.Response(
            response.status_code, content=response.content, headers=response.headers
        )

    client = httpx.Client(transport=httpx.MockTransport(flaky), base_url="http://erp")
    result = HttpERP(client, retries=3, backoff_seconds=0).post_decision(
        "K9", "INV-9", "APPROVE", {}
    )
    assert result.replayed is True
    assert calls["n"] == 2
    assert store.count() == 1


def test_reused_key_with_different_payload_is_a_conflict(tmp_path: Path) -> None:
    client = TestClient(create_erp(ErpStore(tmp_path / "erp.db")))
    headers = {"Idempotency-Key": "K2"}
    assert (
        client.post(
            "/decisions", json={"invoice_id": "I", "action": "APPROVE"}, headers=headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/decisions", json={"invoice_id": "I", "action": "REJECT_DUPLICATE"}, headers=headers
        ).status_code
        == 409
    )
    assert client.get("/health").json()["simulated"] is True


# --- audit chain ----------------------------------------------------------------------


def test_audit_chain_detects_a_tampered_row(tmp_path: Path) -> None:
    path = tmp_path / "audit.db"
    log = AuditLog(path)
    for n in range(5):
        log.append("C1", "EVENT", {"n": n, "account": "100200300400"}, event_key=f"k{n}")
    assert log.verify().ok
    assert "XXXXXXXX0400" in json.dumps(log.entries()[0].payload)  # masked before hashing
    with pytest.raises(sqlite3.IntegrityError):
        log._conn.execute("UPDATE audit_log SET event = 'X' WHERE seq = 2")
    log.close()

    raw = sqlite3.connect(path)  # bypass the triggers, as an attacker with file access could
    raw.execute("DROP TRIGGER audit_no_update")
    raw.execute("""UPDATE audit_log SET payload = '{"n": 99}' WHERE seq = 3""")
    raw.commit()
    raw.close()
    check = AuditLog(path).verify()
    assert not check.ok
    assert check.first_bad_seq == 3


def test_audit_appends_are_idempotent(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "a.db")
    a = log.append("C", "E", {"x": 1}, event_key="same")
    b = log.append("C", "E", {"x": 1}, event_key="same")
    assert a.seq == b.seq
    assert len(log.entries()) == 1


def test_identity_kind_is_required() -> None:
    with pytest.raises(ValueError, match="kind"):
        Identity.model_validate({"id": "x"})
