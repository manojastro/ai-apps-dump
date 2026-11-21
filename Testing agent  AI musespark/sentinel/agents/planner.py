"""Planner: UserStory -> list[TestCase].

No browser here. The job is coverage: happy, negative, boundary, edge —
including the five mandatory edge cases — plus risk-based filtering when
a git diff is supplied.

Reliability design (per project rules):
- Every LLM call has a timeout (config.DEFAULT_LLM_TIMEOUT_SECS).
- Output is validated against the TestCase schema; on failure we send a
  repair prompt with the validation error, max 2 retries.
- Every model call logs tokens + USD and feeds the budget kill switch.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import TypeAdapter

from sentinel.config import (
    CostTracker,
    Settings,
    estimate_cost_usd,
    is_action_blocked,
)
from sentinel.models import TestCase, UserStory

logger = logging.getLogger("sentinel.planner")

MAX_REPAIR_RETRIES = 2

# The five edge cases the spec mandates. Matching is substring-based on
# lowercased title+steps, so the prompt asks for these exact phrases.
REQUIRED_EDGE_SIGNALS = [
    "empty required field",
    "maximum-length",
    "special characters",
    "double-submit",
    "browser-back",
]

PLAN_SYSTEM_PROMPT = """You are Sentinel's test planner, a senior QA engineer.
Given a Salesforce Lightning user story (and optionally a git diff), output test cases.

Rules:
- Output ONLY a JSON array. No markdown fences, no commentary.
- Each item must match the TestCase schema: id, story_id, title, type, steps, expected_result, priority, reasoning.
- type must be one of: happy, negative, boundary, edge.
- Cover: at least 1 happy path, at least 2 negative, at least 1 boundary, at least 2 edge cases (minimum 8 total).
- The edge cases MUST include all five: empty required field, maximum-length input, special characters and emoji, double-submit, browser-back mid-flow. Use those exact phrases in the titles so coverage is auditable.
- steps: ordered, human-readable, intent-based (e.g. "Submit the form via the Save button"). NEVER write CSS selectors or XPath.
- priority: high for happy path + validation-removal risks, medium for boundary, low for cosmetic edges unless the story says otherwise.
- reasoning: one sentence explaining why this case matters.
- If a git diff is supplied: ONLY include cases touching the changed areas, and say in reasoning which changed file/area motivated the case.
- NEVER include irreversible operations: mass delete, delete account, modify org-wide settings, send email, install package. If the story seems to ask for one, replace it with a safe read-only or single-record disposable-data equivalent with TEST- prefix.
- story_id must equal the input story id exactly. ids must be unique: <STORYID>-<TYPE>-<NN>.
"""


def build_planner_prompt(story: UserStory, git_diff: str | None = None) -> str:
    lines = [
        f"Story id: {story.id}",
        f"Title: {story.title}",
        f"Description: {story.description}",
        "Acceptance criteria:",
    ]
    for i, ac in enumerate(story.acceptance_criteria, 1):
        lines.append(f"  {i}. {ac}")
    if git_diff and git_diff.strip():
        # Cap diff size so one huge diff cannot blow the context/cost budget.
        capped = git_diff[:12000]
        lines.append("\nGit diff (risk-based scoping — restrict cases to these changed areas):")
        lines.append(capped)
        lines.append("\nRemember: reasoning must cite the changed area for each case.")
    else:
        lines.append("\nNo git diff supplied — cover the whole story.")
    lines.append("\nReturn the JSON array now.")
    return "\n".join(lines)


def _extract_json_array(raw: str) -> str:
    """Tolerate fences / leading prose; return the first [...] JSON array found."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM output contained no JSON array")
    return text[start : end + 1]


def parse_and_validate(raw: str, story: UserStory, git_diff: str | None = None) -> list[TestCase]:
    adapter: TypeAdapter[list[TestCase]] = TypeAdapter(list[TestCase])
    payload = _extract_json_array(raw)
    try:
        cases = adapter.validate_json(payload)
    except Exception as exc:
        raise ValueError(f"Schema validation failed: {exc}") from exc

    if len(cases) < 8:
        raise ValueError(f"Coverage failure: need >=8 test cases, got {len(cases)}")
    types = {c.type for c in cases}
    for required in ("happy", "negative", "boundary", "edge"):
        if required not in types:
            raise ValueError(f"Coverage failure: missing type {required!r}")
    edges = [c for c in cases if c.type == "edge"]
    if len(edges) < 2:
        raise ValueError(f"Coverage failure: need >=2 edge cases, got {len(edges)}")
    blob = " ".join((c.title + " " + " ".join(c.steps)).lower() for c in cases)
    missing = [s for s in REQUIRED_EDGE_SIGNALS if s not in blob]
    if missing:
        raise ValueError(f"Coverage failure: edge cases missing signals {missing}")

    seen_ids: set[str] = set()
    for c in cases:
        if c.story_id != story.id:
            raise ValueError(f"story_id mismatch: {c.story_id!r} != {story.id!r}")
        if c.id in seen_ids:
            raise ValueError(f"Duplicate test case id: {c.id!r}")
        seen_ids.add(c.id)
        for step in c.steps:
            if is_action_blocked(step):
                raise ValueError(f"Blocked irreversible action in {c.id}: {step!r}")

    if git_diff and git_diff.strip():
        without_reason = [c.id for c in cases if not c.reasoning.strip()]
        if without_reason:
            raise ValueError(f"Risk-based failure: missing reasoning for {without_reason}")
    return cases


def _call_llm(client: Any, model: str, system: str, user: str, timeout: int) -> tuple[str, int, int]:
    """One Anthropic call. Returns (text, input_tokens, output_tokens). Timeout enforced."""
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
        timeout=timeout,
    )
    chunks: list[str] = []
    for block in msg.content:
        if getattr(block, "type", "") == "text":
            chunks.append(getattr(block, "text", ""))
    text = "".join(chunks)
    usage = getattr(msg, "usage", None)
    in_tok = int(getattr(usage, "input_tokens", 0) or 0)
    out_tok = int(getattr(usage, "output_tokens", 0) or 0)
    return text, in_tok, out_tok


def plan(
    story: UserStory,
    git_diff: str | None = None,
    settings: Settings | None = None,
    client: Any | None = None,
    tracker: CostTracker | None = None,
) -> list[TestCase]:
    """Plan test cases for a story. Raises on missing key, budget breach, or schema failure.

    `client` is injectable for tests; in production it is an anthropic.Anthropic instance.
    """
    settings = settings or Settings.from_env()
    if client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key — "
                "the Planner makes real API calls and refuses to fake output."
            )
        try:
            import anthropic  # local import so unit tests don't need the SDK
        except ImportError as exc:
            raise RuntimeError("anthropic package not installed. Run: uv sync --group dev") from exc
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    tracker = tracker or CostTracker(settings.max_tokens_per_run, settings.max_cost_usd_per_run)
    user_prompt = build_planner_prompt(story, git_diff)
    raw, in_tok, out_tok = _call_llm(
        client, settings.anthropic_model, PLAN_SYSTEM_PROMPT, user_prompt, settings.llm_timeout_secs
    )
    cost = estimate_cost_usd(settings.anthropic_model, in_tok, out_tok)
    tracker.add(in_tok + out_tok, cost)
    logger.info("Planner call: %d in / %d out tokens ($%.4f)", in_tok, out_tok, cost)

    try:
        return parse_and_validate(raw, story, git_diff)
    except ValueError as exc:
        first_err: Exception = exc
        logger.warning("Planner schema/coverage failure (attempt 1): %s", first_err)

    last_err: Exception = first_err
    for attempt in range(1, MAX_REPAIR_RETRIES + 1):
        repair = (
            f"Your previous output failed validation:\n{last_err}\n\n"
            f"Previous output:\n{raw[:4000]}\n\n"
            "Fix ALL listed problems and return ONLY the corrected JSON array."
        )
        raw, in_tok, out_tok = _call_llm(
            client, settings.anthropic_model, PLAN_SYSTEM_PROMPT, repair, settings.llm_timeout_secs
        )
        cost = estimate_cost_usd(settings.anthropic_model, in_tok, out_tok)
        tracker.add(in_tok + out_tok, cost)
        logger.info("Planner repair %d: %d in / %d out ($%.4f)", attempt, in_tok, out_tok, cost)
        try:
            return parse_and_validate(raw, story, git_diff)
        except ValueError as exc:
            logger.warning("Planner repair %d failed: %s", attempt, exc)
            last_err = exc
    raise ValueError(f"Planner failed after {MAX_REPAIR_RETRIES} repairs: {last_err}")
