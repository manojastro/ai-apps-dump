"""Config: pydantic-settings for env + YAML eval config (thresholds, target)."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GateThresholds(BaseModel):
    faithfulness: float = 0.50
    hit_rate_at_5: float = 0.50
    refusal_accuracy: float = 0.80
    p95_latency_ms: float = 5000.0


class EvalFileConfig(BaseModel):
    target: str = "stub"
    target_url: str = "http://localhost:8000"
    top_k: int = 5
    repeat: int = 1
    thresholds: GateThresholds = Field(default_factory=GateThresholds)


class Settings(BaseSettings):
    """Env-driven settings. Offline mock-first: no API keys needed."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "stub"
    opscopilot_url: str = "http://localhost:8000"
    max_usd_per_run: float = 5.0


def load_eval_config(path: str | Path = "eval_config.yaml") -> EvalFileConfig:
    """Load eval_config.yaml; return defaults if the file is missing."""
    p = Path(path)
    if not p.exists():
        return EvalFileConfig()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return EvalFileConfig.model_validate(data)
