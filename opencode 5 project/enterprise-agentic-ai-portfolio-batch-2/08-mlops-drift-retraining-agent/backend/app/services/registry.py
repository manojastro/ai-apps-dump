"""Local model registry service (drop-in replaceable with MLflow later)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.entities import ModelRegistry
from backend.app.repositories.registry_repo import RegistryRepository
from backend.app.ml.pipeline import load_artifact


class ModelRegistryService:
    """Versioned registry of champion, challenger, shadow and retired models."""

    def __init__(self) -> None:
        self._cache: dict[str, dict] = {}

    def register(
        self,
        session: Session,
        version: str,
        status: str,
        kind: str,
        algorithm: str,
        artifact_path: str,
        metrics: dict,
        thresholds: dict,
        notes: str = "",
    ) -> ModelRegistry:
        row = ModelRegistry(
            version=version,
            status=status,
            kind=kind,
            algorithm=algorithm,
            artifact_path=artifact_path,
            metrics=metrics,
            thresholds=thresholds,
            notes=notes,
        )
        return RegistryRepository.add(session, row)

    def get(self, session: Session, version: str) -> ModelRegistry | None:
        return RegistryRepository.get(session, version)

    def current_champion(self, session: Session) -> ModelRegistry | None:
        return RegistryRepository.current_champion(session)

    def artifact(self, session: Session, version: str) -> dict:
        if version in self._cache:
            return self._cache[version]
        row = RegistryRepository.get(session, version)
        if row is None or not row.artifact_path:
            raise FileNotFoundError(f"No artifact registered for version {version}")
        payload = load_artifact(Path(row.artifact_path))
        if len(self._cache) > 8:
            self._cache.clear()
        self._cache[version] = payload
        return payload

    def set_status(self, session: Session, version: str, status: str) -> ModelRegistry | None:
        row = RegistryRepository.set_status(session, version, status)
        self._cache.pop(version, None)
        return row

    def thresholds_for(self, session: Session) -> dict:
        """Deployment gate thresholds from the current champion or defaults."""
        champion = self.current_champion(session)
        if champion and champion.thresholds:
            return dict(champion.thresholds)
        return default_thresholds()

    def list_all(self, session: Session) -> list[ModelRegistry]:
        return RegistryRepository.list_all(session)


def default_thresholds() -> dict:
    """Default deployment gates derived from platform settings."""
    from backend.app.config import settings as s

    return {
        "cand_f1_tolerance": s.cand_f1_tolerance,
        "cand_auc_tolerance": s.cand_auc_tolerance,
        "cand_brier_eps": s.cand_brier_eps,
        "fairness_min_ratio": s.fairness_min_ratio,
        "robustness_max_drop": s.robustness_max_drop,
        "psi_meaningful": s.psi_meaningful,
        "tv_meaningful": s.tv_meaningful,
        "pred_rate_meaningful": s.pred_rate_meaningful,
        "missing_meaningful": s.missing_meaningful,
        "perf_f1_tol": s.perf_f1_tol,
        "min_projected_benefit": s.min_projected_benefit,
        "min_labeled_samples": s.min_labeled_samples,
        "artifacts_dir": str(s.artifacts_dir),
    }


registry_service = ModelRegistryService()
