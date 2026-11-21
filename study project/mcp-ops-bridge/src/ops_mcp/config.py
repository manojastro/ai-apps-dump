"""ops_mcp config (env-driven, offline defaults)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    itsm_db_path: str = "data/itsm.db"
    mcp_bearer_token: str = "dev-bearer-token-change-me"
    opscopilot_url: str = ""
    log_cap_lines: int = 200
    mcp_transport: str = "stdio"


settings = Settings()
