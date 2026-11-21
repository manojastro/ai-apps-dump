"""App settings. All config comes from env — nothing hard-coded. No secrets ever logged."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ticketsort"
    llm_provider: str = "openai"  # openai | azure_openai | anthropic | ollama
    llm_model: str = "gpt-4o-mini"
    prompt_version: str = "v1"
    confidence_threshold: float = 0.6
    max_usd_per_run: float = 1.0
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()
