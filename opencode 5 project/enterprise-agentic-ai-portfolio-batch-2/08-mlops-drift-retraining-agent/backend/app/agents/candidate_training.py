"""Candidate training agent producing challenger GradientBoosting models."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.agents.common import load_window
from backend.app.config import settings
from backend.app.ml.data_generator import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    DriftKnobs,
    TARGET,
    generate_customer_data,
)
from backend.app.ml.pipeline import (
    build_candidate_pipeline,
    compute_classification_metrics,
    predict_pipeline,
    save_artifact,
)
from backend.app.models.entities import TrainingRun
from backend.app.repositories.decision_repo import TrainingRunRepository
from backend.app.repositories.registry_repo import RegistryRepository
from backend.app.repositories.results_repo import WindowRepository
from backend.app.schemas.dto import TrainCandidateOutput


class CandidateTrainingAgent:
    """Trains a challenger on window data with an untouched holdout split."""

    def train(
        self,
        session: Session,
        source_window_id: int | None = None,
        seed: int = 7,
        n_samples: int = 4000,
        inject_bad: bool = False,
        bad_n_samples: int = 140,
        bad_label_noise: float = 0.35,
    ) -> TrainCandidateOutput:
        version = RegistryRepository.next_candidate_version(session)
        rng = np.random.default_rng(seed)

        if inject_bad:
            knobs = DriftKnobs(label_noise=bad_label_noise, mean_shift=0.3)
            frame = generate_customer_data(bad_n_samples, seed=13, knobs=knobs)
            train_frame = frame
            holdout_frame = frame
            hyperparams = {
                "mode": "bad_injection",
                "knobs": knobs.to_dict(),
                "train_n": len(train_frame),
                "val_seed": seed + 101,
                "val_n": min(2500, max(500, n_samples // 2)),
            }
        elif source_window_id is not None:
            window = load_window(session, source_window_id)
            frame = WindowRepository.load_frame(window)
            knobs = DriftKnobs.from_dict(window.knobs or {})
            perm = rng.permutation(len(frame))
            cut = int(len(frame) * 0.8)
            train_idx, holdout_idx = perm[:cut], perm[cut:]
            train_frame = frame.iloc[train_idx].reset_index(drop=True)
            holdout_frame = frame.iloc[holdout_idx].reset_index(drop=True)
            hyperparams = {
                "mode": "window_split",
                "source_window_id": source_window_id,
                "knobs": knobs.to_dict(),
                "train_n": len(train_frame),
                "holdout_n": len(holdout_frame),
                "val_seed": seed + 101,
                "val_n": 2500,
                "split_seed": seed,
            }
        else:
            knobs = DriftKnobs()
            frame = generate_customer_data(n_samples, seed=seed, knobs=knobs)
            train_frame = frame
            holdout_frame = generate_customer_data(
                min(2000, n_samples), seed=seed + 5, knobs=knobs
            )
            hyperparams = {
                "mode": "fresh_clean",
                "knobs": knobs.to_dict(),
                "train_n": len(train_frame),
                "val_seed": seed + 101,
                "val_n": 2500,
            }

        features = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c in train_frame.columns]
        pipeline = build_candidate_pipeline()
        pipeline.fit(train_frame[features], train_frame[TARGET])

        pred, prob = predict_pipeline(pipeline, holdout_frame[features])
        metrics = compute_classification_metrics(holdout_frame[TARGET], pred, prob)

        artifact_path = Path(settings.artifacts_dir) / f"{version}.joblib"
        save_artifact(
            artifact_path,
            {"version": version, "pipeline": pipeline, "hyperparams": hyperparams},
        )

        RegistryRepository.add(session, _registry_row(version, metrics, str(artifact_path)))
        TrainingRunRepository.save(
            session,
            TrainingRun(
                version=version,
                kind="candidate",
                algorithm="GradientBoostingClassifier",
                n_samples=int(len(train_frame)),
                seed=seed,
                source_window_id=source_window_id,
                hyperparams=hyperparams,
                metrics={k: round(v, 6) for k, v in metrics.items()},
            ),
        )
        return TrainCandidateOutput(
            version=version,
            kind="candidate",
            algorithm="GradientBoostingClassifier",
            n_samples=int(len(train_frame)),
            metrics={k: round(v, 4) for k, v in metrics.items()},
            source_knobs=knobs.to_dict(),
        )


def _registry_row(version: str, metrics: dict, artifact_path: str):
    from backend.app.models.entities import ModelRegistry

    return ModelRegistry(
        version=version,
        status="challenger",
        kind="candidate",
        algorithm="GradientBoostingClassifier",
        artifact_path=artifact_path,
        metrics={k: round(float(v), 6) for k, v in metrics.items()},
        thresholds={},
        notes="trained candidate awaiting evaluation",
    )
