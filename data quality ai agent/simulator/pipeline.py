"""Executable replay of an orders transform. No golden root-cause labels are exposed here."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.models.domain import Candidate, Contract, Operation, ReplayResult, Scenario
from pydantic import Field


class Fixture(Contract):
    as_of: str
    source_rows: list[dict[str, Any]]
    ledger: dict[str, float]
    customer_master: dict[str, str]
    amount_divisor: int = 100
    dependency_statuses: list[int] = Field(default_factory=lambda: [200])
    deployment: dict[str, Any] = Field(default_factory=dict)


def load_fixture(scenario: Scenario) -> Fixture:
    source = json.loads((Path(__file__).parent / "fixtures" / "orders.json").read_text())
    fixture = Fixture.model_validate(source)
    fixture.deployment = {"version": "orders-2.8.0", "changed": []}
    if scenario == Scenario.SCHEMA_DRIFT:
        for row in fixture.source_rows:
            row["customerId"] = row.pop("customer_id")
        fixture.deployment["changed"] = ["Upstream renamed customer_id to customerId"]
    elif scenario == Scenario.NULL_SPIKE:
        for row in fixture.source_rows[:3]:
            row["customer_id"] = None
        fixture.deployment["changed"] = ["Customer enrichment lookup disabled upstream"]
    elif scenario == Scenario.DUPLICATES:
        fixture.source_rows += deepcopy(fixture.source_rows[:2])
        fixture.deployment["changed"] = ["Ingestion retry without idempotency key"]
    elif scenario == Scenario.TRANSFORMATION:
        fixture.amount_divisor = 1
        fixture.deployment["changed"] = ["Amount divisor changed from 100 to 1"]
    elif scenario == Scenario.DEPENDENCY:
        fixture.dependency_statuses = [503, 200]
        fixture.deployment["changed"] = ["Orders API returns 503 on first request"]
    return fixture


def replay(original: Fixture, candidate: Candidate) -> ReplayResult:
    fixture = original.model_copy(deep=True)
    operations = set(candidate.operations)
    budget = 3 if Operation.RETRY_DEPENDENCY in operations else 1
    calls = 0
    for index in range(budget):
        calls += 1
        status = fixture.dependency_statuses[min(index, len(fixture.dependency_statuses) - 1)]
        if status == 200:
            break
    else:
        return ReplayResult(
            rows=[],
            completed=False,
            errors=["upstream HTTP failure"],
            dependency_calls=calls,
            applied_operations=candidate.operations,
        )
    rows = fixture.source_rows
    if Operation.DEDUPLICATE in operations:
        seen: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = row["transaction_id"]
            if key in seen and seen[key] != row:
                return ReplayResult(
                    rows=[],
                    completed=False,
                    errors=[f"conflicting duplicate requires manual investigation: {key}"],
                    dependency_calls=calls,
                    applied_operations=candidate.operations,
                )
            seen[key] = row
        rows = list({row["transaction_id"]: row for row in rows}.values())
    divisor = candidate.amount_divisor or fixture.amount_divisor
    if Operation.CORRECT_AMOUNT in operations and candidate.amount_divisor is None:
        divisor = 100
    output, errors = [], []
    for source in rows:
        row = dict(source)
        if Operation.MAP_CUSTOMER in operations and "customerId" in row:
            row["customer_id"] = row.pop("customerId")
        if Operation.RESTORE_CUSTOMER in operations and row.get("customer_id") is None:
            row["customer_id"] = fixture.customer_master.get(row["transaction_id"])
        try:
            output.append(
                {
                    "transaction_id": row["transaction_id"],
                    "customer_id": row["customer_id"],
                    "amount": row["amount_cents"] / divisor,
                    "occurred_at": row["occurred_at"],
                }
            )
        except (KeyError, TypeError, ZeroDivisionError) as error:
            errors.append(f"transform failed: {type(error).__name__}: {error}")
    return ReplayResult(
        rows=output,
        completed=not errors,
        errors=errors,
        dependency_calls=calls,
        applied_operations=candidate.operations,
    )
