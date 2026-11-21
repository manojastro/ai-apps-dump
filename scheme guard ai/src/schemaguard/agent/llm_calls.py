"""One place where nodes call the LLM: prompt rendering, budget checks, cost accounting."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from schemaguard.agent.guardrails import UNTRUSTED_PREAMBLE, add_usage, budget_exceeded, new_cost_tracking
from schemaguard.agent.state import AgentState, Deps
from schemaguard.llm.base import LLMError, parse_json_object
from schemaguard.observability import get_logger

log = get_logger("llm")

SYSTEM = (
    "You are SchemaGuard, an agent that protects data pipelines from upstream schema changes. "
    "Deterministic code has already computed the diff, lineage and verdicts; you add judgement and "
    "language. " + UNTRUSTED_PREAMBLE
)


class BudgetExceeded(RuntimeError):
    pass


def prompt(name: str, **values: str) -> str:
    template = resources.files("schemaguard.agent").joinpath(f"prompts/{name}.md").read_text(encoding="utf-8")
    return template.format(untrusted_preamble=UNTRUSTED_PREAMBLE, **values)


def cost_of(state: AgentState, deps: Deps) -> dict[str, Any]:
    return dict(
        state.get("cost_tracking")
        or new_cost_tracking(deps.settings.run_budget_usd, deps.settings.run_budget_tokens)
    )


def call_llm(
    deps: Deps, state: AgentState, task: str, user: str, context: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (parsed JSON, updated cost_tracking). Raises BudgetExceeded / LLMError."""
    ct = cost_of(state, deps)
    reason = budget_exceeded(ct)
    if reason:
        raise BudgetExceeded(reason)
    resp = deps.llm.complete(task, SYSTEM, user, context, json_mode=True)
    ct = add_usage(ct, resp.tokens_in, resp.tokens_out, resp.cost_usd)
    log.info(
        "llm call",
        extra={
            "task": task,
            "model": resp.model,
            "tokens_in": resp.tokens_in,
            "tokens_out": resp.tokens_out,
            "cost_usd": resp.cost_usd,
        },
    )
    try:
        data = parse_json_object(resp.text)
    except (LLMError, json.JSONDecodeError) as exc:
        raise LLMError(f"{task}: could not parse model output: {exc}") from exc
    reason = budget_exceeded(ct)
    if reason:
        raise BudgetExceeded(reason)
    return data, ct


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=1, default=str)[:12000]
