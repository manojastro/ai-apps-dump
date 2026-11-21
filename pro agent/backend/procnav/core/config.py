"""Typed settings loaded from the environment, validated at startup."""

from __future__ import annotations

import json
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

DEV_SECRETS = {"dev-session-secret-change-me", "dev-control-token"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env",), extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    app_base_url: str = "http://localhost:5273"
    app_database_url: str = "postgresql+psycopg://procnav_app:devapp@127.0.0.1:55433/procnav"
    app_migration_database_url: str = "postgresql+psycopg://procnav_owner:devowner@127.0.0.1:55433/procnav"
    session_secret: str = "dev-session-secret-change-me"
    session_ttl_seconds: int = 8 * 3600
    cookie_secure: bool = False

    model_mode: Literal["fixture", "real"] = "fixture"
    model_provider: Literal["anthropic"] = "anthropic"
    model_name: str = "claude-opus-5-5"
    model_endpoint: str | None = None
    model_api_key: str | None = Field(default=None, repr=False)
    model_vision_enabled: bool = True
    # Price table used to compute per-run model cost in USD per million tokens.
    model_input_cost_per_mtok: Decimal = Decimal("4")
    model_output_cost_per_mtok: Decimal = Decimal("20")

    browser_allowed_origins: str = "http://127.0.0.1:8301,http://127.0.0.1:8302,http://127.0.0.1:8303"
    browser_headless: bool = True
    browser_action_timeout_ms: int = 10_000
    browser_navigation_timeout_ms: int = 20_000
    max_browser_actions: int = 80
    active_run_timeout_seconds: int = 900
    max_navigation_retries: int = 3
    max_run_cost: Decimal = Decimal("1.00")
    max_concurrent_runs: int = 2
    approval_ttl_seconds: int = 3600
    quote_max_age_seconds: int = 3600
    dry_run: bool = True

    evidence_dir: Path = REPO_ROOT / "var" / "evidence"
    evidence_retention_days: int = 30
    credentials_key: str = Field(default="", repr=False)
    # JSON object: credential_ref -> {"username": ..., "password": ...}. Prefer a secret store in production.
    supplier_credentials_json: str = Field(default="", repr=False)

    fixture_control_url: str = "http://127.0.0.1:8309"
    fixture_control_token: str = Field(default="dev-control-token", repr=False)

    otel_exporter_otlp_endpoint: str | None = None
    oidc_enabled: bool = False
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_tenant_id: str | None = None

    worker_id: str = "worker-local"
    job_lease_seconds: int = 60
    job_heartbeat_seconds: int = 15

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.browser_allowed_origins.split(",") if o.strip()]

    def supplier_credentials(self) -> dict[str, dict[str, str]]:
        if not self.supplier_credentials_json:
            return {}
        return json.loads(self.supplier_credentials_json)

    @model_validator(mode="after")
    def _validate(self) -> Settings:
        problems: list[str] = []
        if self.model_mode == "real" and not self.model_api_key:
            problems.append("MODEL_MODE=real requires MODEL_API_KEY")
        if self.max_browser_actions < 1 or self.max_browser_actions > 500:
            problems.append("MAX_BROWSER_ACTIONS must be between 1 and 500")
        if self.max_concurrent_runs < 1 or self.max_concurrent_runs > 8:
            problems.append("MAX_CONCURRENT_RUNS must be between 1 and 8")
        if self.approval_ttl_seconds < 60:
            problems.append("APPROVAL_TTL_SECONDS must be at least 60")
        for origin in self.allowed_origins:
            if not origin.startswith(("http://", "https://")) or origin.count("/") != 2:
                problems.append(f"BROWSER_ALLOWED_ORIGINS entry is not an origin: {origin}")
        if self.app_env == "production":
            if self.session_secret in DEV_SECRETS or len(self.session_secret) < 32:
                problems.append("SESSION_SECRET must be a unique value of at least 32 characters in production")
            if self.fixture_control_token in DEV_SECRETS:
                problems.append("FIXTURE_CONTROL_TOKEN must be changed in production")
            if not self.credentials_key:
                problems.append("CREDENTIALS_KEY is required in production")
            if not self.cookie_secure:
                problems.append("COOKIE_SECURE must be true in production")
        if not self.dry_run:
            # The MVP only ships simulated suppliers; real purchasing needs a reviewed adapter.
            problems.append("DRY_RUN=false is not supported in this release; real supplier adapters are not enabled")
        if self.oidc_enabled and not (self.oidc_issuer and self.oidc_audience and self.oidc_tenant_id):
            problems.append("OIDC_ENABLED requires OIDC_ISSUER, OIDC_AUDIENCE and OIDC_TENANT_ID")
        if problems:
            raise ValueError("Invalid configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
