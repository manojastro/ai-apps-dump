"""Configuration: config.yaml for settings, .env for secrets."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

ROOT = Path(os.environ.get("CITATION_GUARD_ROOT", Path(__file__).resolve().parents[1]))


class PricingCfg(BaseModel):
    usd_per_million_input_tokens: float
    usd_per_million_output_tokens: float = 0.0
    checked_on: str
    source: str = ""

    def cost(self, input_tokens: int | None, output_tokens: int | None = 0) -> float | None:
        if input_tokens is None:
            return None
        out = output_tokens or 0
        return (
            input_tokens * self.usd_per_million_input_tokens
            + out * self.usd_per_million_output_tokens
        ) / 1_000_000


class JevCfg(BaseModel):
    model: str
    timeout_s: float = 30.0
    max_retries: int = 3


class LLMProviderCfg(BaseModel):
    base_url: str
    api_key_env: str


class LLMModelCfg(BaseModel):
    model: str
    temperature: float = 0.0
    max_tokens: int = 1000
    max_claims_per_answer: int = 4
    pricing: PricingCfg | None = None


class GateCfg(BaseModel):
    pass_supports: float = 0.80
    fail_contradicts: float = 0.50


class QuoteCfg(BaseModel):
    min_chars: int = 20


class PassageCfg(BaseModel):
    window_chars: int = 1500


class RunCfg(BaseModel):
    max_api_calls_per_run: int = 500
    concurrency: int = 5
    seed: int = 7519


class TuningCfg(BaseModel):
    pass_supports_grid: list[float] = Field(default_factory=lambda: [0.8])
    fail_contradicts_grid: list[float] = Field(default_factory=lambda: [0.5])
    max_wrong_pass_rate: float = 0.0


class ApiCfg(BaseModel):
    judge: str = "mock"


class Config(BaseModel):
    jev: JevCfg
    pricing: dict[str, PricingCfg]
    llm_provider: LLMProviderCfg
    generator: LLMModelCfg
    llm_judge: LLMModelCfg
    gate: GateCfg = GateCfg()
    quote: QuoteCfg = QuoteCfg()
    passage: PassageCfg = PassageCfg()
    run: RunCfg = RunCfg()
    tuning: TuningCfg = TuningCfg()
    api: ApiCfg = ApiCfg()


@lru_cache(maxsize=4)
def load_config(path: str | None = None) -> Config:
    load_dotenv(ROOT / ".env", override=False)
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return Config.model_validate(data)


def paths() -> dict[str, Path]:
    return {
        "root": ROOT,
        "sources": ROOT / "data" / "sources",
        "processed": ROOT / "data" / "processed",
        "eval": ROOT / "data" / "eval",
        "runs": ROOT / "runs",
        "reports": ROOT / "reports",
    }
