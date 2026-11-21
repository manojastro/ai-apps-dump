"""Tests for the deterministic citation validator."""

from opscopilot.citations import parse_citations, validate_citations


def test_parse_citations() -> None:
    pairs = parse_citations("See [KB0001 §Workaround] and [SOP-VPN-01 §Steps].")
    assert ("KB0001", "Workaround") in pairs
    assert ("SOP-VPN-01", "Steps") in pairs


def test_valid_citations() -> None:
    check = validate_citations("Fix in [KB0001 §Workaround].", {"KB0001", "KB0002"})
    assert check.is_valid
    assert check.valid == ["KB0001"]
    assert check.invalid == []


def test_invalid_citations_flagged() -> None:
    check = validate_citations("Fix in [KB0999 §Workaround].", {"KB0001"})
    assert not check.is_valid
    assert check.invalid == ["KB0999"]


def test_no_citations_yields_empty() -> None:
    check = validate_citations("No citations here.", {"KB0001"})
    assert check.cited_ids == []
    assert check.is_valid  # nothing to invalidate
