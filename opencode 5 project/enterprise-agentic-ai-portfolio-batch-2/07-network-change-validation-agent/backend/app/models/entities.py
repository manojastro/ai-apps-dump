"""SQLAlchemy persistence models for the network twin validation service."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SnapshotModel(Base):
    __tablename__ = "network_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(32))
    change_id: Mapped[int | None] = mapped_column(ForeignKey("changes.id"), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeviceRec(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(32))
    zone: Mapped[str] = mapped_column(String(64))
    vendor: Mapped[str] = mapped_column(String(64), default="generic")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class InterfaceRec(Base):
    __tablename__ = "interfaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    device: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(64))
    cidr: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mtu: Mapped[int] = mapped_column(Integer, default=1500)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    vlan: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acl_in: Mapped[str | None] = mapped_column(String(128), nullable=True)
    acl_out: Mapped[str | None] = mapped_column(String(128), nullable=True)


class VlanRec(Base):
    __tablename__ = "vlans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    vlan_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(64))


class SubnetRec(Base):
    __tablename__ = "subnets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    cidr: Mapped[str] = mapped_column(String(64), index=True)
    vlan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    zone: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(128), default="")


class AclRuleRec(Base):
    __tablename__ = "acl_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    acl_name: Mapped[str] = mapped_column(String(128), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(16))
    proto: Mapped[str] = mapped_column(String(16))
    src: Mapped[str] = mapped_column(String(64))
    dst: Mapped[str] = mapped_column(String(64))
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RouteRec(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    device: Mapped[str] = mapped_column(String(128), index=True)
    prefix: Mapped[str] = mapped_column(String(64), index=True)
    next_hop: Mapped[str | None] = mapped_column(String(64), nullable=True)
    protocol: Mapped[str] = mapped_column(String(16))
    distance: Mapped[int] = mapped_column(Integer, default=1)


class BgpNeighborRec(Base):
    __tablename__ = "bgp_neighbors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    device: Mapped[str] = mapped_column(String(128), index=True)
    peer_ip: Mapped[str] = mapped_column(String(64))
    remote_as: Mapped[int] = mapped_column(Integer)
    advertised_prefixes: Mapped[list] = mapped_column(JSON, default=list)


class FirewallPolicyRec(Base):
    __tablename__ = "firewall_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("network_snapshots.id"), index=True)
    device: Mapped[str] = mapped_column(String(128))
    seq: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(16))
    src: Mapped[str] = mapped_column(String(64))
    dst: Mapped[str] = mapped_column(String(64))
    proto: Mapped[str] = mapped_column(String(16))
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str] = mapped_column(String(128), default="")


class ChangeModel(Base):
    __tablename__ = "changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    requested_by: Mapped[str] = mapped_column(String(128), default="netops")
    status: Mapped[str] = mapped_column(String(32), default="PROPOSED", index=True)
    config_diff: Mapped[str] = mapped_column(Text)
    diff_ops: Mapped[list | None] = mapped_column(JSON, nullable=True)
    proposed_fix_diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_ops_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    fix_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_band: Mapped[str] = mapped_column(String(16), default="LOW")
    fault_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_snapshot_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_snapshot_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_snapshot_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DiffRecord(Base):
    __tablename__ = "diffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("changes.id"), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    ops_json: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("changes.id"), index=True)
    verdict: Mapped[str] = mapped_column(String(16))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_band: Mapped[str] = mapped_column(String(16), default="LOW")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    narration: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IntentTest(Base):
    __tablename__ = "intent_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    itype: Mapped[str] = mapped_column(String(32))
    params: Mapped[dict] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    severity: Mapped[str] = mapped_column(String(16), default="HIGH")


class IntentResult(Base):
    __tablename__ = "intent_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"), index=True)
    intent_name: Mapped[str] = mapped_column(String(128))
    passed: Mapped[bool] = mapped_column(Boolean)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class Regression(Base):
    __tablename__ = "regressions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"), index=True)
    kind: Mapped[str] = mapped_column(String(48), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="HIGH")
    source: Mapped[str] = mapped_column(String(128), default="")
    destination: Mapped[str] = mapped_column(String(128), default="")
    message: Mapped[str] = mapped_column(Text)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"), index=True)
    agent: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="completed")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceRec(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    kind: Mapped[str] = mapped_column(String(48))
    source_agent: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSON, default=dict)


class HypothesisRec(Base):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="proposed")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    refuted_by: Mapped[str | None] = mapped_column(Text, nullable=True)


class RcaRecord(Base):
    __tablename__ = "rca_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("validation_runs.id"), index=True)
    incident_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApprovalRec(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("changes.id"), index=True)
    actor: Mapped[str] = mapped_column(String(128))
    decision: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str] = mapped_column(Text, default="")
    from_status: Mapped[str] = mapped_column(String(32), default="")
    to_status: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity: Mapped[str] = mapped_column(String(48), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128), default="system")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ToolCallRec(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tool: Mapped[str] = mapped_column(String(96), index=True)
    permission: Mapped[str] = mapped_column(String(16), default="safe")
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(String(48), default="validation", index=True)
    metrics: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
