"""Tool framework tests: schema validation, audit rows, permissions, behavior."""
from __future__ import annotations

import pytest

from app.db import session_scope
from app.models.entities import ToolCallRec
from app.tools.base import REGISTRY, ToolApprovalRequired, ToolError
from app.tools.network_tools import (
    ApplyChangeTool,
    BuildCandidateTopologyInput,
    BuildCandidateTopologyTool,
    ParseConfigDiffInput,
    ParseConfigDiffTool,
    PolicyCheckInput,
    PolicyCheckTool,
    ReachabilityMatrixInput,
    ReachabilityMatrixTool,
    RollbackTool,
    RoutingTableDiffInput,
    RoutingTableDiffTool,
)
from app.services.intents import IntentDef
from simulator.configs import DiffParser, apply_ops
from simulator.lab import build_lab_twin, SEED_INTENTS
from simulator.models import TwinPayload


DIFF = ("device fw-01\n"
        "+ip access-list APP-DB-GUARD\n"
        "+ deny tcp 10.30.0.0/24 10.30.1.0/24 eq 5432\n"
        "+ permit ip any any\n"
        "interface Vlan210\n"
        "+ ip access-group APP-DB-GUARD in\n")


def test_registry_contains_all_seven_tools() -> None:
    names = set(REGISTRY.names())
    expected = {
        "parse_config_diff_tool",
        "build_candidate_topology_tool",
        "reachability_matrix_tool",
        "routing_table_diff_tool",
        "policy_check_tool",
        "apply_change_tool",
        "rollback_tool",
    }
    assert expected == names


def test_registry_unknown_tool_raises() -> None:
    with pytest.raises(ToolError):
        REGISTRY.get("does_not_exist")


def test_parse_config_diff_tool(client) -> None:
    tool = REGISTRY.get("parse_config_diff_tool")
    output = tool.run({"config_diff": DIFF})
    assert output["op_count"] >= 3
    kinds = {op["kind"] for op in output["ops"]}
    assert {"acl_rule", "interface"} <= kinds
    assert output["risky_ops"] >= 1
    with session_scope() as session:
        row = session.query(ToolCallRec).filter_by(
            tool="parse_config_diff_tool").order_by(ToolCallRec.id.desc()).first()
        assert row is not None and row.ok is True


def test_parse_tool_rejects_invalid_input_schema(client) -> None:
    tool = REGISTRY.get("parse_config_diff_tool")
    with pytest.raises(Exception):
        tool.run({"wrong_field": True})


def test_build_candidate_topology_tool(client) -> None:
    twin = build_lab_twin()
    ops = DiffParser().parse(DIFF, twin)
    tool = REGISTRY.get("build_candidate_topology_tool")
    out = tool.run({"base_payload": twin.to_dict(), "ops": ops})
    assert out["ok"] is True
    acls = {a["name"] for a in out["candidate_payload"]["acls"]}
    assert "APP-DB-GUARD" in acls


def test_reachability_matrix_tool_counts(client) -> None:
    payload = build_lab_twin().to_dict()
    tool = REGISTRY.get("reachability_matrix_tool")
    out = tool.run({"payload": payload})
    assert out["summary"]["total"] == 168
    assert out["summary"]["blocked"] > 0
    statuses = {row["status"] for row in out["rows"]}
    assert "allowed" in statuses


def test_routing_table_diff_tool_detects_changes(client) -> None:
    twin = build_lab_twin()
    ops = DiffParser().parse("device core-01\nrouter bgp 65000\n"
                             "- neighbor 10.200.3.5 advertised-prefixes "
                             "10.80.0.0/24\n", twin)
    candidate, _ = apply_ops(twin, ops)
    tool = REGISTRY.get("routing_table_diff_tool")
    out = tool.run({"base_payload": twin.to_dict(),
                    "candidate_payload": candidate.to_dict()})
    removals = [c for c in out["changes"] if c["change"] == "removed"]
    assert len(removals) == 1
    assert removals[0]["protocol"] == "bgp"
    assert removals[0]["prefix"] == "10.80.0.0/24"


def test_policy_check_tool_passes_baseline(client) -> None:
    payload = build_lab_twin().to_dict()
    intents = [IntentDef(name=s["name"], itype=s["itype"], params=s["params"])
               for s in SEED_INTENTS]
    tool = REGISTRY.get("policy_check_tool")
    out = tool.run({"payload": payload,
                    "intents": [i.model_dump() for i in intents]})
    assert out["passed"] is True
    assert out["compliance_pct"] == 100.0


def test_apply_change_tool_requires_approval_gate(client) -> None:
    from app.repositories.repo import ChangeRepository, SnapshotRepository
    from app.services.validation import seed_network, submit_change

    with session_scope() as session:
        seed_network(session)
        change = submit_change(session, title="t", config_diff=DIFF)
        change_id = change.id
    tool = ApplyChangeTool()
    with pytest.raises((ToolApprovalRequired, ToolError)):
        tool.run({"change_id": change_id}, approved=False)
    with pytest.raises(ToolError):
        tool.run({"change_id": change_id}, approved=True)


def test_rollback_tool_errors_without_parent_snapshot(client) -> None:
    from app.services.validation import seed_network

    with session_scope() as session:
        seed_network(session)
    tool = RollbackTool()
    with pytest.raises(Exception):
        tool.run({"change_id": 9999}, approved=True)


def test_mutating_tools_declare_permission() -> None:
    assert REGISTRY.get("apply_change_tool").permission == "mutating"
    assert REGISTRY.get("rollback_tool").permission == "mutating"
    assert REGISTRY.get("parse_config_diff_tool").permission == "safe"


def test_direct_model_construction_roundtrip(seeded_payload) -> None:
    model = TwinPayload.model_validate(seeded_payload)
    assert model.devices[0].name == "core-01"
