from __future__ import annotations

import pytest

from app.fixtures import SCENARIOS
from app.models import Incident
from app.repository import Repository
from app.workflow import InvestigationEngine


@pytest.fixture
def repository() -> Repository:
    return Repository("sqlite:///:memory:")


@pytest.fixture
def engine(repository: Repository) -> InvestigationEngine:
    return InvestigationEngine(repository, timeout_seconds=0.05)


def make_incident(scenario: str = "bad-deployment", suffix: str = "TEST") -> Incident:
    config = SCENARIOS[scenario]
    return Incident(
        id=f"INC-{suffix}",
        title=config["title"],
        service=config["service"],
        scenario=scenario,
        severity="SEV-2",
        alert_summary=config["impact"],
    )


@pytest.fixture
def incident(repository: Repository) -> Incident:
    value = make_incident()
    repository.save_incident(value)
    return value

