"""Runtime settings, read from environment variables and the git-ignored `.env` file.

Model and endpoint names live only here (from the environment), never in code.
"""

from typing import Literal

from psycopg.conninfo import make_conninfo
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Runtime switches
    invoiceflow_backend: Literal["local", "databricks"] = "local"
    invoiceflow_kill_switch: bool = False
    invoiceflow_state_dir: str = ".invoiceflow"  # local SQLite stores (git-ignored)

    # Local Postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "invoiceflow"
    postgres_user: str = "invoiceflow"
    postgres_password: SecretStr | None = None

    # Databricks
    databricks_config_profile: str | None = None
    databricks_warehouse_id: str | None = None
    invoiceflow_catalog: str = "invoiceflow"
    invoiceflow_schema: str = "ap"
    invoiceflow_eval_schema: str = "eval"
    invoiceflow_volume: str = "raw"
    ai_search_endpoint: str | None = None
    ai_search_index: str | None = None

    # LLM
    llm_provider: Literal["stub", "databricks", "azure_openai"] = "stub"
    llm_endpoint: str | None = None
    embedding_endpoint: str | None = None
    llm_cost_per_1k_input_tokens: float = 0.0  # set from your price sheet for cost reports
    llm_cost_per_1k_output_tokens: float = 0.0
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str | None = None

    # Agent budgets
    agent_max_tool_steps: int = 12
    agent_max_tokens: int = 60000
    agent_max_seconds: float = 120.0
    agent_max_tool_retries: int = 2

    # Approvals service (v1 dev tokens; v2 Entra ID OIDC)
    approvals_auth: Literal["dev", "oidc"] = "dev"
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None

    # Observability
    mlflow_tracing: bool = False

    def postgres_conninfo(self) -> str:
        if self.postgres_password is None:
            raise ConfigError("POSTGRES_PASSWORD is not set; copy .env.example to .env")
        return make_conninfo(
            host=self.postgres_host,
            port=self.postgres_port,
            dbname=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
        )

    def require(self, name: str) -> str:
        value = getattr(self, name)
        if not value:
            raise ConfigError(f"{name.upper()} is not set (see .env.example)")
        return str(value)
