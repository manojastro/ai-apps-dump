from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///.runtime/recoverygraph.db"
    checkpoint_url: str = ".runtime/checkpoints.db"
    demo_mode: bool = True
    demo_force_first_fix_fail: bool = False
    max_remediation_attempts: int = Field(default=3, ge=1, le=10)
    llm_provider: Literal["mock", "openai", "azure"] = "mock"
    llm_model: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_base_url: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: SecretStr = SecretStr("")
    azure_openai_api_version: str = "2024-10-21"
    llm_timeout_seconds: int = Field(default=30, ge=1, le=120)
    llm_input_cost_per_million: float | None = Field(default=None, ge=0)
    llm_output_cost_per_million: float | None = Field(default=None, ge=0)
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = "text-embedding-3-small"
    api_token: SecretStr = SecretStr("")
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    write_requests_per_minute: int = Field(default=60, ge=1)
    otel_exporter_otlp_endpoint: str | None = None

    @model_validator(mode="after")
    def validate_provider(self):
        if not self.demo_mode and self.llm_provider == "mock":
            raise ValueError("Set a real LLM_PROVIDER when DEMO_MODE=false")
        if self.llm_provider != "mock" and not self.llm_model:
            raise ValueError("LLM_MODEL is required for online providers")
        if self.llm_provider == "openai" and not self.llm_api_key.get_secret_value():
            raise ValueError("LLM_API_KEY is required for OpenAI-compatible providers")
        if self.llm_provider == "azure" and (
            not self.azure_openai_endpoint or not self.azure_openai_api_key.get_secret_value()
        ):
            raise ValueError("Azure endpoint and key are required")
        return self

    def prepare_paths(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            Path(self.database_url.removeprefix("sqlite:///")).parent.mkdir(
                parents=True, exist_ok=True
            )
        if not self.checkpoint_url.startswith("postgresql://"):
            Path(self.checkpoint_url).parent.mkdir(parents=True, exist_ok=True)
