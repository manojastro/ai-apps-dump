"""Settings read from environment variables (and an optional .env file).

Settings are re-read on every call to get_settings() so tests can monkeypatch the
environment. Secrets (ANTHROPIC_API_KEY) are never stored on this object: the Anthropic
SDK reads the key from the environment itself.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:  # optional: load .env for local runs
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
except ImportError:  # pragma: no cover
    pass


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _path(name: str, default: str) -> Path:
    raw = os.getenv(name) or default
    p = Path(raw)
    return p if p.is_absolute() else ROOT / p


@dataclass(frozen=True)
class Settings:
    llm_mode: str
    model: str
    effort: str
    max_tokens: int
    structured_output: bool
    use_fallbacks: bool
    price_input_per_mtok: float
    price_output_per_mtok: float
    prompt_version: str
    mock_profile: str
    otel_endpoint: str | None
    generated_dir: Path
    sandbox_dir: Path
    state_db: Path
    ground_truth: Path
    regressions_dir: Path
    results_dir: Path


def get_settings() -> Settings:
    mode = (os.getenv("LLM_MODE") or "mock").strip().lower()
    if mode not in {"mock", "real"}:
        raise ValueError(f"LLM_MODE must be 'mock' or 'real', got {mode!r}")
    return Settings(
        llm_mode=mode,
        model=os.getenv("LLM_MODEL") or "claude-opus-5-5",
        effort=os.getenv("LLM_EFFORT") or "medium",
        max_tokens=int(os.getenv("LLM_MAX_TOKENS") or 2048),
        structured_output=_bool("LLM_STRUCTURED_OUTPUT", True),
        use_fallbacks=_bool("LLM_USE_FALLBACKS", True),
        price_input_per_mtok=float(os.getenv("LLM_PRICE_INPUT_PER_MTOK") or 4.0),
        price_output_per_mtok=float(os.getenv("LLM_PRICE_OUTPUT_PER_MTOK") or 20.0),
        prompt_version=os.getenv("PROMPT_VERSION") or "v1",
        mock_profile=os.getenv("MOCK_PROFILE") or "clean",
        otel_endpoint=os.getenv("PHOENIX_COLLECTOR_ENDPOINT") or None,
        generated_dir=_path("TK_GENERATED_DIR", "data/generated"),
        sandbox_dir=_path("TK_SANDBOX_DIR", "data/sandbox"),
        state_db=_path("TK_STATE_DB", "data/state.db"),
        ground_truth=_path("TK_GROUND_TRUTH", "data/generator/ground_truth.json"),
        regressions_dir=_path("TK_REGRESSIONS_DIR", "evals/regressions"),
        results_dir=_path("TK_RESULTS_DIR", "evals/results"),
    )
