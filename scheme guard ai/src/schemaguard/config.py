"""Central configuration, loaded from environment variables (prefix SCHEMAGUARD_) and .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCHEMAGUARD_", env_file=".env", extra="ignore")

    # Where local state lives (SQLite DB, sandboxes, artifacts). Git-ignored.
    home: Path = Field(default=REPO_ROOT / ".schemaguard")
    # Postgres URL. When empty, SQLite under `home` is used for checkpoints, runs and lineage.
    database_url: str = ""

    # The pipeline SchemaGuard protects, and the git repo PRs/branches are made in.
    pipeline_dir: Path = Field(default=REPO_ROOT / "demo_pipeline")
    target_repo: Path | None = None  # defaults to <home>/target_repo (a git copy of pipeline_dir)

    # Schema registry: "file" (registry dir) or a Confluent Schema Registry URL.
    registry_url: str = ""
    registry_dir: Path | None = None  # defaults to <home>/registry

    # LLM
    llm_provider: Literal["fake", "azure", "openai", "anthropic"] = "fake"
    llm_model: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_deployment: str = ""
    llm_timeout_s: float = 60.0

    # Budgets and loop limits
    run_budget_usd: float = 0.50
    run_budget_tokens: int = 200_000
    max_fix_retries: int = 3

    # Guardrails
    patch_allowed_paths: tuple[str, ...] = ("sql/", "dags/", "tests/")
    patch_max_lines: int = 400

    # Sandbox
    sandbox_timeout_s: float = 120.0

    # GitHub (optional, only used after human approval)
    github_token: str = ""
    github_repo: str = ""  # "owner/name"

    # API: if set, every request except /health must send header X-API-Key with this value.
    api_key: str = ""
    worker_poll_s: float = 10.0

    # Observability
    otel_console: bool = False
    log_level: str = "INFO"

    @property
    def sqlite_path(self) -> Path:
        return self.home / "state.db"

    @property
    def resolved_registry_dir(self) -> Path:
        return self.registry_dir or (self.home / "registry")

    @property
    def resolved_target_repo(self) -> Path:
        return self.target_repo or (self.home / "target_repo")

    @property
    def sandbox_root(self) -> Path:
        return self.home / "sandbox"

    @property
    def artifacts_dir(self) -> Path:
        return self.home / "artifacts"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
