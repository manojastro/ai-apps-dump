"""Fault injection ground truth: every fault yields its expected regressions."""
from __future__ import annotations

import pytest

from simulator.faults import FAULT_CATALOG


def _inject(client, name: str) -> dict:
    r = client.post(f"/api/v1/network/faults/{name}", json={})
    assert r.status_code == 200, f"fault {name} failed: {r.text[:200]}"
    data = r.json()
    v = client.get(f"/api/v1/changes/{data['change_id']}/validation").json()
    return {**v, "change_status": data["status"], "risk_band": data["risk_band"]}


@pytest.mark.parametrize("name", sorted(FAULT_CATALOG.names()))
def test_fault_produces_expected_regressions(module_client, name: str) -> None:
    spec = FAULT_CATALOG.get(name)
    report = _inject(module_client, name)
    detected = {g["kind"] for g in report["regressions"]}
    expected = {e.kind for e in spec.expected_regressions}
    missing = expected - detected
    assert not missing, (
        f"{name}: expected regression kinds missing. "
        f"expected={sorted(expected)} detected={sorted(detected)}")
    if spec.benign:
        assert not detected, f"{name}: benign change must yield zero regressions"
    else:
        assert report["verdict"] == "FAIL"
        assert report["risk"]["band"] in ("MEDIUM", "HIGH", "CRITICAL")


def test_acl_blackhole_blocks_app_to_db_5432(module_client) -> None:
    report = _inject(module_client, "acl_blackhole")
    blocked = report["matrix_diff_summary"].get("newly_blocked_detail", [])
    hits = [m for m in blocked
            if m["flow"]["src"] == "app-01" and m["flow"]["dst"] == "db-01"
            and m["flow"]["port"] == 5432]
    assert hits, "expected app->db tcp/5432 to be BLOCKED"


def test_bgp_leak_hijacks_internal_prefix(module_client) -> None:
    report = _inject(module_client, "bgp_route_leak")
    kinds = {g["kind"] for g in report["regressions"]}
    assert "ROUTE_HIJACK" in kinds
    hijacks = [g for g in report["regressions"]
               if g["kind"] == "ROUTE_HIJACK"
               and "10.50.20.0/24" in g["message"]]
    assert hijacks


def test_dns_failure_marks_service_unreachable(module_client) -> None:
    report = _inject(module_client, "dns_service_failure")
    kinds = {g["kind"] for g in report["regressions"]}
    assert "SERVICE_UNREACHABLE" in kinds


def test_overlapping_subnet_detected_by_topology_agent(module_client) -> None:
    report = _inject(module_client, "overlapping_subnet")
    findings = report["topology_findings"]
    overlaps = [f for f in findings
                if f.get("type") in ("duplicate_ip", "subnet_zone_overlap")]
    assert overlaps


def test_mtu_mismatch_flags_violation_kind(module_client) -> None:
    report = _inject(module_client, "mtu_mismatch")
    mtu_regressions = [g for g in report["regressions"]
                       if g["kind"] == "MTU_VIOLATION"]
    assert mtu_regressions


def test_asymmetric_routing_only_warning_not_outage(module_client) -> None:
    report = _inject(module_client, "asymmetric_routing")
    kinds = {g["kind"] for g in report["regressions"]}
    assert "ASYMMETRIC_ROUTE" in kinds
    outage_kinds = {"ACL_BLACKHOLE", "FW_BLOCKED_FLOW", "SERVICE_UNREACHABLE",
                    "HOST_ISOLATED", "NO_ROUTE"}
    assert not (kinds & outage_kinds), "asymmetry alone must not cause outage"
