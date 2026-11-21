"""LLM explainer + fix proposer with strict validation.

For one Conflict we send ONLY its type and evidence. The reply must:
  1. be a single JSON object                            -> else "invalid_json"
  2. parse into ProposalOutput (Pydantic, extra=forbid) -> else "schema_error"
  3. use an action from the allow-list Enum             -> else "disallowed_action"
  4. explain in <= 80 words                             -> else "explanation_too_long"
  5. use an action compatible with the conflict type    -> else "incompatible_action"
  6. carry params that fit the action and reference ids in the evidence
                                                        -> else "bad_params" / "params_not_in_evidence"
Invalid output is retried at most twice (with the error fed back), then the proposal is FAILED
with the reason. It is never silently accepted.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.actions import COMPATIBLE, PARAM_SPEC, ParamsError, check_compatible, validate_params
from app.core.models import Action, Conflict, ProposalStatus
from app.llm.client import LLMCallError, LLMClient
from app.llm.prompts import load_prompt
from app.tracing import get_tracer

MAX_RETRIES = 2
MAX_EXPLANATION_WORDS = 80
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class ProposalOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation: str
    action: Action
    params: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_human_note: str | None = None

    @field_validator("explanation")
    @classmethod
    def _short(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("explanation is empty")
        if len(v.split()) > MAX_EXPLANATION_WORDS:
            raise ValueError(f"explanation has {len(v.split())} words (max {MAX_EXPLANATION_WORDS})")
        return v


# Schema handed to the API's structured-output mode (real runs). Every possible param key is
# optional; our own per-action validation decides which ones are required.
_PARAM_KEYS = sorted({k for spec in PARAM_SPEC.values() for k in spec})
PROPOSAL_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string"},
        "action": {"type": "string", "enum": [a.value for a in Action]},
        "params": {
            "type": "object",
            "properties": {k: {"type": "string"} for k in _PARAM_KEYS},
            "additionalProperties": False,
        },
        "confidence": {"type": "number"},
        "needs_human_note": {"type": ["string", "null"]},
    },
    "required": ["explanation", "action", "params", "confidence", "needs_human_note"],
    "additionalProperties": False,
}


class ValidationFailure(ValueError):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


@dataclass
class Attempt:
    n: int
    raw: str | None
    valid: bool
    error_category: str | None
    error: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: float


@dataclass
class ProposalResult:
    conflict_id: str
    status: ProposalStatus
    prompt_version: str
    model: str
    llm_mode: str
    output: ProposalOutput | None = None
    failure_category: str | None = None
    failure_reason: str | None = None
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def first_try_valid(self) -> bool:
        return bool(self.attempts) and self.attempts[0].valid

    @property
    def input_tokens(self) -> int:
        return sum(a.input_tokens for a in self.attempts)

    @property
    def output_tokens(self) -> int:
        return sum(a.output_tokens for a in self.attempts)

    @property
    def latency_ms(self) -> float:
        return round(sum(a.latency_ms for a in self.attempts), 2)

    def attempts_dicts(self) -> list[dict]:
        return [asdict(a) for a in self.attempts]


def llm_payload(conflict: Conflict) -> dict:
    """Exactly what the LLM may see: the conflict type and its evidence. Nothing else."""
    return {"type": conflict.type.value, "evidence": conflict.evidence}


def _allowed_actions_text(conflict: Conflict) -> str:
    return "\n".join(f"- {a.value}: params {json.dumps(PARAM_SPEC[a.value])}"
                     for a in sorted(COMPATIBLE[conflict.type], key=lambda a: a.value))


def parse_and_validate(raw: str, conflict: Conflict) -> ProposalOutput:
    text = _FENCE.sub("", raw.strip()).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValidationFailure("invalid_json", f"reply is not valid JSON: {e.msg}") from e
    if not isinstance(data, dict):
        raise ValidationFailure("invalid_json", "reply must be a JSON object")
    if isinstance(data.get("params"), dict):  # structured-output mode may send unused keys as absent/null
        data["params"] = {k: v for k, v in data["params"].items() if v is not None}
    try:
        out = ProposalOutput.model_validate(data)
    except ValidationError as e:
        errs = e.errors()
        if any(err["loc"][:1] == ("action",) for err in errs):
            raise ValidationFailure("disallowed_action",
                                    f"action {data.get('action')!r} is not in the allow-list") from e
        if any(err["loc"][:1] == ("explanation",) and "words" in str(err.get("msg")) for err in errs):
            raise ValidationFailure("explanation_too_long", errs[0]["msg"]) from e
        raise ValidationFailure("schema_error", "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}"
                                                         for x in errs)) from e
    try:
        check_compatible(out.action, conflict)
        out.params = validate_params(out.action, out.params, conflict)
    except ParamsError as e:
        raise ValidationFailure(e.category, str(e)) from e
    return out


def propose(conflict: Conflict, llm: LLMClient, prompt_version: str = "v1",
            max_retries: int = MAX_RETRIES) -> ProposalResult:
    tmpl = load_prompt(prompt_version)
    result = ProposalResult(conflict_id=conflict.id, status=ProposalStatus.FAILED, prompt_version=prompt_version,
                            model=llm.model_name, llm_mode=llm.mode)
    feedback = ""
    tracer = get_tracer()
    with tracer.start_as_current_span("proposer.propose") as span:
        span.set_attribute("tk.conflict_id", conflict.id)
        span.set_attribute("tk.conflict_type", conflict.type.value)
        span.set_attribute("tk.prompt_version", prompt_version)
        for n in range(1, max_retries + 2):
            user = tmpl.render_user(
                conflict_type=conflict.type.value,
                conflict_json=json.dumps(llm_payload(conflict)["evidence"], indent=2, sort_keys=True),
                allowed_actions=_allowed_actions_text(conflict),
                feedback=feedback,
            )
            try:
                res = llm.complete(system=tmpl.system, user=user, prompt_version=prompt_version,
                                   json_schema=PROPOSAL_JSON_SCHEMA)
            except LLMCallError as e:
                result.attempts.append(Attempt(n, None, False, e.category, str(e), 0, 0, 0.0))
                feedback = ""
                continue
            result.model = res.model
            try:
                out = parse_and_validate(res.text, conflict)
            except ValidationFailure as e:
                result.attempts.append(Attempt(n, res.text, False, e.category, str(e), res.input_tokens,
                                               res.output_tokens, res.latency_ms))
                feedback = (f"\nYour previous reply was rejected ({e.category}): {e}. "
                            "Reply again with one valid JSON object that follows the rules.\n")
                continue
            result.attempts.append(Attempt(n, res.text, True, None, None, res.input_tokens, res.output_tokens,
                                           res.latency_ms))
            result.status, result.output = ProposalStatus.PENDING_REVIEW, out
            break
        else:
            last = result.attempts[-1]
            result.failure_category, result.failure_reason = last.error_category, last.error
        span.set_attribute("tk.status", result.status.value)
        span.set_attribute("tk.attempts", len(result.attempts))
        span.set_attribute("tk.first_try_valid", result.first_try_valid)
        if result.output:
            span.set_attribute("tk.action", result.output.action.value)
        if result.failure_category:
            span.set_attribute("tk.failure_category", result.failure_category)
    return result
