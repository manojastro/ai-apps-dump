"""MLflow ResponsesAgent wrapper, so the same graph can be evaluated with MLflow and, if
ADR 0007 chooses it, served on Databricks (the AgentServer path is labelled legacy there).

Input: a user message naming an invoice id (e.g. "Resolve INV-00042"). Output: one text
item summarising the case, plus `custom_outputs` with the case status and proposal. The
agent never approves: an approval comes from the approval service, not from a chat turn.
"""

import re
import uuid
from collections.abc import Generator
from typing import Any

from mlflow.pyfunc.model import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from invoiceflow.agent.runner import AgentRunner

_INVOICE = re.compile(r"\bINV-\d{5}\b")


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(getattr(part, "text", ""))
            for part in content
        )
    return str(content or "")


class InvoiceFlowResponsesAgent(ResponsesAgent):
    def __init__(self, runner: AgentRunner | None = None) -> None:
        self._runner = runner

    @property
    def runner(self) -> AgentRunner:
        if self._runner is None:
            from invoiceflow.agent.wiring import build_runner
            from invoiceflow.config import Settings

            self._runner = build_runner(Settings())
        return self._runner

    def _answer(self, request: ResponsesAgentRequest) -> tuple[str, dict[str, Any]]:
        texts = [
            _text(item.get("content") if isinstance(item, dict) else getattr(item, "content", ""))
            for item in request.input
        ]
        match = next((m for t in reversed(texts) if (m := _INVOICE.search(t))), None)
        if match is None:
            return "Please name an invoice id such as INV-00042.", {"status": "NO_INVOICE"}
        outcome = self.runner.start(match.group(0))
        proposal = outcome.state.get("proposal") or {}
        if outcome.status == "MANUAL_QUEUE":
            text = f"{match.group(0)} was routed to the manual queue ({outcome.fail_reason})."
        else:
            text = (
                f"{match.group(0)}: {proposal.get('exception')} -> {proposal.get('action')} "
                f"({outcome.status}). Citations: {', '.join(proposal.get('citations', []))}."
            )
            if outcome.interrupt:
                text += f" Needs approval by {outcome.interrupt.get('required_role')}."
        return text, {
            "case_id": outcome.case_id,
            "status": outcome.status,
            "fail_reason": outcome.fail_reason,
            "proposal": proposal,
        }

    # ResponsesAgent narrows PythonModel's generic predict signature by design.
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:  # type: ignore[override]
        text, custom = self._answer(request)
        item = self.create_text_output_item(text=text, id=str(uuid.uuid4()))
        return ResponsesAgentResponse(output=[item], custom_outputs=custom)

    def predict_stream(  # type: ignore[override]
        self, request: ResponsesAgentRequest
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        text, _ = self._answer(request)
        item = self.create_text_output_item(text=text, id=str(uuid.uuid4()))
        yield ResponsesAgentStreamEvent(type="response.output_item.done", item=item)
