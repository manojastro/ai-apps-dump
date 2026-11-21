"""Copilot loop: Claude tool use with a post-answer guardrail check.

A manual loop rather than the SDK's beta tool runner, because each tool call has to be
scoped, wrapped as untrusted data and recorded, and the finished answer has to pass a
citation and number check before the user sees it.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic
from sqlalchemy.orm import Session

from app.copilot import guardrails
from app.copilot.audit import write_audit
from app.copilot.prompts import REPAIR_PROMPT, SYSTEM_PROMPT, user_context
from app.copilot.tools import TOOL_DEFINITIONS, ToolContext, run_tool
from app.core.config import get_settings
from app.services.scope import Scope

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 16_000
# Refused requests are retried on another model server-side, where the model supports it.
FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"
REFUSAL_MESSAGE = "I can't help with that request. I can answer questions about revenue data."


class LLMUnavailable(RuntimeError):
    """No API key is configured."""


class MessagesClient(Protocol):
    """The slice of the Anthropic client we use. Tests supply a scripted fake."""

    def create(self, **kwargs: Any) -> Any: ...


@dataclass
class CopilotResult:
    answer: str
    tools_called: list[dict] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    invalid_citations: list[str] = field(default_factory=list)
    ungrounded_numbers: list[str] = field(default_factory=list)
    stop_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    audit_id: int | None = None


def default_client() -> MessagesClient:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise LLMUnavailable("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key).beta.messages


def _request(messages: list[dict]) -> dict[str, Any]:
    settings = get_settings()
    request: dict[str, Any] = {
        "model": settings.llm_model,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "system": [{
            "type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"},
        }],
        "tools": TOOL_DEFINITIONS,
        "messages": messages,
        "output_config": {"effort": settings.llm_effort},
    }
    if settings.llm_model in FALLBACK_MODELS:
        request["betas"] = [FALLBACK_BETA]
        request["fallbacks"] = "default"
    return request


def _text_of(response: Any) -> str:
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


class Copilot:
    def __init__(
        self,
        session: Session,
        scope: Scope,
        team_name: str | None = None,
        client: MessagesClient | None = None,
    ) -> None:
        self.ctx = ToolContext(session=session, scope=scope)
        self.team_name = team_name
        self.client = client or default_client()
        self.allowed_citations: set[str] = set()
        self.known_numbers: set[float] = set()
        self.tools_called: list[dict] = []
        self.input_tokens = 0
        self.output_tokens = 0

    def _call(self, messages: list[dict]) -> Any:
        response = self.client.create(**_request(messages))
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.input_tokens += getattr(usage, "input_tokens", 0) or 0
            self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        return response

    def _execute(self, block: Any) -> dict:
        arguments = dict(block.input or {})
        result, is_error = run_tool(self.ctx, block.name, arguments)
        self.tools_called.append({"name": block.name, "input": arguments, "error": is_error})
        guardrails.collect_citations(result, self.allowed_citations)
        guardrails.collect_numbers(result, self.known_numbers)
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": guardrails.wrap_tool_result(block.name, result),
            "is_error": is_error,
        }

    def _loop(self, messages: list[dict]) -> tuple[str, str | None]:
        """Run until the model stops calling tools. Returns (answer, stop_reason)."""
        for _ in range(get_settings().llm_max_tool_turns):
            response = self._call(messages)
            stop = response.stop_reason
            if stop == "refusal":
                return REFUSAL_MESSAGE, stop
            if stop == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue
            if stop == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                calls = [b for b in response.content if b.type == "tool_use"]
                messages.append({"role": "user", "content": [self._execute(b) for b in calls]})
                continue
            messages.append({"role": "assistant", "content": response.content})
            return _text_of(response), stop
        return "I could not finish that within the tool-call limit. Please narrow the " \
               "question.", "tool_limit"

    def ask(self, question: str, history: list[dict] | None = None) -> CopilotResult:
        started = time.perf_counter()
        settings = get_settings()
        context = user_context(
            settings.data_as_of.isoformat(), self.ctx.scope.role, self.team_name
        )
        messages: list[dict] = list(history or [])
        messages.append({"role": "user", "content": f"{context}\n\nQuestion: {question}"})

        answer, stop = self._loop(messages)
        check = guardrails.check_answer(answer, self.allowed_citations, self.known_numbers)
        if not check.ok and stop == "end_turn":
            messages.append({"role": "user", "content": REPAIR_PROMPT.format(
                invalid=check.invalid_citations or "none",
                numbers=check.ungrounded or "none",
            )})
            answer, stop = self._loop(messages)
            check = guardrails.check_answer(answer, self.allowed_citations, self.known_numbers)
        answer = guardrails.strip_invalid_citations(answer, check.invalid_citations)

        result = CopilotResult(
            answer=answer,
            tools_called=self.tools_called,
            citations=[c for c in check.citations if c not in check.invalid_citations],
            invalid_citations=check.invalid_citations,
            ungrounded_numbers=check.ungrounded,
            stop_reason=stop,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        result.audit_id = write_audit(self.ctx.session, self.ctx.scope.user_id, question, result)
        logger.info("copilot_answer", extra={"fields": {
            "audit_id": result.audit_id, "tools": len(result.tools_called),
            "citations": len(result.citations), "latency_ms": result.latency_ms,
            "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
            "stop_reason": stop,
        }})
        return result


def result_payload(result: CopilotResult) -> dict:
    payload = result.__dict__.copy()
    return json.loads(json.dumps(payload, default=str))
