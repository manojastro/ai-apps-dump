"""Application configuration.

All settings come from environment variables (or a local ``.env`` file). Secrets are
held as ``SecretStr`` so they never appear in ``repr()`` output or logs.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application -------------------------------------------------------------
    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "AegisRemediate AI"
    log_level: str = "INFO"
    log_json: bool = True
    database_url: str = "sqlite:///./aegis_dev.db"
    checkpoint_database_url: str | None = None  # defaults to database_url
    secret_key: SecretStr = SecretStr("dev-only-insecure-secret-change-me")
    session_ttl_minutes: int = 480
    cookie_secure: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    seed_on_start: bool = False
    workflow_workers: int = 4
    login_rate_limit_per_minute: int = 10

    # --- AI provider -------------------------------------------------------------
    ai_provider: Literal["mock", "openai", "anthropic", "gemini"] = "mock"
    ai_model: str = ""
    ai_api_key: SecretStr = SecretStr("")
    ai_base_url: str = ""
    ai_timeout_seconds: float = 60.0
    ai_max_retries: int = 2
    ai_cost_input_per_1k: float | None = None
    ai_cost_output_per_1k: float | None = None

    # --- ServiceNow ----------------------------------------------------------------
    servicenow_mode: Literal["mock", "real"] = "mock"
    servicenow_instance_url: str = ""
    servicenow_client_id: str = ""
    servicenow_client_secret: SecretStr = SecretStr("")
    servicenow_username: str = ""
    servicenow_password: SecretStr = SecretStr("")
    servicenow_change_table: str = "change_request"
    servicenow_cmdb_table: str = "cmdb_ci_server"
    servicenow_service_table: str = "cmdb_ci_service"
    servicenow_remediation_table: str = ""
    servicenow_timeout_seconds: float = 20.0
    enable_servicenow_writes: bool = False

    # --- Microsoft Defender for Endpoint -----------------------------------------------
    defender_mode: Literal["mock", "real"] = "mock"
    defender_tenant_id: str = ""
    defender_client_id: str = ""
    defender_client_secret: SecretStr = SecretStr("")
    defender_api_base: str = "https://api.securitycenter.microsoft.com"

    # --- Threat intelligence --------------------------------------------------------
    threat_intel_mode: Literal["offline", "live"] = "offline"
    kev_feed_url: str = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    epss_api_url: str = "https://api.first.org/data/v1/epss"
    nvd_api_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    nvd_api_key: SecretStr = SecretStr("")
    threat_intel_cache_hours: int = 24
    threat_intel_snapshot_path: str = str(DATA_DIR / "fixtures" / "threat_intel_snapshot.json")

    # --- Policy -----------------------------------------------------------------------
    separation_of_duties: bool = True

    # --- Observability --------------------------------------------------------------
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = ""
    otel_exporter_otlp_endpoint: str = ""

    # --- MCP ---------------------------------------------------------------------------
    mcp_actor_email: str = "analyst@northstar.example"
    mcp_allowed_tools: str = "*"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def servicenow_configured(self) -> bool:
        has_oauth = bool(self.servicenow_client_id and self.servicenow_client_secret.get_secret_value())
        has_basic = bool(self.servicenow_username and self.servicenow_password.get_secret_value())
        return bool(self.servicenow_instance_url) and (has_oauth or has_basic)

    @property
    def defender_configured(self) -> bool:
        return bool(self.defender_tenant_id and self.defender_client_id and self.defender_client_secret.get_secret_value())

    def validate_for_production(self) -> list[str]:
        problems: list[str] = []
        if self.app_env == "production":
            if "dev-only" in self.secret_key.get_secret_value() or len(self.secret_key.get_secret_value()) < 32:
                problems.append("SECRET_KEY must be a random value of at least 32 characters in production")
            if not self.cookie_secure:
                problems.append("COOKIE_SECURE must be true in production (HTTPS)")
            if self.is_sqlite:
                problems.append("DATABASE_URL must point to PostgreSQL in production")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
