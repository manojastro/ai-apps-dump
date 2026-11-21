"""Shared loading helpers for agents."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.api.errors import DomainError
from backend.app.models.entities import ModelRegistry, MonitoringWindow
from backend.app.repositories.results_repo import WindowRepository
from backend.app.repositories.registry_repo import RegistryRepository
from backend.app.services.registry import registry_service


def load_champion(session: Session) -> tuple[ModelRegistry, dict]:
    """Return the current champion row and its artifact bundle."""
    row = RegistryRepository.current_champion(session)
    if row is None:
        raise DomainError(409, "no champion model registered; train a baseline first")
    payload = registry_service.artifact(session, row.version)
    return row, payload


def load_window(session: Session, window_id: int) -> MonitoringWindow:
    """Fetch a window or raise 404."""
    window = WindowRepository.get(session, window_id)
    if window is None:
        raise DomainError(404, f"monitoring window {window_id} not found")
    return window


def load_candidate(session: Session, version: str) -> ModelRegistry:
    """Fetch a registered candidate or raise 404."""
    row = RegistryRepository.get(session, version)
    if row is None:
        raise DomainError(404, f"model version {version} not found")
    return row
