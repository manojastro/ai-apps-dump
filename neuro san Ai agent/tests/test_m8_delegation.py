"""M8 tests: delegation follows evidence, never a fixed symptom→script map."""

from __future__ import annotations

from orchestration.investigate import MAX_TOOL_CALLS, _next_tools, investigate_sync

SLOW = "My laptop is very slow and Teams keeps freezing."


def test_slow_laptop_full_evidence_path() -> None:
    inv = investigate_sync(SLOW, "DEVICE_001", "USER_001")
    assert inv.agents_involved == ["endpoint_agent", "software_agent"]
    assert inv.tools_consulted == ["query_device_health", "query_software_inventory",
                                   "query_processes", "query_recent_changes"]
    assert "knowledge_agent" not in inv.agents_involved
    assert inv.verdict == "PROCEED" and inv.confidence == 100.0
    assert len(inv.hypotheses) == 1
    top = inv.hypotheses[0]
    assert top["title"] == "Teams excessive memory after update"
    assert top["status"] == "SUPPORTED"


def test_same_text_healthy_device_abstains() -> None:
    """Same words, different telemetry → different path + safe escalation."""
    inv = investigate_sync("My laptop is very slow.", "DEVICE_100", "USER_100")
    assert inv.tools_consulted == ["query_device_health", "query_processes"]
    assert inv.follow_up_used  # RCA asked for more, then honestly gave up
    assert inv.verdict == "ESCALATE" and inv.confidence == 0.0
    assert inv.hypotheses == []


def test_vpn_identity_path() -> None:
    inv = investigate_sync("I changed my password and now my VPN won't connect.",
                           "DEVICE_002", "USER_002")
    assert set(inv.agents_involved) == {"network_agent", "identity_agent"}
    assert "query_vpn_state" in inv.tools_consulted
    assert "query_signin_history" in inv.tools_consulted
    assert "query_zscaler" in inv.tools_consulted
    assert not any(t in inv.tools_consulted for t in ("query_processes", "query_disk_health"))
    assert inv.verdict == "PROCEED"
    assert inv.hypotheses[0]["title"] == "Stale secure-access token"


def test_knowledge_path_calls_nobody_else() -> None:
    inv = investigate_sync("How do I claim internet reimbursement?")
    assert inv.agents_involved == ["knowledge_agent"]
    assert inv.tools_consulted == ["search_enterprise_knowledge"]
    assert inv.verdict == "KNOWLEDGE"


def test_budgets_and_determinism() -> None:
    first = investigate_sync(SLOW, "DEVICE_001", "USER_001")
    second = investigate_sync(SLOW, "DEVICE_001", "USER_001")
    assert first.tools_consulted == second.tools_consulted
    assert first.verdict == second.verdict
    for inv in (first, second):
        assert len(inv.tools_consulted) <= MAX_TOOL_CALLS
        assert len(inv.tools_consulted) == len(set(inv.tools_consulted))  # no repeats


def test_predicates_read_numbers_not_text() -> None:
    hot = _next_tools({"query_device_health": {"ram_pct": 91.0, "cpu_pct": 40.0, "disk_pct": 42.0}})
    assert "query_processes" in {t for t, _ in hot}
    calm = _next_tools({"query_device_health": {"ram_pct": 50.0, "cpu_pct": 30.0, "disk_pct": 40.0}})
    assert calm == []
    vpn_down = _next_tools({"query_vpn_state": {"connected": False}})
    assert {t for t, _ in vpn_down} == {"query_signin_history", "query_zscaler"}
