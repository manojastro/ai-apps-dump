from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Agent Reliability Control Plane"
    environment: str = os.getenv("APP_ENV", "development")
    database_path: Path = Path(
        os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "reliability.db"))
    )
    llm_mode: str = os.getenv("LLM_MODE", "mock")
    llm_model: str = os.getenv("LLM_MODEL", "deterministic-rca-v1")
    api_key: str = os.getenv("API_KEY", "")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:8101").split(",")
        if origin.strip()
    )
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    max_trace_steps: int = int(os.getenv("MAX_TRACE_STEPS", "200"))


def get_settings() -> Settings:
    return Settings()
