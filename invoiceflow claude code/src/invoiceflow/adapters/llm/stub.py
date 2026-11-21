"""A deterministic stand-in for an LLM. It exists to test the harness (tool loop, budgets,
validation, policy, interrupts, audit), not to measure intelligence.

It never reads invoice free text. It calls a fixed set of tools, then proposes the
control-matrix default action for the matcher's exception (or a bank-change escalation if
the deterministic text screen raised that signal), citing the first retrieved sections.
Agent results with this model are therefore close to the rule-only baseline by design.
"""

import json
import re
from collections.abc import Sequence
from typing import Any

from invoiceflow.ports.llm import LLMResponse, Message, ToolCall, ToolSpec, Usage

_CONTEXT = re.compile(r"CASE_CONTEXT\s*```json\s*(\{.*?\})\s*```", re.DOTALL)


def case_context(messages: Sequence[Message]) -> dict[str, Any]:
    for message in reversed(messages):
        if message.role == "user":
            match = _CONTEXT.search(message.content)
            if match:
                return dict(json.loads(match.group(1)))
    return {}


class StubChatModel:
    @property
    def name(self) -> str:
        return "stub"

    def complete(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        context = case_context(messages)
        usage = Usage(input_tokens=sum(len(m.content) // 4 for m in messages), output_tokens=60)
        if json_schema is not None:
            return LLMResponse(
                content=json.dumps(self._propose(context)), usage=usage, model=self.name
            )
        turns = sum(1 for m in messages if m.role == "assistant" and m.tool_calls)
        invoice_id, po_id = context.get("invoice_id", ""), context.get("po_id", "")
        if turns == 0 and tools:
            calls = [
                ToolCall(id="t1", name="get_invoice", arguments={"invoice_id": invoice_id}),
                ToolCall(id="t2", name="get_po", arguments={"po_id": po_id}),
                ToolCall(id="t3", name="get_grn", arguments={"po_id": po_id}),
                ToolCall(
                    id="t4",
                    name="get_vendor",
                    arguments={"vendor_id": context.get("vendor_id", "")},
                ),
            ]
            return LLMResponse(tool_calls=tuple(calls), usage=usage, model=self.name)
        if turns == 1 and tools:
            calls = [
                ToolCall(
                    id="t5",
                    name="search_policy",
                    arguments={"query": context.get("policy_query", "")},
                )
            ]
            if context.get("matcher_primary") == "PRICE_VARIANCE":
                calls.append(
                    ToolCall(
                        id="t6",
                        name="search_contract",
                        arguments={"query": "price escalation clause"},
                    )
                )
            return LLMResponse(tool_calls=tuple(calls), usage=usage, model=self.name)
        return LLMResponse(content="Investigation complete.", usage=usage, model=self.name)

    @staticmethod
    def _propose(context: dict[str, Any]) -> dict[str, Any]:
        signals = list(context.get("text_signals", []))
        exception = context.get("matcher_primary", "CLEAN")
        if "REMITTANCE_CHANGE_REQUEST" in signals:
            exception = "VENDOR_BANK_CHANGE"
        action = context.get("default_actions", {}).get(exception, "ESCALATE_FRAUD_REVIEW")
        citations = list(context.get("retrieved_chunk_ids", []))[:2]
        return {
            "exception": exception,
            "action": action,
            "rationale": f"Deterministic matcher found {context.get('matcher_primary')}; "
            f"proposing the control-matrix default {action}.",
            "citations": citations,
            "text_signals": signals,
            "vendor_email_needed": action in {"REQUEST_CREDIT_NOTE", "REQUEST_CORRECTED_INVOICE"},
        }
