"""Unit tests: versions, CPE ranges, normalisation, risk engine, EPSS/KEV parsing, redaction, state machine."""

from __future__ import annotations

import pytest

from app.approvals.state_machine import PLAN_TRANSITIONS, InvalidTransition, check_transition, lifecycle_stage
from app.core.types import canonical_hash
from app.core.versions import Version, match_cpe_ranges
from app.integrations.cisa.kev import normalize_kev_entry
from app.integrations.epss.epss import parse_epss_row
from app.security.redaction import REDACTED, redact, redact_text
from app.services.normalization import (
    NormalizationError,
    RawFinding,
    dedup_key,
    normalize_cve_id,
    normalize_finding,
    normalize_severity,
    severity_from_cvss,
)
from app.services.risk_engine import RiskInputs, RiskPolicy, calculate_risk, classify


# ------------------------------------------------------------------ versions
@pytest.mark.parametrize(
    ("a", "b", "op"),
    [
        ("2.14.1", "2.15.0", "<"),
        ("2.15", "2.15.0", "=="),
        ("9.8p1", "9.8", ">"),
        ("8.9p1", "9.6", "<"),
        ("2.0-beta9", "2.0", "<"),
        ("5.15.0-91", "5.15.25", "<"),
        ("2023.11.3", "2023.11.4", "<"),
        ("0.120", "121", "<"),
        ("116.0.5845.187", "115.0.5790.170", ">"),
        ("1.10.0", "1.9", ">"),
    ],
)
def test_version_ordering(a: str, b: str, op: str) -> None:
    va, vb = Version(a), Version(b)
    assert {"<": va < vb, ">": va > vb, "==": va == vb}[op]


LOG4J = [
    {
        "criteria": "cpe:2.3:a:apache:log4j:*:*:*:*:*:*:*:*",
        "vendor": "apache",
        "product": "log4j",
        "version": "*",
        "version_start_including": "2.13.0",
        "version_end_excluding": "2.15.0",
    },
]
JENKINS = [
    {
        "criteria": "cpe:2.3:a:jenkins:jenkins:*:*:*:*:lts:*:*:*",
        "vendor": "jenkins",
        "product": "jenkins",
        "version": "*",
        "version_end_excluding": "2.426.3",
    },
    {
        "criteria": "cpe:2.3:a:jenkins:jenkins:*:*:*:*:-:*:*:*",
        "vendor": "jenkins",
        "product": "jenkins",
        "version": "*",
        "version_end_excluding": "2.442",
    },
]


def test_cpe_range_match_and_fixed_version() -> None:
    m = match_cpe_ranges(LOG4J, "apache", "log4j", "2.14.1")
    assert m.matched and m.fixed_version == "2.15.0"
    assert not match_cpe_ranges(LOG4J, "apache", "log4j", "2.17.1").matched
    assert not match_cpe_ranges(LOG4J, "apache", "commons_text", "2.14.1").matched


def test_cpe_edition_is_respected() -> None:
    assert match_cpe_ranges(JENKINS, "jenkins", "jenkins", "2.426.2", "lts").matched
    assert not match_cpe_ranges(JENKINS, "jenkins", "jenkins", "2.426.3", "lts").matched  # weekly range must not apply
    assert match_cpe_ranges(JENKINS, "jenkins", "jenkins", "2.440", None).matched


def test_cpe_exact_version_with_update() -> None:
    ranges = [
        {"criteria": "cpe:2.3:a:openbsd:openssh:8.5:p1:*:*:*:*:*:*", "vendor": "openbsd", "product": "openssh", "version": "8.5"}
    ]
    assert match_cpe_ranges(ranges, "openbsd", "openssh", "8.5p1").matched
    assert not match_cpe_ranges(ranges, "openbsd", "openssh", "8.6p1").matched


# ------------------------------------------------------------------ normalisation
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CVE-2021-44228", "CVE-2021-44228"),
        ("cve-2021-44228", "CVE-2021-44228"),
        ("CVE 2023 4863", "CVE-2023-4863"),
        ("vuln cve_2024_3094 found", "CVE-2024-3094"),
        ("CVE-21-1", None),
        ("CVE-2099-0001", None),
        ("", None),
        (None, None),
        ("CVE-1998-0001", None),
    ],
)
def test_cve_normalisation(raw: str | None, expected: str | None) -> None:
    assert normalize_cve_id(raw) == expected


def test_severity_aliases() -> None:
    assert normalize_severity("Important") == "high"
    assert normalize_severity("4") == "critical"
    assert normalize_severity("weird") == "unknown"
    assert severity_from_cvss(9.8) == "critical" and severity_from_cvss(None) == "unknown"


def test_normalize_finding_rejects_invalid_and_missing_asset() -> None:
    with pytest.raises(NormalizationError) as exc:
        normalize_finding(RawFinding(scanner="csv", cve_id="CVE-XX", asset_identifier=None))
    assert len(exc.value.reasons) == 2


def test_normalize_finding_derives_and_warns() -> None:
    nf = normalize_finding(
        RawFinding(
            scanner="CSV",
            cve_id="cve-2024-3094",
            asset_identifier="Host.Example.",
            cvss_score="9.1",
            last_seen="2026-01-01T00:00:00Z",
            first_seen="2026-02-01T00:00:00Z",
        )
    )
    assert nf.cve_id == "CVE-2024-3094" and nf.asset_identifier == "host.example"
    assert nf.scanner_severity == "critical"
    assert any("derived" in w for w in nf.warnings) and any("swapped" in w for w in nf.warnings)
    assert nf.first_seen < nf.last_seen


def test_dedup_key_is_case_insensitive_and_scanner_scoped() -> None:
    assert dedup_key("csv", "Host", "cve-2021-1", "Log4j") == dedup_key("CSV", "host", "CVE-2021-1", "log4j")
    assert dedup_key("csv", "host", "CVE-2021-1", None) != dedup_key("json", "host", "CVE-2021-1", None)


# ------------------------------------------------------------------ risk engine
FULL = RiskInputs(cvss_score=10.0, epss_probability=0.97, kev_listed=True, asset_criticality="critical", internet_exposed=True)


def test_risk_maximum_score() -> None:
    r = calculate_risk(FULL)
    assert r.score == 100 and r.risk_level == "critical" and r.priority == "P1"
    assert r.coverage == 1.0 and r.missing_factors == [] and r.score_lower == r.score_upper == 100


@pytest.mark.parametrize(
    ("factor", "value", "points"),
    [
        ("cvss", 7.5, 18.75),
        ("cvss", 0.0, 0.0),
        ("epss", 0.6, 25.0),
        ("epss", 0.2, 17.5),
        ("epss", 0.05, 8.75),
        ("epss", 0.001, 2.5),
    ],
)
def test_individual_factors(factor: str, value: float, points: float) -> None:
    inputs = RiskInputs(
        cvss_score=value if factor == "cvss" else 5.0,
        epss_probability=value if factor == "epss" else 0.0,
        kev_listed=False,
        asset_criticality="low",
        internet_exposed=False,
    )
    assert calculate_risk(inputs).factors[factor].points == points


def test_kev_and_exposure_and_criticality_points() -> None:
    r = calculate_risk(FULL)
    assert r.factors["kev"].points == 25 and r.factors["internet_exposure"].points == 10
    assert r.factors["asset_criticality"].points == 15
    low = calculate_risk(RiskInputs(10.0, 0.97, False, "low", False))
    assert low.factors["kev"].points == 0 and low.factors["asset_criticality"].points == 3


def test_missing_data_is_not_zero_risk() -> None:
    r = calculate_risk(
        RiskInputs(cvss_score=9.8, epss_probability=0.99, kev_listed=True, asset_criticality=None, internet_exposed=None)
    )
    assert set(r.missing_factors) == {"asset_criticality", "internet_exposure"}
    assert r.coverage == 0.75
    assert r.score_lower == 74 and r.score_upper == 100 and r.score == 87  # imputed at 50 %
    assert r.requires_immediate_review
    assert any("imputed" in line for line in r.rationale)


def test_low_coverage_forces_review() -> None:
    r = calculate_risk(RiskInputs(None, None, None, "medium", False))
    assert r.coverage == 0.25 and r.requires_immediate_review


def test_contextual_risk_differs_from_severity() -> None:
    dev = calculate_risk(RiskInputs(9.8, 0.034, False, "low", False))
    prod = calculate_risk(RiskInputs(9.8, 0.034, False, "critical", True))
    assert dev.risk_level == "low" and prod.score > dev.score


@pytest.mark.parametrize(
    ("score", "level"),
    [(100, "critical"), (85, "critical"), (84, "high"), (70, "high"), (69, "medium"), (40, "medium"), (39, "low"), (0, "low")],
)
def test_classification_thresholds(score: int, level: str) -> None:
    assert classify(RiskPolicy(), score) == level


def test_policy_validation() -> None:
    with pytest.raises(ValueError):
        RiskPolicy(weights={"cvss": 50, "epss": 25, "kev": 25, "asset_criticality": 15, "internet_exposure": 10})
    with pytest.raises(ValueError):
        RiskPolicy(level_thresholds={"critical": 50, "high": 70, "medium": 40})
    custom = RiskPolicy(weights={"cvss": 30, "epss": 20, "kev": 30, "asset_criticality": 10, "internet_exposure": 10})
    assert custom.policy_version != RiskPolicy().policy_version


def test_out_of_range_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_risk(RiskInputs(11.0, 0.1, False, "low", False))
    with pytest.raises(ValueError):
        calculate_risk(RiskInputs(5.0, 1.5, False, "low", False))


# ------------------------------------------------------------------ EPSS / KEV parsing
def test_epss_parsing() -> None:
    assert parse_epss_row({"cve": "cve-2021-44228", "epss": "0.97", "percentile": "0.99", "date": "2026-10-25"}) == {
        "cve": "CVE-2021-44228",
        "epss": 0.97,
        "percentile": 0.99,
        "date": "2026-10-25",
    }
    assert parse_epss_row({"cve": "CVE-1", "epss": "abc", "percentile": "0.1"}) is None
    assert parse_epss_row({"cve": "CVE-1", "epss": "1.5", "percentile": "0.1"}) is None
    assert parse_epss_row({"cve": "CVE-1"}) is None


def test_kev_normalisation_drops_unknown_fields() -> None:
    out = normalize_kev_entry({"cveID": "CVE-1", "dateAdded": "2021-12-10", "injected": "x" * 10, "notes": "y" * 5000})
    assert "injected" not in out and len(out["notes"]) == 2000


# ------------------------------------------------------------------ misc
def test_redaction() -> None:
    data = {
        "password": "hunter2",
        "nested": {"api_key": "abc", "ok": "Bearer abc.def.ghi"},
        "policy": "aegis-demo-risk-policy-v1-1234abcd",
    }
    out = redact(data)
    assert out["password"] == REDACTED and out["nested"]["api_key"] == REDACTED
    assert REDACTED in out["nested"]["ok"] and out["policy"] == data["policy"]
    assert REDACTED in redact_text("key sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ123")


def test_canonical_hash_is_order_independent() -> None:
    assert canonical_hash({"a": 1, "b": [1, 2]}) == canonical_hash({"b": [1, 2], "a": 1})
    assert canonical_hash({"a": 1}) != canonical_hash({"a": 2})


def test_plan_state_machine() -> None:
    check_transition(PLAN_TRANSITIONS, "DRAFT", "PENDING_APPROVAL", "plan")
    with pytest.raises(InvalidTransition):
        check_transition(PLAN_TRANSITIONS, "REJECTED", "APPROVED", "plan")
    with pytest.raises(InvalidTransition):
        check_transition(PLAN_TRANSITIONS, "DRAFT", "APPROVED", "plan")


def test_lifecycle_stage_derivation() -> None:
    assert lifecycle_stage("PENDING_APPROVAL", "NOT_STARTED", None, "not_started", "open") == "PENDING_APPROVAL"
    assert lifecycle_stage("APPROVED", "NOT_STARTED", "SYNC_FAILED", "not_started", "open") == "SYNC_FAILED"
    assert lifecycle_stage("APPROVED", "IMPLEMENTED", "SYNCED", "pending_rescan", "in_remediation") == "PENDING_VERIFICATION"
    assert lifecycle_stage("APPROVED", "IMPLEMENTED", "SYNCED", "verified_remediated", "closed") == "CLOSED"
