"""sysparm_query parser tests (M2 learner-core concept)."""

import pytest

from mock_itsm.query import build_where, parse_sysparm_query


def test_empty() -> None:
    assert parse_sysparm_query(None) == {}
    assert parse_sysparm_query("") == {}
    assert parse_sysparm_query("   ") == {}


def test_single() -> None:
    assert parse_sysparm_query("state=New") == {"state": "New"}


def test_multi_and() -> None:
    assert parse_sysparm_query("state=New^priority=1^service=vpn") == {
        "state": "New",
        "priority": "1",
        "service": "vpn",
    }


def test_value_with_equals_kept() -> None:
    assert parse_sysparm_query("short_description=a=b") == {"short_description": "a=b"}


def test_bad_parts_raise() -> None:
    with pytest.raises(ValueError):
        parse_sysparm_query("stateNew")
    with pytest.raises(ValueError):
        parse_sysparm_query("state=New^^priority=1")
    with pytest.raises(ValueError):
        parse_sysparm_query("=New")


def test_build_where_allowlist() -> None:
    clause, params = build_where({"state": "New"}, {"state", "priority"})
    assert clause == "state = ?"
    assert params == ["New"]
    with pytest.raises(ValueError):
        build_where({"number; DROP TABLE incident": "x"}, {"number"})


def test_build_where_empty() -> None:
    clause, params = build_where({}, {"state"})
    assert clause == "1=1"
    assert params == []
