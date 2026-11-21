import asyncio
import difflib
import json
from collections import Counter
from typing import Any

from app.models.domain import Candidate, Evidence, Incident, ReplayResult
from app.security.policy import CONTROLLED_OPERATIONS
from simulator.pipeline import Fixture, load_fixture, replay


class LocalSimulatorAdapter:
    async def fixture(self, incident: Incident) -> Fixture:
        return await asyncio.to_thread(load_fixture, incident.scenario)

    async def read_snapshot(self, incident: Incident) -> dict[str, Any]:
        fixture = await self.fixture(incident)
        ids = [r["transaction_id"] for r in fixture.source_rows]
        return {
            "row_count": len(ids),
            "expected_rows": len(fixture.ledger),
            "null_customer_count": sum(
                r.get("customer_id", r.get("customerId")) is None for r in fixture.source_rows
            ),
            "duplicate_count": len(ids) - len(set(ids)),
            "duplicate_ids": [key for key, count in Counter(ids).items() if count > 1],
        }

    async def read_health(self, incident: Incident) -> dict[str, Any]:
        fixture = await self.fixture(incident)
        return {
            "worker_healthy": True,
            "database_healthy": True,
            "upstream_statuses": fixture.dependency_statuses,
            "source": "local simulator health probes",
        }

    async def read_changes(self, incident: Incident) -> dict[str, Any]:
        fixture = await self.fixture(incident)
        return {**fixture.deployment, "amount_divisor": fixture.amount_divisor}

    async def investigate(self, incident: Incident, branch: str) -> Evidence:
        if branch == "schema":
            fixture = await self.fixture(incident)
            fields = sorted({k for row in fixture.source_rows for k in row})
            facts = {
                "observed_fields": fields,
                "required_field": "customer_id",
                "customer_id_missing": "customer_id" not in fields,
                "customerId_present": "customerId" in fields,
            }
            summary = "Compare upstream fields against the customer identifier contract"
        elif branch == "quality":
            facts = await self.read_snapshot(incident)
            summary = "Measured row volume, required values and duplicate transaction IDs"
        elif branch in ("infrastructure", "dependency"):
            health = await self.read_health(incident)
            facts = (
                health
                if branch == "infrastructure"
                else {
                    "response_statuses": health["upstream_statuses"],
                    "upstream_failing": health["upstream_statuses"][0] != 200,
                    "retry_budget": 3,
                }
            )
            summary = (
                "Captured worker health" if branch == "infrastructure" else "Orders API responses"
            )
        elif branch == "change":
            facts = await self.read_changes(incident)
            summary = "Compared deployed transformation and recent source changes"
        else:
            raise ValueError(f"Unknown investigation branch: {branch}")
        return Evidence(
            id=f"EV-{branch.upper()}-001",
            branch=branch,
            facts=facts,
            summary=summary,
            source=f"simulator://orders_daily/{branch}",
        )

    async def apply(self, fixture: Fixture, candidate: Candidate) -> Candidate:
        if not set(candidate.operations).issubset(CONTROLLED_OPERATIONS):
            raise PermissionError("Sandbox only supports the documented controlled operations")
        return Candidate.model_validate(candidate.model_dump())

    async def replay(self, fixture: Fixture, candidate: Candidate) -> ReplayResult:
        return await asyncio.to_thread(replay, fixture, candidate)

    def artifact(self, incident: Incident, candidate: Candidate) -> dict[str, Any]:
        before = json.dumps({"pipeline": incident.pipeline_id, "recovery": []}, indent=2)
        after = json.dumps(
            {"pipeline": incident.pipeline_id, "recovery": candidate.model_dump(mode="json")},
            indent=2,
        )
        diff = "\n".join(
            difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile="a/recovery-plan.json",
                tofile="b/recovery-plan.json",
                lineterm="",
            )
        )
        return {
            "title": candidate.summary,
            "kind": "reviewable_recovery_plan",
            "filename": "recovery-plan.diff",
            "diff": diff,
            "deployment_executed": False,
            "rollback": "Discard this proposal; original pipeline and source remain unchanged.",
            "instructions": "Review the controlled operations and port them to a vendor adapter.",
        }
