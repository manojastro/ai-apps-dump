import math
from collections import Counter
from datetime import datetime
from typing import Any

from app.models.domain import ReplayResult, ValidationResult
from simulator.pipeline import Fixture

REQUIRED_VALIDATORS = (
    "SchemaValidator",
    "RowCountValidator",
    "NullRateValidator",
    "DuplicateValidator",
    "FreshnessValidator",
    "DataTypeValidator",
    "BusinessRuleValidator",
    "TransformationValidator",
    "DownstreamContractValidator",
    "PipelineCompletionValidator",
)
OUTPUT_FIELDS = {"transaction_id", "customer_id", "amount", "occurred_at"}


def _fresh(timestamp: Any, as_of: str) -> bool:
    try:
        age = (datetime.fromisoformat(as_of) - datetime.fromisoformat(timestamp)).total_seconds()
        return 0 <= age <= 3600
    except (ValueError, TypeError):
        return False


def _number(value: Any) -> bool:
    return type(value) in (float, int) and math.isfinite(value)


def validate(fixture: Fixture, replay: ReplayResult) -> list[ValidationResult]:
    rows = replay.rows
    ids = [r.get("transaction_id") for r in rows]
    nulls = sum(any(r.get(k) is None for k in OUTPUT_FIELDS) for r in rows)
    duplicates = len(ids) - len(set(ids))
    mismatches = [
        r.get("transaction_id")
        for r in rows
        if not (
            _number(r.get("amount"))
            and r.get("transaction_id") in fixture.ledger
            and math.isclose(r["amount"], fixture.ledger[r["transaction_id"]], abs_tol=0.000001)
        )
    ]
    checks = [
        (
            bool(rows) and all(set(r) == OUTPUT_FIELDS for r in rows),
            sorted(OUTPUT_FIELDS),
            sorted({k for r in rows for k in r}),
            "Output schema must match the warehouse contract",
        ),
        (
            len(rows) == len(fixture.ledger),
            len(fixture.ledger),
            len(rows),
            "No transactions may disappear or be invented",
        ),
        (bool(rows) and nulls == 0, 0, nulls, "All required fields must be populated"),
        (duplicates == 0, 0, duplicates, "Transaction identifiers must be unique"),
        (
            bool(rows) and all(_fresh(r.get("occurred_at"), fixture.as_of) for r in rows),
            "0..3600 seconds old at fixture clock",
            [r.get("occurred_at") for r in rows],
            "Freshness uses the captured incident clock, not the machine clock",
        ),
        (
            bool(rows)
            and all(
                _number(r.get("amount"))
                and all(isinstance(r.get(k), str) for k in OUTPUT_FIELDS - {"amount"})
                for r in rows
            ),
            "finite numeric amount, string identifiers and timestamp",
            [{k: type(v).__name__ for k, v in r.items()} for r in rows],
            "Actual runtime types checked",
        ),
        (
            bool(rows)
            and all(_number(r.get("amount")) and 0 < r["amount"] <= 100000 for r in rows),
            "0 < amount <= 100000",
            [r.get("amount") for r in rows],
            "Orders must have a positive finite business amount",
        ),
        (
            bool(rows) and not mismatches,
            fixture.ledger,
            mismatches,
            "Transformation invariant: per-transaction currency units match independent ledger",
        ),
        (
            set(ids) == set(fixture.ledger)
            and all(
                r.get("customer_id") == fixture.customer_master.get(str(r.get("transaction_id")))
                for r in rows
            ),
            "Exact transaction set and customer master relationship",
            ids,
            "Downstream join integrity is required",
        ),
        (
            replay.completed and not replay.errors,
            "Pipeline completed without errors",
            replay.errors,
            "Replay completion is reported by the executable pipeline",
        ),
    ]
    return [
        ValidationResult(
            validator=name,
            status="PASS" if passed else "FAIL",
            expected=expected,
            actual=actual,
            evidence=evidence,
        )
        for name, (passed, expected, actual, evidence) in zip(
            REQUIRED_VALIDATORS, checks, strict=True
        )
    ]


def all_passed(results: list[ValidationResult]) -> bool:
    """Fail closed on missing, duplicated, unexpected or downgraded mandatory checks."""
    return Counter(r.validator for r in results) == Counter(REQUIRED_VALIDATORS) and all(
        r.status == "PASS" and r.severity == "critical" for r in results
    )
