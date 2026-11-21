"""The InvoiceFlow agent as a LangGraph state machine.

intake -> deterministic_match -> screen_text
  CLEAN, no vendor text  -> propose_default (deterministic)  -> validate
  otherwise              -> investigate (bounded tool loop) -> retrieve -> propose -> validate
validate -> policy_authorize
  ALLOW            -> execute -> record (audit, evidence pack, email draft) -> END
  REQUIRE_APPROVAL -> await_approval (interrupt) -> apply_approval -> execute | await_approval
  DENY             -> fail_safe
any failure        -> fail_safe (manual queue, with a reason) -> END

Design rules:
- The LLM only sees read-only tools (tools/readonly.py). Only `execute` writes, and only
  through the Executor, which calls `require_allow` first.
- `await_approval` contains nothing but `interrupt()`: LangGraph re-runs a node from the
  top on resume, so side effects there would repeat.
- Every other side effect is idempotent (audit event keys, ERP idempotency keys, drafts).
- State holds ids and JSON only. Raw invoices (with full bank numbers) are re-read from the
  data port, never stored in checkpoints.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from invoiceflow.agent.cases import CaseStore
from invoiceflow.agent.prompts import (
    INVESTIGATE_INSTRUCTION,
    PROPOSE_INSTRUCTION,
    SYSTEM_PROMPT,
    case_message,
)
from invoiceflow.agent.proposal import proposal_schema, validate_proposal
from invoiceflow.agent.text_screen import free_text, screen
from invoiceflow.audit.chain import AuditLog
from invoiceflow.audit.evidence import write_evidence_pack
from invoiceflow.core.findings import Finding
from invoiceflow.core.matcher import MatchInputError, match_invoice
from invoiceflow.core.tolerance import PriceVariance
from invoiceflow.data.models import Action, ExceptionCode, Frozen
from invoiceflow.observability.tracing import span
from invoiceflow.policy.evaluator import evaluate
from invoiceflow.policy.matrix import ControlMatrix
from invoiceflow.policy.models import (
    Approval,
    Identity,
    Outcome,
    PolicyDecision,
    Proposal,
    Verification,
)
from invoiceflow.ports.data import APDataReader, NotFoundError
from invoiceflow.ports.erp import ErpConflictError, ErpUnavailableError
from invoiceflow.ports.llm import ChatModel, LLMError, Message
from invoiceflow.ports.retrieval import Retriever
from invoiceflow.retrieval.models import AccessScope
from invoiceflow.tools.drafts import DraftStore, draft_vendor_email
from invoiceflow.tools.executor import Executor
from invoiceflow.tools.readonly import ReadOnlyTools

AGENT_IDENTITY = Identity(id="agent-invoiceflow", kind="agent")
MAX_PROPOSE_ATTEMPTS = 2
MAX_APPROVAL_ROUNDS = 5

POLICY_QUERIES = {
    ExceptionCode.CLEAN: "invoice matches purchase order and goods receipt approve payment",
    ExceptionCode.PRICE_VARIANCE: "price above tolerance credit note contract escalation clause",
    ExceptionCode.QTY_OVERBILLED: "quantity billed more than received or ordered",
    ExceptionCode.MISSING_GRN: "no goods receipt hold invoice",
    ExceptionCode.DUPLICATE_INVOICE: "duplicate invoice rejected confirmation",
    ExceptionCode.GST_MISMATCH: "invalid GSTIN wrong tax type GST rate corrected invoice",
    ExceptionCode.PO_CLOSED: "closed or expired purchase order route to buyer",
    ExceptionCode.VENDOR_BANK_CHANGE: "vendor bank change fraud review verification call-back",
}


class Budget(Frozen):
    max_tool_steps: int = 12
    max_tokens: int = 60000
    max_seconds: float = 120.0
    max_tool_retries: int = 2


@dataclass
class AgentDeps:
    reader: APDataReader
    retriever: Retriever
    llm: ChatModel
    matrix: ControlMatrix
    executor: Executor
    audit: AuditLog
    cases: CaseStore
    drafts: DraftStore
    evidence_dir: Path
    budget: Budget
    kill_switch: Callable[[], bool]
    preparer: Identity = AGENT_IDENTITY


class AgentState(TypedDict, total=False):
    case_id: str
    invoice_id: str
    status: str
    started_at: float
    match: dict[str, Any]
    text_signals: list[str]
    has_free_text: bool
    messages: list[dict[str, Any]]
    tool_steps: int
    tool_errors: int
    tool_error_counts: dict[str, int]
    llm_calls: int
    tokens_in: int
    tokens_out: int
    retrieved: dict[str, dict[str, Any]]
    proposal: dict[str, Any] | None
    proposal_source: str
    issues: list[dict[str, Any]]
    propose_attempts: int
    decision: dict[str, Any] | None
    approvals: list[dict[str, Any]]
    verifications: list[dict[str, Any]]
    approval_rounds: int
    approval_note: str
    resume: dict[str, Any] | None
    execution: dict[str, Any] | None
    evidence: dict[str, Any] | None
    draft: dict[str, Any] | None
    fail_reason: str
    fail_detail: str


def _fail(reason: str, detail: str) -> dict[str, Any]:
    return {"fail_reason": reason, "fail_detail": detail[:1000]}


def build_graph(deps: AgentDeps) -> StateGraph[AgentState]:
    matrix = deps.matrix
    params = matrix.match_params()

    def audit(state: AgentState, event: str, payload: dict[str, Any], n: int | str = 0) -> None:
        case_id = state["case_id"]
        deps.audit.append(case_id, event, payload, event_key=f"{case_id}:{event}:{n}")

    def proposal_obj(state: AgentState) -> Proposal:
        p, inv = state["proposal"] or {}, deps.reader.get_invoice(state["invoice_id"])
        return Proposal(
            invoice_id=inv.invoice_id,
            exception=ExceptionCode(p["exception"]),
            action=Action(p["action"]),
            gross_value=inv.gross_total,
            price_variance=PriceVariance.model_validate(state["match"]["price_variance"]),
            citations=tuple(p.get("citations", ())),
            preparer=deps.preparer,
        )

    # -- nodes ------------------------------------------------------------------------

    def intake(state: AgentState) -> dict[str, Any]:
        with span("intake", {"invoice_id": state["invoice_id"]}):
            if deps.kill_switch():
                return _fail("KILL_SWITCH", "automation is paused; route to manual processing")
            try:
                invoice = deps.reader.get_invoice(state["invoice_id"])
            except NotFoundError as exc:
                return _fail("NOT_FOUND", str(exc))
            deps.cases.upsert(state["case_id"], invoice.invoice_id, "RUNNING", deps.preparer.id)
            audit(state, "CASE_STARTED", {"invoice_id": invoice.invoice_id, "model": deps.llm.name})
            return {
                "status": "RUNNING",
                "started_at": time.time(),
                "fail_reason": "",
                "tool_steps": 0,
                "tool_errors": 0,
                "tool_error_counts": {},
                "llm_calls": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "retrieved": {},
                "messages": [],
                "propose_attempts": 0,
                "approvals": [],
                "verifications": [],
                "approval_rounds": 0,
                "issues": [],
            }

    def deterministic_match(state: AgentState) -> dict[str, Any]:
        with span("deterministic_match") as out:
            r = deps.reader
            try:
                invoice = r.get_invoice(state["invoice_id"])
                result = match_invoice(
                    invoice,
                    r.get_purchase_order(invoice.po_id),
                    r.get_goods_receipts(invoice.po_id),
                    r.get_vendor(invoice.vendor_id),
                    r.prior_invoices(invoice),
                    params,
                )
            except (MatchInputError, NotFoundError) as exc:
                return _fail("MATCH_INPUT_ERROR", str(exc))
            match = result.model_dump(mode="json")
            out["primary"] = match["primary"]
            audit(
                state,
                "MATCHED",
                {"primary": match["primary"], "reasons": [f["reason"] for f in match["findings"]]},
            )
            return {"match": match}

    def screen_text(state: AgentState) -> dict[str, Any]:
        invoice = deps.reader.get_invoice(state["invoice_id"])
        po = deps.reader.get_purchase_order(invoice.po_id)
        signals = screen(invoice)
        if signals:
            audit(state, "TEXT_SIGNALS", {"signals": signals})
        # Vendor text = notes, remarks, or a line description that differs from the PO's own.
        rewritten = any(
            (po_line := po.line(line.po_line_no)) is None or line.description != po_line.description
            for line in invoice.lines
        )
        has_text = bool(invoice.notes.strip() or invoice.remarks.strip()) or rewritten
        return {"text_signals": signals, "has_free_text": has_text and bool(free_text(invoice))}

    def _context(state: AgentState) -> dict[str, Any]:
        invoice = deps.reader.get_invoice(state["invoice_id"])
        primary = ExceptionCode(state["match"]["primary"])
        findings = tuple(Finding.model_validate(f) for f in state["match"]["findings"])
        return {
            "invoice_id": invoice.invoice_id,
            "po_id": invoice.po_id,
            "vendor_id": invoice.vendor_id,
            "matcher_primary": primary.value,
            "matcher_findings": [
                {"code": f["code"], "reason": f["reason"], "message": f["message"]}
                for f in state["match"]["findings"]
            ],
            "price_variance": state["match"]["price_variance"],
            "text_signals": state.get("text_signals", []),
            "allowed_actions": {
                c.value: [a.value for a in p.allowed_actions] for c, p in matrix.exceptions.items()
            },
            # Defaults depend on the findings (e.g. over-ordered quantity -> credit note).
            "default_actions": {
                c.value: matrix.default_action(c, findings).value for c in matrix.exceptions
            },
            "policy_query": POLICY_QUERIES[primary],
            "retrieved_chunk_ids": list(state.get("retrieved", {})),  # retrieval order
        }

    def investigate(state: AgentState) -> dict[str, Any]:
        invoice = deps.reader.get_invoice(state["invoice_id"])
        tools = ReadOnlyTools(deps.reader, deps.retriever, params, invoice.vendor_id)
        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=case_message(_context(state), INVESTIGATE_INSTRUCTION)),
        ]
        steps, errors = state.get("tool_steps", 0), state.get("tool_errors", 0)
        error_counts = dict(state.get("tool_error_counts", {}))
        tokens_in, tokens_out = state.get("tokens_in", 0), state.get("tokens_out", 0)
        llm_calls = state.get("llm_calls", 0)
        budget, started = deps.budget, state.get("started_at", time.time())
        with span("investigate", {"invoice_id": invoice.invoice_id}) as out:
            while True:
                if time.time() - started > budget.max_seconds:
                    return _fail("BUDGET_EXCEEDED", f"wall clock over {budget.max_seconds}s")
                try:
                    response = deps.llm.complete(messages, tools.specs())
                except LLMError as exc:
                    return _fail("LLM_ERROR", str(exc))
                llm_calls += 1
                tokens_in += response.usage.input_tokens
                tokens_out += response.usage.output_tokens
                if tokens_in + tokens_out > budget.max_tokens:
                    return _fail("BUDGET_EXCEEDED", f"token budget {budget.max_tokens} exceeded")
                messages.append(
                    Message(
                        role="assistant", content=response.content, tool_calls=response.tool_calls
                    )
                )
                if not response.tool_calls:
                    break
                for call in response.tool_calls:
                    steps += 1
                    if steps > budget.max_tool_steps:
                        return _fail(
                            "BUDGET_EXCEEDED", f"more than {budget.max_tool_steps} tool steps"
                        )
                    with span(f"tool:{call.name}", {"arguments": call.arguments}) as tool_out:
                        result = tools.call(call.name, call.arguments)
                        tool_out["ok"] = result["ok"]
                    if not result["ok"]:
                        errors += 1
                        error_counts[call.name] = error_counts.get(call.name, 0) + 1
                        if error_counts[call.name] > budget.max_tool_retries:
                            return _fail("TOOL_FAILED", f"{call.name}: {result['error']}")
                    messages.append(
                        Message(role="tool", tool_call_id=call.id, content=_json(result))
                    )
            out["tool_steps"] = steps
        retrieved = {**state.get("retrieved", {}), **tools.retrieved}
        return {
            "messages": [m.model_dump(mode="json") for m in messages],
            "tool_steps": steps,
            "tool_errors": errors,
            "tool_error_counts": error_counts,
            "llm_calls": llm_calls,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "retrieved": retrieved,
        }

    def retrieve(state: AgentState) -> dict[str, Any]:
        invoice = deps.reader.get_invoice(state["invoice_id"])
        primary = ExceptionCode(state["match"]["primary"])
        scope = AccessScope(
            role=matrix.approver_hierarchy[0], vendor_ids=frozenset({invoice.vendor_id})
        )
        queries: list[tuple[str, list[Any]]] = [(POLICY_QUERIES[primary], ["policy", "gst_guide"])]
        if "REMITTANCE_CHANGE_REQUEST" in state.get("text_signals", []):
            queries.append((POLICY_QUERIES[ExceptionCode.VENDOR_BANK_CHANGE], ["policy"]))
        if primary is ExceptionCode.PRICE_VARIANCE:
            queries.append(("price escalation clause authorised increase", ["contract"]))
        retrieved = dict(state.get("retrieved", {}))
        with span("retrieve") as out:
            for query, types in queries:
                for hit in deps.retriever.search(query, scope, k=3, doc_types=types).hits:
                    retrieved[hit.chunk.chunk_id] = {
                        "title": hit.chunk.title,
                        "text": hit.chunk.text,
                    }
            out["chunk_ids"] = sorted(retrieved)
        return {"retrieved": retrieved}

    def propose_default(state: AgentState) -> dict[str, Any]:
        """Deterministic fast path for a clean invoice with no vendor text."""
        retrieved = retrieve(state)["retrieved"]
        citation = next(
            (c for c in ("AP-POL:§4.1", "AP-POL:§4.2") if c in retrieved),
            next(iter(sorted(retrieved)), ""),
        )
        proposal = {
            "exception": "CLEAN",
            "action": "APPROVE",
            "rationale": "Matches PO and goods receipt within tolerance (deterministic).",
            "citations": [citation] if citation else [],
            "text_signals": [],
            "vendor_email_needed": False,
        }
        return {"retrieved": retrieved, "proposal": proposal, "proposal_source": "deterministic"}

    def propose(state: AgentState) -> dict[str, Any]:
        history = [Message.model_validate(m) for m in state.get("messages", [])]
        context = _context(state)
        context["retrieved_chunks"] = {
            k: v["text"][:600] for k, v in state.get("retrieved", {}).items()
        }
        feedback = ""
        if state.get("issues"):
            feedback = "\n\nYour previous proposal was rejected:\n" + "\n".join(
                f"- {i['code']}: {i['message']}" for i in state["issues"]
            )
        messages = (history or [Message(role="system", content=SYSTEM_PROMPT)]) + [
            Message(role="user", content=case_message(context, PROPOSE_INSTRUCTION + feedback))
        ]
        attempts = state.get("propose_attempts", 0) + 1
        with span("propose_resolution", {"attempt": attempts}):
            try:
                response = deps.llm.complete(messages, json_schema=proposal_schema())
            except LLMError as exc:
                return _fail("LLM_ERROR", str(exc))
        return {
            "proposal": {"raw": response.content},
            "proposal_source": "llm",
            "propose_attempts": attempts,
            "llm_calls": state.get("llm_calls", 0) + 1,
            "tokens_in": state.get("tokens_in", 0) + response.usage.input_tokens,
            "tokens_out": state.get("tokens_out", 0) + response.usage.output_tokens,
        }

    def validate(state: AgentState) -> dict[str, Any]:
        raw = state.get("proposal") or {}
        text = raw["raw"] if "raw" in raw else _json(raw)
        proposal, issues = validate_proposal(
            text,
            ExceptionCode(state["match"]["primary"]),
            state.get("text_signals", []),
            set(state.get("retrieved", {})),
            matrix,
        )
        with span("validate") as out:
            out["issues"] = [i.code for i in issues]
        audit(
            state,
            "PROPOSAL",
            {
                "proposal": proposal.model_dump(mode="json") if proposal else None,
                "issues": [i.model_dump() for i in issues],
                "source": state.get("proposal_source", ""),
            },
            n=state.get("propose_attempts", 0),
        )
        if issues:
            update: dict[str, Any] = {"issues": [i.model_dump() for i in issues]}
            if (
                state.get("propose_attempts", 0) >= MAX_PROPOSE_ATTEMPTS
                or state.get("proposal_source") == "deterministic"
            ):
                update |= _fail(
                    "VALIDATION_FAILED", "; ".join(f"{i.code}: {i.message}" for i in issues)
                )
            return update
        if proposal is None:  # unreachable: no issues means it parsed
            return _fail("VALIDATION_FAILED", "proposal missing")
        return {"proposal": proposal.model_dump(mode="json"), "issues": []}

    def policy_authorize(state: AgentState) -> dict[str, Any]:
        decision = evaluate(proposal_obj(state), matrix)
        with span("policy_authorize") as out:
            out["outcome"] = decision.outcome.value
        audit(state, "POLICY_DECISION", decision.model_dump(mode="json"), n="initial")
        update: dict[str, Any] = {"decision": decision.model_dump(mode="json")}
        if decision.outcome is Outcome.DENY:
            failed = [r.rule_id for r in decision.results if r.status == "fail"]
            return update | _fail("POLICY_DENY", f"policy denied the proposal: {failed}")
        if decision.outcome is Outcome.REQUIRE_APPROVAL:
            deps.cases.upsert(
                state["case_id"],
                state["invoice_id"],
                "AWAITING_APPROVAL",
                deps.preparer.id,
                summary=_summary(state, decision),
                required_role=decision.required_role.value if decision.required_role else None,
            )
            update["status"] = "AWAITING_APPROVAL"
        return update

    def await_approval(state: AgentState) -> dict[str, Any]:
        # Nothing but the interrupt: this node re-runs from the top when resumed.
        decision = state["decision"] or {}
        value = interrupt(
            {
                "case_id": state["case_id"],
                "proposal": state["proposal"],
                "required_role": decision.get("required_role"),
                "requires_out_of_band_verification": decision.get(
                    "requires_out_of_band_verification"
                ),
                "note": state.get("approval_note", ""),
            }
        )
        return {"resume": value}

    def apply_approval(state: AgentState) -> dict[str, Any]:
        value = state.get("resume") or {}
        rounds = state.get("approval_rounds", 0) + 1
        approver = Identity.model_validate(
            value.get("approver", {"id": "unknown", "kind": "agent"})
        )
        if value.get("decision") == "reject":
            audit(
                state,
                "APPROVAL_REJECTED",
                {"approver": approver.model_dump(), "comment": value.get("comment", "")},
                n=rounds,
            )
            return {"approval_rounds": rounds} | _fail(
                "REJECTED_BY_APPROVER", value.get("comment", "")
            )
        approvals = [*state.get("approvals", []), {"approver": approver.model_dump()}]
        verifications = list(state.get("verifications", []))
        if value.get("verification"):
            verifications.append(Verification.model_validate(value["verification"]).model_dump())
        decision = evaluate(
            proposal_obj(state),
            matrix,
            [Approval.model_validate(a) for a in approvals],
            [Verification.model_validate(v) for v in verifications],
        )
        audit(
            state,
            "APPROVAL_EVALUATED",
            {
                "approver": approver.model_dump(),
                "outcome": decision.outcome.value,
                "decision": decision.model_dump(mode="json"),
            },
            n=rounds,
        )
        update: dict[str, Any] = {
            "approval_rounds": rounds,
            "decision": decision.model_dump(mode="json"),
        }
        if decision.outcome is Outcome.ALLOW:
            return update | {
                "approvals": approvals,
                "verifications": verifications,
                "approval_note": "",
            }
        if rounds >= MAX_APPROVAL_ROUNDS:
            return update | _fail("APPROVAL_ROUNDS_EXCEEDED", "no valid approval recorded")
        if decision.outcome is Outcome.DENY:  # invalid approver (self, agent, auditor): drop it
            failed = [r.message for r in decision.results if r.status == "fail"]
            return update | {
                "approval_note": f"approval not accepted: {failed}",
                "decision": evaluate(
                    proposal_obj(state),
                    matrix,
                    [Approval.model_validate(a) for a in approvals[:-1]],
                    [Verification.model_validate(v) for v in verifications],
                ).model_dump(mode="json"),
            }
        pending = [r.message for r in decision.results if r.status == "pending"]
        return update | {
            "approvals": approvals,
            "verifications": verifications,
            "approval_note": f"still required: {pending}",
        }

    def execute(state: AgentState) -> dict[str, Any]:
        decision = PolicyDecision.model_validate(state["decision"])
        with span("execute") as out:
            try:
                result = deps.executor.execute(state["case_id"], proposal_obj(state), decision)
            except (ErpUnavailableError, ErpConflictError) as exc:
                return _fail("ERP_ERROR", str(exc))
            out["decision_id"] = result.decision_id
        audit(state, "EXECUTED", result.model_dump())
        return {"execution": result.model_dump(), "status": "EXECUTED"}

    def record(state: AgentState) -> dict[str, Any]:
        invoice = deps.reader.get_invoice(state["invoice_id"])
        vendor = deps.reader.get_vendor(invoice.vendor_id)
        proposal = state.get("proposal") or {}
        draft = None
        if proposal and Action(proposal["action"]) in (
            Action.REQUEST_CREDIT_NOTE,
            Action.REQUEST_CORRECTED_INVOICE,
            Action.REJECT_DUPLICATE,
        ):
            reason = (
                "; ".join(f["message"] for f in state["match"]["findings"]) or proposal["rationale"]
            )
            made = draft_vendor_email(
                deps.drafts,
                state["case_id"],
                Action(proposal["action"]),
                vendor.legal_name,
                invoice.invoice_number,
                invoice.invoice_date.isoformat(),
                reason,
                proposal["citations"],
            )
            draft = made.model_dump() if made else None
            if draft:
                audit(state, "EMAIL_DRAFTED", {"subject": draft["subject"], "sent": False})
        evidence = _evidence(state, "EXECUTED")
        deps.cases.upsert(
            state["case_id"],
            state["invoice_id"],
            "EXECUTED",
            deps.preparer.id,
            summary=_summary(state, None),
        )
        return {"evidence": evidence, "draft": draft, "status": "EXECUTED"}

    def fail_safe(state: AgentState) -> dict[str, Any]:
        reason = state.get("fail_reason") or "UNKNOWN"
        audit(state, "FAIL_SAFE", {"reason": reason, "detail": state.get("fail_detail", "")})
        evidence = _evidence(state, "MANUAL_QUEUE")
        deps.cases.upsert(
            state["case_id"],
            state["invoice_id"],
            "MANUAL_QUEUE",
            deps.preparer.id,
            summary=_summary(state, None),
            reason=reason,
        )
        return {"status": "MANUAL_QUEUE", "evidence": evidence}

    def _evidence(state: AgentState, outcome: str) -> dict[str, Any]:
        pack = {
            "case_id": state["case_id"],
            "invoice_id": state["invoice_id"],
            "outcome": outcome,
            "simulated": True,
            "model": deps.llm.name,
            "match": state.get("match"),
            "text_signals": state.get("text_signals"),
            "retrieved": state.get("retrieved"),
            "proposal": state.get("proposal"),
            "decision": state.get("decision"),
            "approvals": state.get("approvals"),
            "verifications": state.get("verifications"),
            "execution": state.get("execution"),
            "fail_reason": state.get("fail_reason"),
            "fail_detail": state.get("fail_detail"),
            "usage": {
                k: state.get(k, 0)
                for k in ("llm_calls", "tool_steps", "tool_errors", "tokens_in", "tokens_out")
            },
        }
        path, digest = write_evidence_pack(deps.evidence_dir, state["case_id"], pack)
        audit(state, "EVIDENCE_PACK", {"path": path.name, "sha256": digest}, n=outcome)
        return {"path": str(path), "sha256": digest}

    # -- wiring -----------------------------------------------------------------------

    def failed(state: AgentState) -> bool:
        return bool(state.get("fail_reason"))

    def after_screen(state: AgentState) -> str:
        clean = state["match"]["primary"] == ExceptionCode.CLEAN.value
        if clean and not state.get("has_free_text") and not state.get("text_signals"):
            return "propose_default"
        return "investigate"

    def after_validate(state: AgentState) -> str:
        if failed(state):
            return "fail_safe"
        return "propose" if state.get("issues") else "policy_authorize"

    def after_authorize(state: AgentState) -> str:
        if failed(state):
            return "fail_safe"
        outcome = (state.get("decision") or {}).get("outcome")
        return "execute" if outcome == Outcome.ALLOW.value else "await_approval"

    def after_apply(state: AgentState) -> str:
        if failed(state):
            return "fail_safe"
        outcome = (state.get("decision") or {}).get("outcome")
        return (
            "execute"
            if outcome == Outcome.ALLOW.value and not state.get("approval_note")
            else "await_approval"
        )

    def ok_or_fail(next_node: str) -> Callable[[AgentState], str]:
        return lambda state: "fail_safe" if failed(state) else next_node

    graph: StateGraph[AgentState] = StateGraph(AgentState)
    for name, fn in [
        ("intake", intake),
        ("deterministic_match", deterministic_match),
        ("screen_text", screen_text),
        ("investigate", investigate),
        ("retrieve", retrieve),
        ("propose_default", propose_default),
        ("propose", propose),
        ("validate", validate),
        ("policy_authorize", policy_authorize),
        ("await_approval", await_approval),
        ("apply_approval", apply_approval),
        ("execute", execute),
        ("record", record),
        ("fail_safe", fail_safe),
    ]:
        graph.add_node(name, fn)
    graph.add_edge(START, "intake")
    graph.add_conditional_edges("intake", ok_or_fail("deterministic_match"))
    graph.add_conditional_edges("deterministic_match", ok_or_fail("screen_text"))
    graph.add_conditional_edges("screen_text", after_screen)
    graph.add_conditional_edges("investigate", ok_or_fail("retrieve"))
    graph.add_conditional_edges("retrieve", ok_or_fail("propose"))
    graph.add_edge("propose_default", "validate")
    graph.add_conditional_edges("propose", ok_or_fail("validate"))
    graph.add_conditional_edges("validate", after_validate)
    graph.add_conditional_edges("policy_authorize", after_authorize)
    graph.add_edge("await_approval", "apply_approval")
    graph.add_conditional_edges("apply_approval", after_apply)
    graph.add_conditional_edges("execute", ok_or_fail("record"))
    graph.add_edge("record", END)
    graph.add_edge("fail_safe", END)
    return graph


def _json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, default=str)


def _summary(state: AgentState, decision: PolicyDecision | None) -> dict[str, Any]:
    proposal = state.get("proposal") or {}
    return {
        "exception": proposal.get("exception"),
        "action": proposal.get("action"),
        "rationale": proposal.get("rationale"),
        "citations": proposal.get("citations"),
        "text_signals": state.get("text_signals"),
        "requires_out_of_band_verification": bool(
            decision and decision.requires_out_of_band_verification
        ),
    }
