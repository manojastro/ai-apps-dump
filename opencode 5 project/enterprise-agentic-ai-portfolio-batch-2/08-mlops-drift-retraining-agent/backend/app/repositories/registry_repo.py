"""Data access helpers for the model registry."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import ModelRegistry


class RegistryRepository:
    """CRUD operations for registered model versions."""

    @staticmethod
    def add(session: Session, row: ModelRegistry) -> ModelRegistry:
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @staticmethod
    def get(session: Session, version: str) -> ModelRegistry | None:
        return session.scalar(select(ModelRegistry).where(ModelRegistry.version == version))

    @staticmethod
    def get_by_status(session: Session, status: str) -> list[ModelRegistry]:
        return list(
            session.scalars(
                select(ModelRegistry)
                .where(ModelRegistry.status == status)
                .order_by(ModelRegistry.id.desc())
            )
        )

    @staticmethod
    def current_champion(session: Session) -> ModelRegistry | None:
        rows = RegistryRepository.get_by_status(session, "champion")
        return rows[0] if rows else None

    @staticmethod
    def set_status(session: Session, version: str, status: str) -> ModelRegistry | None:
        row = RegistryRepository.get(session, version)
        if row is not None:
            row.status = status
            session.commit()
            session.refresh(row)
        return row

    @staticmethod
    def retire_all_of_status(session: Session, status: str) -> None:
        for row in RegistryRepository.get_by_status(session, status):
            row.status = "retired"
        session.commit()

    @staticmethod
    def list_all(session: Session) -> list[ModelRegistry]:
        return list(session.scalars(select(ModelRegistry).order_by(ModelRegistry.id)))

    @staticmethod
    def next_baseline_version(session: Session) -> str:
        highest = 0
        for row in RegistryRepository.list_all(session):
            if row.version.startswith("v"):
                try:
                    highest = max(highest, int(row.version[1:]))
                except ValueError:
                    continue
        return f"v{highest + 1}"

    @staticmethod
    def next_candidate_version(session: Session) -> str:
        count = len(
            [r for r in RegistryRepository.list_all(session) if r.kind == "candidate"]
        )
        return f"cand-{count + 1:03d}"
