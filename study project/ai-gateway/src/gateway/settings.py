"""Central settings (pydantic-settings). No secrets hard-coded."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    admin_api_key: str = "admin-dev-key-change-me"
    database_path: str = "data/gateway.db"
    redis_url: str = "memory://stub"
    prices_path: str = "config/prices.yaml"
    routing_policy_path: str = "config/routing_policy.yaml"
    guardrail_profiles_path: str = "config/guardrail_profiles.yaml"
    cache_ttl_s: int = 300
    max_usd_per_run: float = 5.0


def get_settings() -> Settings:
    return Settings()
