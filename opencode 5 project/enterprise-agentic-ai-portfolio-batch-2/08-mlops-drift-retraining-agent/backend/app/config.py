"""Application configuration loaded from environment variables with enterprise-safe defaults."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Settings:
    """Runtime settings for the drift detection and retraining service."""

    def __init__(self) -> None:
        self.database_url: str = _env_str(
            "DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'data' / 'app.db').as_posix()}"
        )
        self.artifacts_dir: Path = Path(
            _env_str("ARTIFACTS_DIR", str(PROJECT_ROOT / "artifacts"))
        )
        self.window_data_dir: Path = Path(
            _env_str("WINDOW_DATA_DIR", str(PROJECT_ROOT / "data" / "windows"))
        )
        self.frontend_dir: Path = PROJECT_ROOT / "frontend"

        self.llm_mode: str = _env_str("LLM_MODE", "mock")
        self.llm_api_key: str = _env_str("LLM_API_KEY", "")
        self.llm_base_url: str = _env_str("LLM_BASE_URL", "https://api.openai.com/v1")
        self.llm_model: str = _env_str("LLM_MODEL", "gpt-4o-mini")

        self.min_labeled_samples: int = _env_int("MIN_LABELED_SAMPLES", 400)
        self.psi_meaningful: float = _env_float("PSI_MEANINGFUL", 0.25)
        self.tv_meaningful: float = _env_float("TV_MEANINGFUL", 0.20)
        self.pred_rate_meaningful: float = _env_float("PRED_RATE_MEANINGFUL", 0.08)
        self.missing_meaningful: float = _env_float("MISSING_MEANINGFUL", 0.10)
        self.perf_f1_tol: float = _env_float("PERF_F1_TOL", 0.02)

        self.fairness_min_ratio: float = _env_float("FAIRNESS_MIN_RATIO", 0.80)
        self.cand_f1_tolerance: float = _env_float("CAND_F1_TOLERANCE", 0.01)
        self.cand_brier_eps: float = _env_float("CAND_BRIER_EPS", 0.02)
        self.cand_auc_tolerance: float = _env_float("CAND_AUC_TOLERANCE", 0.0)
        self.robustness_max_drop: float = _env_float("ROBUSTNESS_MAX_DROP", 0.12)
        self.min_projected_benefit: float = _env_float("MIN_PROJECTED_BENEFIT", 0.15)

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.window_data_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
