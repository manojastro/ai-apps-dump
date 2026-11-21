"""Application settings, read from the environment or .env files.

Why one settings object: every tunable lives in one typed place, so a missing or
malformed value fails at start-up instead of halfway through a request.
"""
from __future__ import annotations

import secrets
from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env.devdb"),
        extra="ignore",
    )

    environment: str = "dev"
    database_url: str = "postgresql+psycopg://revenueos:revenueos@localhost:5432/revenueos"

    jwt_secret: str = ""
    jwt_expire_minutes: int = 480
    demo_user_password: str = ""

    anthropic_api_key: str = ""
    llm_model: str = "claude-opus-5-5"
    llm_effort: str = "medium"
    llm_max_tool_turns: int = 8

    data_as_of: date = date(2026, 10, 31)
    copilot_rate_limit_per_minute: int = 20
    enable_scheduler: bool = False
    cors_origins: str = "http://localhost:3000"
    mlflow_tracking_uri: str = ""

    data_dir: Path = BACKEND_DIR / "data" / "synthetic"
    artifact_dir: Path = BACKEND_DIR / "artifacts"

    @model_validator(mode="after")
    def _secure_defaults(self) -> Settings:
        """Refuse weak secrets in production; use a throwaway one in dev."""
        placeholder = self.jwt_secret in ("", "replace-me")
        if placeholder and self.environment == "prod":
            raise ValueError("JWT_SECRET must be set when ENVIRONMENT=prod")
        if placeholder:
            self.jwt_secret = secrets.token_urlsafe(48)
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
