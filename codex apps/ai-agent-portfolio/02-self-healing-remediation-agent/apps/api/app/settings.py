from functools import lru_cache
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[3])))


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'selfheal.db'}"
    allowed_namespace: str = "selfheal-demo"
    policy_path: str = str(PROJECT_ROOT / "config" / "policies.yaml")
    sandbox_mode: str = "memory"
    llm_provider: str = "deterministic"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = ""
    operator_token: str = "demo-operator-token"
    viewer_token: str = "demo-viewer-token"
    csrf_token: str = "demo-csrf-token"
    cors_origins: str = "http://localhost:3002,http://127.0.0.1:3002"
    seed_on_start: bool = True

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
