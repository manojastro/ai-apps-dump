"""Concrete network tools registered in the global registry."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.db import session_scope
from app.repositories.repo import AuditRepository, ChangeRepository, SnapshotRepository
from app.services.intents import IntentDef, evaluate_all
from app.services.twin import TwinRuntime, diff_matrices
from app.tools.base import REGISTRY, BaseTool, ToolError
from simulator.configs import DiffParser, apply_ops
from simulator.models import TwinPayload


class ParseConfigDiffInput(BaseModel):
    config_diff: str = Field(min_length=1)


class ParseConfigDiffOutput(BaseModel):
    ops: list[dict[str, Any]]
    op_count: int
    risky_ops: int


class BuildCandidateTopologyInput(BaseModel):
    base_payload: dict[str, Any]
    ops: list[dict[str, Any]] = Field(default_factory=list)


class BuildCandidateTopologyOutput(BaseModel):
    candidate_payload: dict[str, Any]
    journal: list[dict[str, Any]]
    ok: bool


class ReachabilityMatrixInput(BaseModel):
    payload: dict[str, Any]


class ReachabilityMatrixOutput(BaseModel):
    rows: list[dict[str, Any]]
    summary: dict[str, Any]


class RoutingTableDiffInput(BaseModel):
    base_payload: dict[str, Any]
    candidate_payload: dict[str, Any]
    devices: list[str] = Field(default_factory=list)


class RoutingTableDiffOutput(BaseModel):
    changes: list[dict[str, Any]]
    added: int
    removed: int


class PolicyCheckInput(BaseModel):
    payload: dict[str, Any]
    intents: list[dict[str, Any]]


class PolicyCheckOutput(BaseModel):
    results: list[dict[str, Any]]
    passed: bool
    compliance_pct: float


class ApplyChangeInput(BaseModel):
    change_id: int


class ApplyChangeOutput(BaseModel):
    applied: bool
    new_snapshot_id: int | None = None
    status: str


class RollbackChangeInput(BaseModel):
    change_id: int


class RollbackChangeOutput(BaseModel):
    rolled_back: bool
    restored_snapshot_id: int | None = None
    status: str


def _risky(op: dict[str, Any]) -> bool:
    if op.get("kind") == "noop":
        return False
    if op.get("remove"):
        return True
    if op.get("kind") == "acl_rule" and op.get("action") == "deny":
        return True
    if op.get("kind") == "interface" and op.get("attr") in ("enabled", "cidr", "mtu"):
        return True
    if op.get("kind") == "firewall_policy":
        return True
    return False


class ParseConfigDiffTool(BaseTool):
    name = "parse_config_diff_tool"
    description = "Parse a unified device-config diff into normalized structured operations"
    permission = "safe"
    timeout_s = 10.0

    def input_model(self) -> type[BaseModel]:
        return ParseConfigDiffInput

    def output_model(self) -> type[BaseModel]:
        return ParseConfigDiffOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, ParseConfigDiffInput)
        with session_scope() as session:
            snap = SnapshotRepository(session).current()
            if snap is None:
                raise ToolError("no current network snapshot; seed first")
            payload = TwinPayload.model_validate(snap.payload)
        ops = DiffParser().parse(validated_input.config_diff, payload)
        return ParseConfigDiffOutput(
            ops=ops,
            op_count=len(ops),
            risky_ops=sum(1 for op in ops if _risky(op)),
        )


class BuildCandidateTopologyTool(BaseTool):
    name = "build_candidate_topology_tool"
    description = "Build the CANDIDATE twin by applying parsed operations to CURRENT twin"
    permission = "safe"
    timeout_s = 15.0

    def input_model(self) -> type[BaseModel]:
        return BuildCandidateTopologyInput

    def output_model(self) -> type[BaseModel]:
        return BuildCandidateTopologyOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, BuildCandidateTopologyInput)
        base = TwinPayload.model_validate(validated_input.base_payload)
        candidate, journal = apply_ops(base, validated_input.ops)
        return BuildCandidateTopologyOutput(
            candidate_payload=candidate.to_dict(), journal=journal,
            ok=True,
        )


class ReachabilityMatrixTool(BaseTool):
    name = "reachability_matrix_tool"
    description = "Compute endpoint-pair x port reachability matrix for one twin snapshot"
    permission = "safe"
    timeout_s = 120.0

    def input_model(self) -> type[BaseModel]:
        return ReachabilityMatrixInput

    def output_model(self) -> type[BaseModel]:
        return ReachabilityMatrixOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, ReachabilityMatrixInput)
        runtime = TwinRuntime(TwinPayload.model_validate(validated_input.payload))
        rows = runtime.reachability_matrix()
        blocked = sum(1 for r in rows if r["status"] != "allowed")
        asym = sum(1 for r in rows if r["asymmetric"])
        summary = {"total": len(rows), "blocked": blocked,
                   "allowed": len(rows) - blocked, "asymmetric": asym}
        return ReachabilityMatrixOutput(rows=rows, summary=summary)


class RoutingTableDiffTool(BaseTool):
    name = "routing_table_diff_tool"
    description = "Diff installed routing tables (static/ospf/bgp) between two twins"
    permission = "safe"
    timeout_s = 30.0

    def input_model(self) -> type[BaseModel]:
        return RoutingTableDiffInput

    def output_model(self) -> type[BaseModel]:
        return RoutingTableDiffOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, RoutingTableDiffInput)
        from simulator.models import norm_cidr

        base_rt = TwinRuntime(TwinPayload.model_validate(validated_input.base_payload))
        cand_rt = TwinRuntime(TwinPayload.model_validate(validated_input.candidate_payload))
        devices = validated_input.devices or sorted(base_rt.devices)
        changes: list[dict[str, Any]] = []
        for dev in devices:
            before = {
                (norm_cidr(r.prefix), r.next_hop, r.protocol): r
                for r in base_rt.routing_table(dev)
            }
            after = {
                (norm_cidr(r.prefix), r.next_hop, r.protocol): r
                for r in cand_rt.routing_table(dev)
            }
            for key in sorted(set(before) - set(after), key=str):
                r = before[key]
                changes.append({"device": dev, "change": "removed", "prefix": key[0],
                                "next_hop": key[1], "protocol": key[2],
                                "distance": r.distance})
            for key in sorted(set(after) - set(before), key=str):
                r = after[key]
                changes.append({"device": dev, "change": "added", "prefix": key[0],
                                "next_hop": key[1], "protocol": key[2],
                                "distance": r.distance})
        removed = sum(1 for c in changes if c["change"] == "removed")
        added = len(changes) - removed
        return RoutingTableDiffOutput(changes=changes, added=added, removed=removed)


class PolicyCheckTool(BaseTool):
    name = "policy_check_tool"
    description = "Evaluate declarative intent policies against one twin snapshot"
    permission = "safe"
    timeout_s = 60.0

    def input_model(self) -> type[BaseModel]:
        return PolicyCheckInput

    def output_model(self) -> type[BaseModel]:
        return PolicyCheckOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, PolicyCheckInput)
        intents = [IntentDef(**i) for i in validated_input.intents]
        runtime = TwinRuntime(TwinPayload.model_validate(validated_input.payload))
        outcomes = evaluate_all(intents, runtime)
        total = len(outcomes)
        passed = sum(1 for o in outcomes if o.passed)
        pct = 100.0 if total == 0 else round(passed * 100.0 / total, 1)
        return PolicyCheckOutput(
            results=[o.model_dump() for o in outcomes],
            passed=all(o.passed for o in outcomes),
            compliance_pct=pct,
        )


class ApplyChangeTool(BaseTool):
    name = "apply_change_tool"
    description = "Promote the approved CANDIDATE twin to CURRENT (mutating)"
    permission = "mutating"
    timeout_s = 60.0

    def input_model(self) -> type[BaseModel]:
        return ApplyChangeInput

    def output_model(self) -> type[BaseModel]:
        return ApplyChangeOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, ApplyChangeInput)
        with session_scope() as session:
            changes = ChangeRepository(session)
            snaps = SnapshotRepository(session)
            audit = AuditRepository(session)
            change = changes.get(validated_input.change_id)
            if change is None:
                raise ToolError(f"change {validated_input.change_id} not found")
            if change.status not in ("APPROVED", "EXECUTING"):
                raise ToolError(
                    f"change {change.id} has not passed the approval gate "
                    f"(status={change.status}); apply requires approval"
                )
            current = snaps.current()
            if current is not None:
                archived = snaps.create(version=f"pre-apply-{change.id}",
                                        payload=current.payload, is_current=False)
                change.parent_snapshot_id = archived.id
            cand = None
            if change.candidate_snapshot_id:
                cand = snaps.get(change.candidate_snapshot_id)
            payload = cand.payload if cand else (current.payload if current else {})
            new_snap = snaps.create(version="CURRENT", payload=payload, is_current=True,
                                    change_id=change.id)
            change.current_snapshot_id = new_snap.id
            audit.event("change", change.id, "applied", actor="apply_change_tool",
                        detail={"snapshot_id": new_snap.id})
            return ApplyChangeOutput(applied=True, new_snapshot_id=new_snap.id,
                                     status="EXECUTING")


class RollbackTool(BaseTool):
    name = "rollback_tool"
    description = "Restore the pre-change CURRENT snapshot (mutating)"
    permission = "mutating"
    timeout_s = 60.0

    def input_model(self) -> type[BaseModel]:
        return RollbackChangeInput

    def output_model(self) -> type[BaseModel]:
        return RollbackChangeOutput

    def execute(self, validated_input: BaseModel) -> BaseModel:
        assert isinstance(validated_input, RollbackChangeInput)
        with session_scope() as session:
            changes = ChangeRepository(session)
            snaps = SnapshotRepository(session)
            audit = AuditRepository(session)
            change = changes.get(validated_input.change_id)
            if change is None:
                raise ToolError(f"change {validated_input.change_id} not found")
            parent_id = change.parent_snapshot_id
            parent = snaps.get(parent_id) if parent_id else None
            if parent is None:
                raise ToolError(f"no rollback snapshot recorded for change {change.id}")
            snaps.create(version="CURRENT", payload=parent.payload, is_current=True,
                         change_id=change.id)
            audit.event("change", change.id, "rolled_back", actor="rollback_tool",
                        detail={"restored_from": parent.id})
            return RollbackChangeOutput(rolled_back=True, restored_snapshot_id=parent.id,
                                        status="ROLLED_BACK")


REGISTRY.register(ParseConfigDiffTool())
REGISTRY.register(BuildCandidateTopologyTool())
REGISTRY.register(ReachabilityMatrixTool())
REGISTRY.register(RoutingTableDiffTool())
REGISTRY.register(PolicyCheckTool())
REGISTRY.register(ApplyChangeTool())
REGISTRY.register(RollbackTool())


def diff_riskiness(ops: list[dict[str, Any]]) -> int:
    return sum(1 for op in ops if _risky(op))
