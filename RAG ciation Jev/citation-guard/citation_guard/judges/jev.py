"""JevJudge: one Choice question to TypeSafe's Jev model via typesafe-sdk.

SDK usage verified against docs.typesafe.ai on 2026-11-21 (typesafe-sdk 0.7.5):
  - AsyncTypeSafeClient(model=..., retry=RetryPolicy(...)); key from TYPESAFE_API_KEY
  - await client.system_one(state, questions) -> SystemOneResponse
  - response.choices["relation"] -> ChoiceAnswer(choice, confidence, probabilities)
  - response.usage.input_tokens (int | None), response.request_id, response.model
"""

from __future__ import annotations

import time

from ..config import Config
from .base import CRITERIA, INSTRUCTIONS, JudgeResult, build_state, normalise_probs


class JevJudge:
    name = "jev"
    is_live = True

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.model = cfg.jev.model
        if self.model in ("jev-latest", "jev-preview"):
            raise ValueError("pin a concrete Jev version in config.yaml (jev.model), not an alias")
        self.pricing = cfg.pricing["jev"]
        self._client = None

    async def __aenter__(self) -> "JevJudge":
        from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

        retry = RetryPolicy(max_retries=self.cfg.jev.max_retries, timeout=self.cfg.jev.timeout_s)
        # Raises TypeSafeError here if TYPESAFE_API_KEY is missing or invalid.
        self._client = AsyncTypeSafeClient(model=self.model, retry=retry, timeout=self.cfg.jev.timeout_s)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None:
            await self._client.__aexit__(*exc)
            self._client = None

    @staticmethod
    def questions():
        from typesafe_sdk import Choice

        return {"relation": Choice(instructions=INSTRUCTIONS, criteria=dict(CRITERIA))}

    async def judge(self, claim: str, quote: str, passage: str) -> JudgeResult:
        if self._client is None:
            raise RuntimeError("use `async with JevJudge(cfg) as judge:`")
        t0 = time.perf_counter()
        resp = await self._client.system_one(build_state(claim, quote, passage), self.questions())
        latency = (time.perf_counter() - t0) * 1000
        ans = resp.choices["relation"]
        tokens = resp.usage.input_tokens if resp.usage else None
        return JudgeResult(
            judge=self.name,
            model=resp.model or self.model,
            probabilities=normalise_probs(dict(ans.probabilities)),
            confidence=float(ans.confidence),
            latency_ms=latency,
            input_tokens=tokens,
            output_tokens=resp.usage.output_tokens if resp.usage else None,
            estimated_cost_usd=self.pricing.cost(tokens, 0),
            request_id=resp.request_id,
            raw={"choice": ans.choice, "probabilities": dict(ans.probabilities), "confidence": ans.confidence},
        )


async def list_models() -> list[dict]:
    from typesafe_sdk import AsyncTypeSafeClient

    async with AsyncTypeSafeClient() as client:
        resp = await client.models.list()
        return [{"name": m.name, "release_date": m.release_date, "description": m.description} for m in resp.models]
