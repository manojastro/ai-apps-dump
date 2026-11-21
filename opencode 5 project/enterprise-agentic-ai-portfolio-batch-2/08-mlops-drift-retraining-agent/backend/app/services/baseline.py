"""Baseline champion training service."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.ml.data_generator import DriftKnobs
from backend.app.ml.pipeline import save_artifact, train_reference_champion
from backend.app.models.entities import ModelRegistry, TrainingRun
from backend.app.repositories.registry_repo import RegistryRepository
from backend.app.schemas.dto import TrainBaselineResponse
from backend.app.services.registry import default_thresholds


def train_baseline(session: Session, seed: int = 42, n_samples: int = 6000) -> TrainBaselineResponse:
    """Train a new champion on clean reference data and register it."""
    artifact = train_reference_champion(n_samples=n_samples, seed=seed)
    version = RegistryRepository.next_baseline_version(session)
    previous = RegistryRepository.current_champion(session)

    artifact_path = Path(settings.artifacts_dir) / f"champion_{version}.joblib"
    payload = {
        "version": version,
        "pipeline": artifact["pipeline"],
        "reference_df": artifact["reference_df"],
        "stats": artifact["stats"],
        "metrics": artifact["metrics"],
        "thresholds": {},
        "knobs": artifact["knobs"],
    }
    save_artifact(artifact_path, payload)
    thresholds = default_thresholds()

    if previous is not None:
        RegistryRepository.set_status(session, previous.version, "retired")

    row = RegistryRepository.add(
        session,
        ModelRegistry(
            version=version,
            status="champion",
            kind="baseline",
            algorithm="LogisticRegression",
            artifact_path=str(artifact_path),
            thresholds=thresholds,
            metrics={k: round(v, 6) for k, v in artifact["metrics"].items()},
            notes=f"baseline trained on {n_samples} clean rows, seed={seed}",
        ),
    )
    TrainingRunRepository_save(
        session,
        version=version,
        n_samples=n_samples,
        seed=seed,
        metrics=artifact["metrics"],
        hyperparams={"knobs": DriftKnobs().to_dict()},
    )
    return TrainBaselineResponse(
        version=row.version,
        status=row.status,
        metrics={k: round(v, 4) for k, v in artifact["metrics"].items()},
        thresholds=thresholds,
    )


def TrainingRunRepository_save(
    session: Session, version: str, n_samples: int, seed: int, metrics: dict, hyperparams: dict
) -> None:
    from backend.app.repositories.decision_repo import TrainingRunRepository

    TrainingRunRepository.save(
        session,
        TrainingRun(
            version=version,
            kind="baseline",
            algorithm="LogisticRegression",
            n_samples=n_samples,
            seed=seed,
            hyperparams=hyperparams,
            metrics={k: round(v, 6) for k, v in metrics.items()},
        ),
    )
