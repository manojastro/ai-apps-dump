"""Runtime configuration, read from environment variables (see ../.env.example)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPREADLENS_", env_file=".env", extra="ignore")

    env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://spreadlens:spreadlens@localhost:5433/spreadlens"

    # Storage: "local" for development, "gcs" for deployment (object storage adapter).
    storage_backend: Literal["local", "gcs"] = "local"
    storage_root: Path = Path("./data/files")
    gcs_bucket: str | None = None

    # Agent mode. "demo" = deterministic adapters (no credentials needed).
    # "live" = eve agents (model calls via Vercel AI Gateway). Never silently falls back.
    agent_mode: Literal["demo", "live"] = "demo"
    eve_document_understanding_url: str = "http://127.0.0.1:3101"
    eve_table_extraction_url: str = "http://127.0.0.1:3102"
    eve_financial_mapping_url: str = "http://127.0.0.1:3103"
    eve_reconciliation_url: str = "http://127.0.0.1:3104"
    eve_analyst_pack_url: str = "http://127.0.0.1:3105"
    eve_service_token: str | None = None  # bearer for eve routes (Secret Manager in deployment)
    agent_tool_token: str | None = None  # eve tools call back into the engine with this token
    live_model_max_retries: int = 2
    live_request_timeout_s: float = 120.0

    # OCR: "local" (RapidOCR, ONNX, runs on this machine) or "none".
    ocr_provider: Literal["local", "none"] = "local"
    ocr_dpi: int = 150
    ocr_max_retries: int = 1
    ocr_low_confidence: float = 0.80

    # Upload / processing limits
    max_upload_bytes: int = 25 * 1024 * 1024
    max_pdf_pages: int = 200
    max_xlsx_uncompressed_bytes: int = 100 * 1024 * 1024
    max_xlsx_compression_ratio: float = 100.0
    max_xlsx_sheets: int = 50
    stage_timeout_s: float = 300.0

    # Per-document budgets
    budget_max_model_calls: int = 40
    budget_max_cost_usd: float = 2.00
    budget_max_ocr_pages: int = 60

    # Worker
    worker_concurrency: int = 4
    worker_lease_s: int = 120
    worker_poll_s: float = 0.5
    task_max_attempts: int = 3
    run_worker_in_api: bool = True  # dev convenience; compose runs a separate worker

    # Auth
    session_ttl_hours: int = 12
    seed_password: str = Field(default="spreadlens-demo")
    cookie_secure: bool = False

    # Retention
    default_retention_days: int = 365

    # Observability
    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

    # Cost estimation for live mode (USD per 1M tokens), configurable per model
    model_price_input_per_mtok: float = 3.0
    model_price_output_per_mtok: float = 15.0

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


PARSER_VERSION = "extract-1.3.0"
TAXONOMY_VERSION = "spreadlens-tax-1.0"
RULESET_VERSION = "rules-1.2.0"
METRICS_VERSION = "metrics-1.1.0"
