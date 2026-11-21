from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    data_mode: Literal["mock", "live"] = "mock"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "sqlite:///./data/aegis.db"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    llm_api_key: str = ""
    llm_base_url: str = "https://api.x.ai/v1"
    llm_model: str = "grok-4.5"
    xai_api_key: str = ""

    firecrawl_api_key: str = ""
    firecrawl_base_url: str = "https://api.firecrawl.dev"
    firecrawl_max_calls_per_plan: int = 8
    cache_ttl_seconds: int = 21600

    max_llm_calls_per_plan: int = 12
    max_plan_runtime_seconds: int = 180
    max_retries: int = 2
    vda_opt_in_cap_pct: float = 3.0
    concentration_cap_pct: float = 15.0
    source_coverage_veto_pct: float = 30.0
    max_request_bytes: int = 2_000_000

    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def resolved_llm_key(self) -> str:
        return self.llm_api_key or self.xai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
