"""Environment-based configuration. Secrets stay in env, never in code/logs."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # pragma: no cover - dotenv is in requirements
    def _load_dotenv(*args: object, **kwargs: object) -> bool:
        return False


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    google_api_key: str = ""
    neuro_san_host: str = "localhost"
    neuro_san_http_port: int = 8080
    nsflow_host: str = "localhost"
    nsflow_port: int = 4173
    agent_manifest_file: str = "./registries/manifest.hocon"
    agent_tool_path: str = "./coded_tools"
    thinking_file: str = "/tmp/agent_thinking.txt"
    log_level: str = "INFO"
    db_path: str = "./data/autopilot.db"
    servicenow_instance_url: str = ""
    servicenow_user: str = ""
    servicenow_pwd: str = ""

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.google_api_key and "YOUR_" not in self.google_api_key)

    @property
    def has_servicenow(self) -> bool:
        return bool(self.servicenow_instance_url and "YOUR-" not in self.servicenow_instance_url
                    and self.servicenow_user and self.servicenow_pwd)


def load_settings(env_file: str = ".env") -> Settings:
    """Load .env (if present) then read env vars. Never prints secrets."""
    _load_dotenv(env_file)
    instance = _get("SERVICENOW_INSTANCE_URL") or _get("SERVICENOW_INSTANCE")
    user = _get("SERVICENOW_USER") or _get("SERVICENOW_USERNAME")
    pwd = _get("SERVICENOW_PWD") or _get("SERVICENOW_PASSWORD")
    try:
        http_port = int(_get("NEURO_SAN_SERVER_HTTP_PORT", "8080"))
    except ValueError:
        http_port = 8080
    try:
        nsflow_port = int(_get("NSFLOW_PORT", "4173"))
    except ValueError:
        nsflow_port = 4173
    return Settings(
        google_api_key=_get("GOOGLE_API_KEY"),
        neuro_san_host=_get("NEURO_SAN_SERVER_HOST", "localhost"),
        neuro_san_http_port=http_port,
        nsflow_host=_get("NSFLOW_HOST", "localhost"),
        nsflow_port=nsflow_port,
        agent_manifest_file=_get("AGENT_MANIFEST_FILE", "./registries/manifest.hocon"),
        agent_tool_path=_get("AGENT_TOOL_PATH", "./coded_tools"),
        thinking_file=_get("THINKING_FILE", "/tmp/agent_thinking.txt"),
        log_level=_get("LOG_LEVEL", "INFO").upper(),
        db_path=_get("DB_PATH", "./data/autopilot.db"),
        servicenow_instance_url=instance,
        servicenow_user=user,
        servicenow_pwd=pwd,
    )
