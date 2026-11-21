"""Plain-Python agent loop: prompt -> model picks tool -> gateway -> result back -> repeat (max 8 steps)."""
from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from app import clock
from app.agents.prompts import get_prompt
from app.config import get_settings
from app.data.db import session
from app.data.models import AgentRun
from app.llm.client import LLMClient, get_llm
from app.obs.tracing import span
from app.rbac import policy
from app.safety import wrap_untrusted
from app.tools import REGISTRY, call_tool

MAX_FORMAT_RETRIES = 2


class AgentRunResult(BaseModel):
    status: Literal["DONE", "STEP_LIMIT", "INVALID_OUTPUT", "FAILED"]
    result: dict | None = None
    steps: int = 0
    tool_calls: list[dict] = []
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    error: str | None = None


def build_task_message(task: dict, untrusted: dict[str, str] | None) -> str:
    parts = ["TASK_JSON: " + json.dumps(task, sort_keys=True, default=str)]
    for label, text in (untrusted or {}).items():
        parts.append(wrap_untrusted(label, text))
    return "\n\n".join(parts)


def extract_json(text: str) -> Any:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


class BaseAgent:
    name: str = ""
    role: str = ""
    result_model: type[BaseModel]
    prompt_version = "v1"

    def __init__(self, llm: LLMClient | None = None, max_steps: int | None = None):
        self.llm = llm or get_llm()
        self.max_steps = max_steps or get_settings().agent_max_steps

    # tools shown to the model = exactly the role's allow-list
    def tool_schemas(self) -> list[dict]:
        return [REGISTRY[t].llm_schema() for t in policy.allowed_tools(self.role) if t in REGISTRY]

    def run(self, task: dict, *, untrusted: dict[str, str] | None = None, workflow_id: str | None = None,
            task_key: str | None = None, patient_scope: str | None = None) -> AgentRunResult:
        with span("agent.run", {"agent": self.name, "workflow_id": workflow_id or ""}) as sp:
            res = self._loop(task, untrusted, workflow_id, task_key or f"{workflow_id}:{self.name}", patient_scope)
            sp.set_attribute("status", res.status)
            sp.set_attribute("steps", res.steps)
        self._record(res, workflow_id)
        return res

    def _record(self, res: AgentRunResult, workflow_id: str | None) -> None:
        with session() as s:
            s.add(AgentRun(workflow_id=workflow_id, agent=self.name, status=res.status, steps=res.steps,
                           tokens_in=res.tokens_in, tokens_out=res.tokens_out, latency_ms=res.latency_ms,
                           prompt_version=self.prompt_version, llm_mode=self.llm.mode, created_at=clock.now()))

    def _loop(self, task, untrusted, workflow_id, task_key, patient_scope) -> AgentRunResult:
        version, system = get_prompt(self.name, self.prompt_version)
        messages: list[dict] = [{"role": "user", "content": build_task_message(task, untrusted)}]
        tools = self.tool_schemas()
        out = AgentRunResult(status="STEP_LIMIT")
        format_retries = 0
        tool_counter: dict[str, int] = {}

        for step in range(1, self.max_steps + 1):
            out.steps = step
            try:
                resp = self.llm.complete(agent=self.name, prompt_version=version, system=system,
                                         messages=messages, tools=tools)
            except Exception as exc:  # noqa: BLE001
                out.status, out.error = "FAILED", f"LLM error: {exc}"
                return out
            out.tokens_in += resp.tokens_in
            out.tokens_out += resp.tokens_out
            out.latency_ms += resp.latency_ms
            blocks: list[dict] = []
            if resp.text:
                blocks.append({"type": "text", "text": resp.text})
            blocks += [{"type": "tool_use", "id": t.id, "name": t.name, "input": t.input} for t in resp.tool_uses]
            messages.append({"role": "assistant", "content": blocks or [{"type": "text", "text": ""}]})

            if resp.tool_uses:
                results = []
                for tu in resp.tool_uses:
                    args = dict(tu.input)
                    spec = REGISTRY.get(tu.name)
                    if spec is not None and spec.mutating:  # keys come from code, never from the model
                        n = tool_counter[tu.name] = tool_counter.get(tu.name, 0) + 1
                        args["idempotency_key"] = f"{task_key}:{tu.name}:{n}"
                    tr = call_tool(self.role, tu.name, args, workflow_id=workflow_id, patient_scope=patient_scope)
                    out.tool_calls.append({"tool": tu.name, "status": tr.status, "error": tr.error})
                    results.append({"type": "tool_result", "tool_use_id": tu.id,
                                    "content": json.dumps(tr.data if tr.status == "ok" else {"error": tr.error,
                                                                                            "status": tr.status},
                                                          default=str)})
                messages.append({"role": "user", "content": results})
                continue

            try:
                obj = self.parse_final(resp.text)
                out.result, out.status = obj.model_dump(mode="json"), "DONE"
                return out
            except (ValueError, ValidationError) as exc:
                format_retries += 1
                if format_retries > MAX_FORMAT_RETRIES:
                    out.status, out.error = "INVALID_OUTPUT", f"invalid final answer: {str(exc)[:200]}"
                    return out
                messages.append({"role": "user", "content": "INVALID: your final answer did not match the required "
                                 f"JSON shape ({str(exc)[:150]}). Reply with only the JSON object."})
        out.status = "STEP_LIMIT"
        return out

    def parse_final(self, text: str) -> BaseModel:
        return self.result_model.model_validate(extract_json(text))
