"""Concrete, narrowly scoped tools. Read-only unless explicitly marked ``mutating``."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select

from app.approvals import service as approvals
from app.integrations.defender.mock import MockDefenderAdapter
from app.integrations.servicenow.base import CHANGE_STATES
from app.integrations.servicenow.factory import get_servicenow_client
from app.models.enterprise import Asset, AssetDependency, BusinessService
from app.models.remediation import ApprovalRequest, RemediationPlan, RiskAssessment
from app.models.simulation import SimDevice
from app.models.vulnerability import Finding, Vulnerability
from app.security.permissions import Permission
from app.services.normalization import normalize_cve_id
from app.services.threat_intel import ThreatIntelService
from app.tools.registry import ToolContext, ToolError, ToolSpec, registry

SEARCHABLE_TABLES = {"change_request", "change_task", "cmdb_ci_server", "cmdb_ci_service"}


class CveArgs(BaseModel):
    cve_id: str = Field(max_length=32)

    @field_validator("cve_id")
    @classmethod
    def _valid(cls, v: str) -> str:
        cve = normalize_cve_id(v)
        if not cve:
            raise ValueError("invalid CVE identifier")
        return cve


class AssetArgs(BaseModel):
    asset_id: str | None = Field(default=None, max_length=32)
    hostname: str | None = Field(default=None, max_length=255)


class DeviceArgs(BaseModel):
    device_id: str | None = Field(default=None, max_length=64)
    hostname: str | None = Field(default=None, max_length=255)


class ChangeArgs(BaseModel):
    number: str | None = Field(default=None, pattern=r"^[A-Z]{2,5}\d{5,10}$")
    sys_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")


class SearchArgs(BaseModel):
    table: Literal["change_request", "change_task", "cmdb_ci_server", "cmdb_ci_service"]
    field: Literal["number", "name", "state", "correlation_id", "short_description", "cmdb_ci"]
    value: str = Field(max_length=100, pattern=r"^[\w .:\-]+$")
    limit: int = Field(default=10, ge=1, le=25)


class PlanArgs(BaseModel):
    plan_id: str = Field(max_length=36)


class FindingArgs(BaseModel):
    finding_id: str = Field(max_length=36)


class FindingSearchArgs(BaseModel):
    risk_level: Literal["critical", "high", "medium", "low"] | None = None
    kev_only: bool = False
    business_service: str | None = Field(default=None, max_length=100)
    status: Literal["open", "in_remediation", "remediated", "closed"] | None = None
    verification_state: str | None = Field(default=None, max_length=32)
    cve_id: str | None = Field(default=None, max_length=32)
    limit: int = Field(default=10, ge=1, le=50)


class RequestApprovalArgs(BaseModel):
    plan_id: str = Field(max_length=36)
    comment: str | None = Field(default=None, max_length=1000)


def _asset_dict(a: Asset) -> dict[str, Any]:
    return {
        "asset_id": a.id,
        "hostname": a.hostname,
        "fqdn": a.fqdn,
        "environment": a.environment,
        "business_criticality": a.business_criticality,
        "internet_exposed": a.internet_exposed,
        "business_service": a.business_service.name if a.business_service else None,
        "owner": a.owner,
        "support_group": a.support_group,
        "operational_status": a.operational_status,
        "cmdb_sys_id": a.cmdb_sys_id,
        "os": a.operating_system,
    }


def _find_asset(ctx: ToolContext, args: AssetArgs) -> Asset:
    if args.asset_id:
        asset = ctx.db.get(Asset, args.asset_id)
    elif args.hostname:
        rows = list(ctx.db.scalars(select(Asset).where(func.lower(Asset.hostname) == args.hostname.lower())))
        if len(rows) > 1:
            raise ToolError(f"hostname '{args.hostname}' is ambiguous ({len(rows)} CMDB records)")
        asset = rows[0] if rows else None
    else:
        raise ToolError("asset_id or hostname required")
    if asset is None:
        raise ToolError("asset not found")
    return asset


# --------------------------------------------------------------------- ServiceNow (read)
def servicenow_get_asset(ctx: ToolContext, args: AssetArgs) -> dict[str, Any]:
    asset = _find_asset(ctx, args)
    out = _asset_dict(asset)
    if asset.cmdb_sys_id:
        remote = get_servicenow_client().get("cmdb_ci_server", asset.cmdb_sys_id)
        out["cmdb_record_found"] = remote is not None
        out["cmdb_last_sync"] = asset.last_sync_at.isoformat() if asset.last_sync_at else None
    return out


def servicenow_get_change(ctx: ToolContext, args: ChangeArgs) -> dict[str, Any]:
    client = get_servicenow_client()
    if args.sys_id:
        rec = client.get("change_request", args.sys_id)
    elif args.number:
        rows = client.query("change_request", f"number={args.number}", None, 1)
        rec = rows[0] if rows else None
    else:
        raise ToolError("number or sys_id required")
    if rec is None:
        return {"found": False}
    return {
        "found": True,
        "number": rec.get("number"),
        "sys_id": rec.get("sys_id"),
        "state": CHANGE_STATES.get(str(rec.get("state")), rec.get("state")),
        "short_description": rec.get("short_description"),
        "close_code": rec.get("close_code"),
        "correlation_id": rec.get("correlation_id"),
    }


def servicenow_search_records(ctx: ToolContext, args: SearchArgs) -> dict[str, Any]:
    if args.table not in SEARCHABLE_TABLES:
        raise ToolError("table not permitted")
    rows = get_servicenow_client().query(args.table, f"{args.field}LIKE{args.value}", None, args.limit)
    keep = ("sys_id", "number", "name", "state", "short_description", "correlation_id", "busines_criticality")
    return {"count": len(rows), "records": [{k: r.get(k) for k in keep if k in r} for r in rows]}


# --------------------------------------------------------------------- Defender (read)
def _device(ctx: ToolContext, args: DeviceArgs) -> SimDevice:
    if args.device_id:
        dev = ctx.db.get(SimDevice, args.device_id)
    elif args.hostname:
        dev = ctx.db.scalar(select(SimDevice).where(func.lower(SimDevice.computer_dns_name) == args.hostname.lower()))
    else:
        raise ToolError("device_id or hostname required")
    if dev is None:
        raise ToolError("device not found in Defender inventory")
    return dev


def defender_get_device(ctx: ToolContext, args: DeviceArgs) -> dict[str, Any]:
    d = _device(ctx, args)
    return {
        "device_id": d.id,
        "computer_dns_name": d.computer_dns_name,
        "os_platform": d.os_platform,
        "os_version": d.os_version,
        "last_ip_address": d.last_ip_address,
        "health_status": d.health_status,
        "exposure_level": d.exposure_level,
        "machine_tags": d.machine_tags,
        "last_seen": d.last_seen.isoformat(),
        "software_count": len(d.software),
    }


def defender_get_vulnerabilities(ctx: ToolContext, args: DeviceArgs) -> dict[str, Any]:
    d = _device(ctx, args)
    adapter = MockDefenderAdapter(ctx.db)
    findings = [f for f in adapter.list_findings() if f.device_id == d.id]
    return {
        "device_id": d.id,
        "count": len(findings),
        "vulnerabilities": [
            {"cve_id": f.cve_id, "software": f.software_name, "version": f.software_version, "severity": f.severity}
            for f in findings
        ],
    }


# --------------------------------------------------------------------- Threat intel (read)
def threat_get_cve(ctx: ToolContext, args: CveArgs) -> dict[str, Any]:
    r = ThreatIntelService(ctx.db).get_nvd(args.cve_id)
    d = r.data or {}
    return {
        "status": r.status,
        "origin": r.origin,
        "reference": r.reference,
        "fetched_at": r.fetched_at,
        "description": d.get("description"),
        "cvss": d.get("cvss"),
        "cwes": d.get("cwes"),
        "affected_ranges": d.get("cpe_ranges", [])[:40],
        "references": d.get("references"),
        "notes": r.notes,
    }


def threat_get_epss(ctx: ToolContext, args: CveArgs) -> dict[str, Any]:
    return ThreatIntelService(ctx.db).get_epss(args.cve_id).to_dict()


def threat_check_kev(ctx: ToolContext, args: CveArgs) -> dict[str, Any]:
    return ThreatIntelService(ctx.db).get_kev(args.cve_id).to_dict()


# --------------------------------------------------------------------- Inventory / remediation (read)
def asset_get_dependencies(ctx: ToolContext, args: AssetArgs) -> dict[str, Any]:
    asset = _find_asset(ctx, args)
    downstream = [
        ctx.db.get(Asset, d.target_asset_id)
        for d in ctx.db.scalars(select(AssetDependency).where(AssetDependency.source_asset_id == asset.id))
    ]
    upstream = [
        ctx.db.get(Asset, d.source_asset_id)
        for d in ctx.db.scalars(select(AssetDependency).where(AssetDependency.target_asset_id == asset.id))
    ]
    return {
        "asset_id": asset.id,
        "depends_on": [_asset_dict(a) for a in downstream if a],
        "used_by": [_asset_dict(a) for a in upstream if a],
    }


def remediation_get_plan(ctx: ToolContext, args: PlanArgs) -> dict[str, Any]:
    plan = ctx.db.get(RemediationPlan, args.plan_id)
    if plan is None:
        raise ToolError("plan not found")
    return {
        "plan_id": plan.id,
        "status": plan.status,
        "title": plan.title,
        "summary": plan.summary,
        "recommended_action": plan.recommended_action,
        "target_version": plan.target_version,
        "requires_expert_validation": plan.requires_expert_validation,
        "evidence_refs": plan.evidence_refs,
        "remediation_state": plan.remediation_state,
    }


def remediation_get_approval_status(ctx: ToolContext, args: PlanArgs) -> dict[str, Any]:
    reqs = list(
        ctx.db.scalars(
            select(ApprovalRequest).where(ApprovalRequest.plan_id == args.plan_id).order_by(ApprovalRequest.created_at)
        )
    )
    return {
        "plan_id": args.plan_id,
        "requests": [
            {
                "id": r.id,
                "state": r.state,
                "risk_level": r.risk_level,
                "created_at": r.created_at.isoformat(),
                "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                "decision_comment": r.decision_comment,
            }
            for r in reqs
        ],
    }


def finding_get_risk(ctx: ToolContext, args: FindingArgs) -> dict[str, Any]:
    finding = ctx.db.get(Finding, args.finding_id)
    if finding is None:
        raise ToolError("finding not found")
    ra = ctx.db.scalar(
        select(RiskAssessment).where(RiskAssessment.finding_id == finding.id).order_by(RiskAssessment.calculated_at.desc())
    )
    if ra is None:
        return {"finding_id": finding.id, "assessed": False}
    return {
        "finding_id": finding.id,
        "cve_id": finding.vulnerability.cve_id,
        "score": ra.score,
        "band": [ra.score_lower, ra.score_upper],
        "risk_level": ra.risk_level,
        "priority": ra.priority,
        "coverage": ra.coverage,
        "policy_version": ra.policy_version,
        "factors": ra.factors,
        "missing_factors": ra.missing_factors,
        "rationale": ra.rationale,
    }


def findings_search(ctx: ToolContext, args: FindingSearchArgs) -> dict[str, Any]:
    q = select(Finding).join(Vulnerability).outerjoin(Asset, Finding.asset_id == Asset.id).outerjoin(BusinessService)
    if args.risk_level:
        q = q.where(Finding.risk_level == args.risk_level)
    if args.kev_only:
        q = q.where(Vulnerability.kev.is_(True))
    if args.business_service:
        q = q.where(func.lower(BusinessService.name).like(f"%{args.business_service.lower()}%"))
    if args.status:
        q = q.where(Finding.status == args.status)
    if args.verification_state:
        q = q.where(Finding.verification_state == args.verification_state)
    if args.cve_id:
        q = q.where(or_(Vulnerability.cve_id == args.cve_id.upper()))
    rows = list(ctx.db.scalars(q.order_by(Finding.risk_score.desc().nulls_last()).limit(args.limit)))
    return {
        "count": len(rows),
        "findings": [
            {
                "finding_id": f.id,
                "cve_id": f.vulnerability.cve_id,
                "risk_score": f.risk_score,
                "risk_level": f.risk_level,
                "priority": f.priority,
                "kev": f.vulnerability.kev,
                "epss": f.vulnerability.epss_score,
                "asset": f.asset.hostname if f.asset else f.reported_asset_identifier,
                "business_service": f.asset.business_service.name if f.asset and f.asset.business_service else None,
                "status": f.status,
                "verification_state": f.verification_state,
                "remediated_at": f.remediated_at.isoformat() if f.remediated_at else None,
            }
            for f in rows
        ],
    }


# --------------------------------------------------------------------- mutating (approval-enforcing)
def remediation_request_approval(ctx: ToolContext, args: RequestApprovalArgs) -> dict[str, Any]:
    try:
        req = approvals.request_approval(ctx.db, args.plan_id, ctx.principal, args.comment)
    except approvals.ApprovalError as exc:
        raise ToolError(str(exc)) from exc
    return {"approval_request_id": req.id, "state": req.state, "note": "Approval requested; a human approver must decide."}


for spec in [
    ToolSpec(
        "servicenow_get_asset",
        "Read a CMDB configuration item for an asset (by asset_id or hostname).",
        AssetArgs,
        servicenow_get_asset,
    ),
    ToolSpec("servicenow_get_change", "Read a ServiceNow change request by number or sys_id.", ChangeArgs, servicenow_get_change),
    ToolSpec(
        "servicenow_search_records",
        "Search allowlisted ServiceNow tables by one field (LIKE).",
        SearchArgs,
        servicenow_search_records,
    ),
    ToolSpec("defender_get_device", "Read Defender device metadata.", DeviceArgs, defender_get_device),
    ToolSpec(
        "defender_get_vulnerabilities",
        "List Defender-reported vulnerabilities for a device.",
        DeviceArgs,
        defender_get_vulnerabilities,
    ),
    ToolSpec("threat_get_cve", "Authoritative CVE record (NVD) with provenance.", CveArgs, threat_get_cve),
    ToolSpec("threat_get_epss", "FIRST EPSS probability (an estimate, not proof of exploitation).", CveArgs, threat_get_epss),
    ToolSpec("threat_check_kev", "Check CISA KEV listing (confirmed exploitation).", CveArgs, threat_check_kev),
    ToolSpec(
        "asset_get_dependencies", "CMDB dependencies of an asset (depends_on / used_by).", AssetArgs, asset_get_dependencies
    ),
    ToolSpec("remediation_get_plan", "Read a remediation plan.", PlanArgs, remediation_get_plan),
    ToolSpec("remediation_get_approval_status", "Read approval requests for a plan.", PlanArgs, remediation_get_approval_status),
    ToolSpec("finding_get_risk", "Latest deterministic risk assessment with factor breakdown.", FindingArgs, finding_get_risk),
    ToolSpec("findings_search", "Search findings by risk, KEV, business service, status.", FindingSearchArgs, findings_search),
    ToolSpec(
        "remediation_request_approval",
        "Submit a plan for HUMAN approval (cannot approve; approval engine enforces policy).",
        RequestApprovalArgs,
        remediation_request_approval,
        permission=Permission.APPROVAL_REQUEST,
        mutating=True,
    ),
]:
    registry.register(spec)

READ_ONLY_TOOLS = {s.name for s in registry.specs() if not s.mutating}
