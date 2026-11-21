"""Central configuration via pydantic-settings (env prefix OPS_)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime knobs for the mock-first slice. No secrets required."""

    model_config = SettingsConfigDict(env_prefix="OPS_", env_file=".env", extra="ignore")

    app_name: str = "OpsCopilot P1"
    top_k_default: int = 5
    rrf_k: int = 60
    # RRF fused scores are small (≈0.033 for rank-1 in both lists).
    # Refuse when the best fused score is below this. 0.029 is the midpoint
    # between the strongest smoke-set false positive (0.0254) and the weakest
    # true positive (0.0325) — see reports/smoke_*.json. Single-list-only
    # matches top out at 1/(60+1) ≈ 0.0164, so they always refuse.
    refuse_threshold: float = 0.029
    rerank_enabled: bool = True
    embedding_dim: int = 128
    corpus_dir: str = "data/corpus"
    max_usd_per_run: float = 0.0


def get_settings() -> Settings:
    """Return a fresh Settings instance (cheap; reads env on construction)."""
    return Settings()
