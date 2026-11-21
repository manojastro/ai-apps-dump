"""Runtime config via environment. No secrets hard-coded."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    itsm_db_path: str = "data/itsm.db"
    itsm_host: str = "127.0.0.1"
    itsm_port: int = 8001
    approval_default_minutes: int = 10
    log_cap_lines: int = 200
    mcp_bearer_token: str = "dev-bearer-token-change-me"
    opscopilot_url: str = ""
    mcp_transport: str = "stdio"


settings = Settings()
