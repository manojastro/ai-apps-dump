from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Multi-Agent Incident RCA"
    environment: str = os.getenv("APP_ENV", "development")
    api_port: int = int(os.getenv("API_PORT", "8003"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./incident_rca.db")
    neo4j_uri: str = os.getenv("NEO4J_URI", "memory://")
    llm_mode: str = os.getenv("LLM_MODE", "deterministic")
    llm_model: str = os.getenv("LLM_MODEL", "deterministic-rules-v1")
    worker_timeout_seconds: float = float(os.getenv("WORKER_TIMEOUT_SECONDS", "3"))
    secret_patterns: tuple[str, ...] = tuple(
        value.strip()
        for value in os.getenv(
            "REDACT_PATTERNS", "password,passwd,api_key,apikey,secret,token,bearer"
        ).split(",")
        if value.strip()
    )
    cors_origins: tuple[str, ...] = tuple(
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "http://localhost:3003").split(",")
        if value.strip()
    )


settings = Settings()

