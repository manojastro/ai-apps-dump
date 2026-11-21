from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.catalog import get_scenario
from app.repository import Repository
from services.agent import RemediationWorkflow


def seed_demo(repository: Repository, workflow: RemediationWorkflow, force: bool = False) -> list[str]:
    if repository.count("incidents") and not force:
        return []
    if force:
        repository.clear()
    seeded: list[str] = []
    cases = [
        ("crashloop", False),
        ("unhealthy_pod", False),
        ("excessive_latency", True),
        ("replica_shortage", False),
        ("bad_deployment", False),
        ("failing_job", False),
        ("unsafe_no_remediation", False),
    ]
    for scenario_id, fail in cases:
        incident = repository.create_incident(get_scenario(scenario_id).model_dump(mode="json"), fail)
        workflow.run(incident["id"])
        seeded.append(incident["id"])
    # Seeded history should demonstrate cooldown metrics without blocking a reviewer's new injection.
    repository.execute("UPDATE executions SET created_at=:historical",
                       {"historical": (datetime.now(UTC) - timedelta(minutes=5)).isoformat()})
    return seeded
