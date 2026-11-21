"""M7 tests: 10-agent network validity + coded-tool behavior.

HOCON is parsed with repo-root basedir (neuro-san resolves top-level
includes root-relative under `ns run`; raw pyhocon defaults file-relative).
"""

from __future__ import annotations

import asyncio
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOCON_PATH = ROOT / "registries" / "digital_workplace_autopilot" / "commander.hocon"

EXPECTED_AGENTS = ["commander", "endpoint_agent", "software_agent",
                   "network_agent", "identity_agent", "rca_agent",
                   "knowledge_agent", "security_agent", "learning_agent",
                   "servicenow_agent"]


def _parse():
    from pyhocon import ConfigFactory
    return ConfigFactory.parse_string(HOCON_PATH.read_text(encoding="utf-8"),
                                      str(ROOT))


def _run(tool, args: dict):
    return asyncio.run(tool.async_invoke(args, {}))


def test_hocon_parses_and_counts() -> None:
    cfg = _parse()
    tools = cfg["tools"]
    llm_agents = [t for t in tools if "class" not in t and "toolbox" not in t]
    coded = [t for t in tools if "class" in t]
    assert len(tools) == 64
    assert [t["name"] for t in llm_agents] == EXPECTED_AGENTS  # exactly 10, in order
    assert len(coded) == 54
    assert tools[0]["name"] == "commander"  # front man first


def test_frontman_rules() -> None:
    cfg = _parse()
    commander = cfg["tools"][0]
    assert "class" not in commander and "toolbox" not in commander
    assert "parameters" not in commander.get("function", {})
    for agent in cfg["tools"][1:10]:
        assert "inquiry" in agent["function"]["parameters"]["properties"]


def test_all_refs_resolve_no_dupes() -> None:
    cfg = _parse()
    names = [t["name"] for t in cfg["tools"]]
    assert not [n for n, c in Counter(names).items() if c > 1]
    by_name = {t["name"]: t for t in cfg["tools"]}
    for tool in cfg["tools"]:
        for ref in tool.get("tools", []):
            assert ref in by_name, f"{tool['name']} -> missing {ref}"


def test_llm_config_gemini_and_no_secrets() -> None:
    cfg = _parse()
    assert cfg["llm_config"]["model_name"] == "gemini-3-flash"
    assert cfg["llm_config"]["temperature"] == 1.0
    text = HOCON_PATH.read_text(encoding="utf-8")
    # Secret SHAPES only — user prose like "my password" in sample queries is fine.
    for banned in ("AIza", "GOOGLE_API_KEY", "sk-ant-", "sk-proj-", "AKIA", "xoxb-"):
        assert banned not in text


def test_manifest_serves_network() -> None:
    text = (ROOT / "registries" / "digital_workplace_autopilot" / "manifest.hocon").read_text()
    assert "digital_workplace_autopilot/commander.hocon" in text


def test_every_coded_class_resolves() -> None:
    import importlib
    import tests.conftest  # noqa: F401 (neuro_san stub)
    from neuro_san.interfaces.coded_tool import CodedTool

    cfg = _parse()
    for tool in cfg["tools"]:
        if "class" not in tool:
            continue
        module_name, class_name = tool["class"].rsplit(".", 1)
        module = importlib.import_module(f"coded_tools.{module_name}")
        cls = getattr(module, class_name)
        assert issubclass(cls, CodedTool), tool["name"]
        assert hasattr(cls, "async_invoke"), tool["name"]


def test_commander_routing_is_ranked_not_fixed() -> None:
    from coded_tools.digital_workplace.commander_tools import RouteRequest

    slow = _run(RouteRequest(), {"request_text": "My laptop is very slow and Teams keeps freezing"})
    agents = [r["agent"] for r in slow["ranked"]]
    assert agents[0] == "endpoint_agent"
    assert "rca_agent" in agents
    assert "knowledge_agent" not in agents  # not called for every request

    kb = _run(RouteRequest(), {"request_text": "How do I claim internet reimbursement?"})
    assert kb["ranked"][0]["agent"] == "knowledge_agent"

    vpn = _run(RouteRequest(), {"request_text": "I changed my password and now my VPN won't connect"})
    top2 = {r["agent"] for r in vpn["ranked"][:2]}
    assert {"identity_agent", "network_agent"} <= top2


def test_observe_demo_evidence() -> None:
    from coded_tools.digital_workplace.observe import (QueryDeviceHealth,
                                                       QueryProcesses,
                                                       QueryVpnState)

    health = _run(QueryDeviceHealth(), {"device_id": "DEVICE_001"})
    assert (health["cpu_pct"], health["ram_pct"], health["disk_pct"]) == (94.0, 91.0, 42.0)
    procs = _run(QueryProcesses(), {"device_id": "DEVICE_001"})
    teams = next(p for p in procs["processes"] if p["name"] == "Teams")
    assert teams["mem_mb"] == 4812.8
    vpn = _run(QueryVpnState(), {"device_id": "DEVICE_002"})
    assert not vpn["connected"] and "stale" in vpn["last_error"]


def test_rca_bands_and_graph() -> None:
    from coded_tools.digital_workplace.rca import (BuildCausalGraph,
                                                   CheckConfidenceThreshold,
                                                   GenerateHypotheses)

    assert _run(CheckConfidenceThreshold(), {"confidence": 95})["may_auto_remediate"]
    assert not _run(CheckConfidenceThreshold(), {"confidence": 75})["may_auto_remediate"]
    assert _run(CheckConfidenceThreshold(), {"confidence": 40})["action"].startswith("escalate")
    hyps = _run(GenerateHypotheses(), {"evidence": []})
    assert hyps["verdict"] == "INSUFFICIENT EVIDENCE"
    graph = _run(BuildCausalGraph(), {"evidence": [
        {"evidence_id": "E1", "sanitized_summary": "Teams update"},
        {"evidence_id": "E2", "sanitized_summary": "RAM pressure"}],
        "root_cause": "Teams memory regression"})
    assert "ROOT_CAUSE" in graph["mermaid"] and "E1 --> E2" in graph["mermaid"]


def test_knowledge_deny_by_default_and_security_advisory() -> None:
    from coded_tools.digital_workplace import knowledge
    from coded_tools.digital_workplace.knowledge import SearchEnterpriseKnowledge
    from coded_tools.digital_workplace.security import CheckDeviceCompliance

    assert knowledge._acl_allows  # filter helper present (runs BEFORE llm context)
    # M11 seeded the base: authorized payroll-mentioning docs may surface,
    # but the restricted payroll SOP must never reach an employee.
    payroll = _run(SearchEnterpriseKnowledge(), {"query": "payroll"})
    assert all(h["doc_id"] != "payroll_admin_sop" for h in payroll["results"])
    compliance = _run(CheckDeviceCompliance(), {"device_id": "DEVICE_001"})
    assert compliance["compliant"] and "advisory only" in compliance["disclaimer"]


def test_learning_never_self_approves() -> None:
    from coded_tools.digital_workplace.ops import CreateWorkflowCandidate

    candidate = _run(CreateWorkflowCandidate(), {
        "workflow_id": "WF-TEST-1", "failure_signature": "teams_memory",
        "action_id": "SCR-018"})
    assert candidate["approval_state"] == "candidate"
