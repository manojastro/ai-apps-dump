"""LLMJudge: baseline that asks a small chat LLM for a probability per label.

IMPORTANT: these are prompted estimates, not calibrated probabilities. Thresholds tuned
for Jev must not be reused for this judge; the report tunes them separately on dev.
"""

from __future__ import annotations

import json
import os
import time

from ..config import Config
from .base import CRITERIA, INSTRUCTIONS, LABELS, JudgeResult, build_state, normalise_probs

SYSTEM = (
    INSTRUCTIONS
    + "\n\nLabels:\n"
    + "\n".join(f"- {k}: {v}" for k, v in CRITERIA.items())
    + "\n\nReply with only a JSON object giving your probability for each label, summing to 1, "
    'for example {"supports": 0.1, "contradicts": 0.2, "says_nothing": 0.7}.'
)


def make_openai_client(cfg: Config):
    from openai import AsyncOpenAI

    key = os.environ.get(cfg.llm_provider.api_key_env)
    if not key:
        raise RuntimeError(f"{cfg.llm_provider.api_key_env} is not set")
    return AsyncOpenAI(base_url=cfg.llm_provider.base_url, api_key=key, max_retries=3, timeout=60)


class LLMJudge:
    name = "llm"
    is_live = True

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.model = cfg.llm_judge.model
        self._client = None

    async def __aenter__(self) -> "LLMJudge":
        self._client = make_openai_client(self.cfg)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def judge(self, claim: str, quote: str, passage: str) -> JudgeResult:
        if self._client is None:
            raise RuntimeError("use `async with LLMJudge(cfg) as judge:`")
        t0 = time.perf_counter()
        resp = await self._client.chat.completions.create(
            model=self.model,
            temperature=self.cfg.llm_judge.temperature,
            max_tokens=self.cfg.llm_judge.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(build_state(claim, quote, passage), ensure_ascii=False)},
            ],
        )
        latency = (time.perf_counter() - t0) * 1000
        text = resp.choices[0].message.content or ""
        parse_error = None
        try:
            parsed = json.loads(text)
            probs = normalise_probs({k: float(parsed.get(k, 0.0)) for k in LABELS})
        except (ValueError, TypeError, AttributeError) as e:
            parse_error = str(e)
            probs = normalise_probs({})  # uniform -> lands in HUMAN_REVIEW
        usage = resp.usage
        tin = usage.prompt_tokens if usage else None
        tout = usage.completion_tokens if usage else None
        pricing = self.cfg.llm_judge.pricing
        return JudgeResult(
            judge=self.name,
            model=resp.model or self.model,
            probabilities=probs,
            confidence=max(probs.values()),
            latency_ms=latency,
            input_tokens=tin,
            output_tokens=tout,
            estimated_cost_usd=pricing.cost(tin, tout) if pricing else None,
            request_id=getattr(resp, "id", None),
            raw={"text": text, "parse_error": parse_error, "calibrated": False},
        )
