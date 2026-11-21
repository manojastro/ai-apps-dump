"""M2 tests: table-driven priority (all 9 combos) + routing."""

import pytest

from ticketsort.domain.models import Category, Priority, Service
from ticketsort.domain.priority import compute_priority
from ticketsort.domain.routing import route


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, Priority.P1),
        (1, 2, Priority.P2),
        (1, 3, Priority.P3),
        (2, 1, Priority.P2),
        (2, 2, Priority.P3),
        (2, 3, Priority.P4),
        (3, 1, Priority.P3),
        (3, 2, Priority.P4),
        (3, 3, Priority.P5),
    ],
)
def test_priority_matrix(impact: int, urgency: int, expected: Priority) -> None:
    assert compute_priority(impact, urgency) == expected


def test_priority_rejects_bad_values() -> None:
    with pytest.raises(ValueError):
        compute_priority(4, 1)


def test_route_exact_match() -> None:
    assert route(Category.DATABASE, Service.ORDERS_DB) == "DB-Ops"


def test_route_category_wildcard() -> None:
    assert route(Category.NETWORK, Service.SSO) == "Network-Ops"


def test_route_safe_default() -> None:
    assert route(Category.HARDWARE, Service.UNKNOWN) == "EUC"
