"""ServiceNow, simulation console, threat intelligence, integrations, settings and audit."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import serializers as ser
from app.api.deps import Page, domain_errors, page_params, paginate
from app.core.config import get_settings
from app.core.db import get_db
from app.integrations.defender.mock import MockDefenderAdapter
from app.integrations.defender.rest import DefenderApiAdapter
from app.integrations.scanners.base import UnsupportedScannerAdapter
from app.integrations.servicenow.base import CHANGE_STATES, ServiceNowError
from app.integrations.servicenow.factory import CMDB_FIELD_MAP, get_servicenow_client, remediation_table, write_allowlist
from app.llm.factory import provider_status
from app.models.identity import User
from app.models.servicenow import ServiceNowRecord, ServiceNowSyncAttempt, SnSimActivity, SnSimRecord
from app.models.simulation import SimDevice
from app.models.vulnerability import ScanImport, ThreatIntelCache, Vulnerability
from app.models.workflow import AuditEvent
from app.security.auth import Principal, require
from app.security.permissions import ROLE_PERMISSIONS, Permission
from app.services import simulation
from app.services.audit import record_audit
from app.services.policy_store import get_risk_policy, set_risk_policy
from app.services.risk_engine import RiskPolicy
from app.services.risk_service import assess_finding
from app.services.threat_intel import ThreatIntelService

router = APIRouter(tags=["integrations"])
Reader = Depends(require(Permission.READ))


# ------------------------------------------------------------------ ServiceNow
def _last_success(db: Session) -> str | None:
    ts = db.scalar(
        select(func.max(ServiceNowSyncAttempt.created_at)).where(
            ServiceNowSyncAttempt.outcome.in_(["success", "adopted_existing"])
        )
    )
    return ser.iso(ts)


@router.get("/api/servicenow/status")
def servicenow_status(_: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    client_label = get_servicenow_client().instance_label if (s.servicenow_mode == "mock" or s.servicenow_configured) else None
    counts = dict(db.execute(select(ServiceNowRecord.sync_state, func.count()).group_by(ServiceNowRecord.sync_state)).all())
    last_error = db.scalar(
        select(ServiceNowSyncAttempt)
        .where(ServiceNowSyncAttempt.outcome == "error")
        .order_by(ServiceNowSyncAttempt.created_at.desc())
    )
    return {
        "mode": s.servicenow_mode,
        "configured": s.servicenow_mode == "mock" or s.servicenow_configured,
        "instance": client_label,
        "writes_enabled": s.servicenow_mode == "mock" or s.enable_servicenow_writes,
        "tables": {
            "change": s.servicenow_change_table,
            "remediation": remediation_table(),
            "cmdb": s.servicenow_cmdb_table,
            "service": s.servicenow_service_table,
        },
        "write_allowlist": sorted(write_allowlist()),
        "cmdb_field_map": CMDB_FIELD_MAP,
        "auth_method": (
            "simulator"
            if s.servicenow_mode == "mock"
            else "oauth"
            if s.servicenow_client_id
            else "basic"
            if s.servicenow_username
            else "none"
        ),
        "record_counts": counts,
        "last_successful_sync": _last_success(db),
        "last_error": None
        if last_error is None
        else {"error": last_error.error, "at": ser.iso(last_error.created_at), "operation": last_error.operation},
        "simulator_failure_mode": simulation.failure_mode(db) if s.servicenow_mode == "mock" else None,
    }


@router.post("/api/servicenow/test-connection")
def test_connection(principal: Principal = Depends(require(Permission.SERVICENOW_SYNC)), db: Session = Depends(get_db)) -> dict:
    """Safe, read-only connectivity check (no writes)."""
    s = get_settings()
    if s.servicenow_mode == "real" and not s.servicenow_configured:
        return {"ok": False, "detail": "ServiceNow real mode selected but credentials are not configured"}
    import time

    started = time.monotonic()
    try:
        result = get_servicenow_client().test_connection()
    except ServiceNowError as exc:
        result = {"ok": False, "detail": str(exc)}
    db.add(
        ServiceNowSyncAttempt(
            operation="test_connection",
            outcome="success" if result.get("ok") else "error",
            error=None if result.get("ok") else result.get("detail"),
            actor=principal.email,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
    )
    record_audit(
        db,
        actor=principal,
        action="servicenow_test_connection",
        target_type="integration",
        target_id="servicenow",
        details={"ok": result.get("ok")},
        outcome="success" if result.get("ok") else "error",
    )
    db.commit()
    return result


@router.get("/api/servicenow/records")
def list_records(page: Page = Depends(page_params), _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    return paginate(db, select(ServiceNowRecord).order_by(ServiceNowRecord.created_at.desc()), page, ser.sn_record)


@router.get("/api/servicenow/records/{record_id}/activity")
def record_activity(record_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    rec = db.get(ServiceNowRecord, record_id)
    if rec is None:
        raise HTTPException(404, "Record not found")
    attempts = db.scalars(
        select(ServiceNowSyncAttempt).where(ServiceNowSyncAttempt.record_id == rec.id).order_by(ServiceNowSyncAttempt.created_at)
    )
    remote: list[dict[str, Any]] = []
    if rec.mode == "mock" and rec.sys_id:
        remote = [
            {"action": a.action, "changes": a.changes, "actor": a.actor, "at": ser.iso(a.created_at)}
            for a in db.scalars(
                select(SnSimActivity).where(SnSimActivity.sys_id == rec.sys_id).order_by(SnSimActivity.created_at)
            )
        ]
    return {
        "record": ser.sn_record(rec),
        "remote_activity": remote,
        "attempts": [
            {
                "operation": a.operation,
                "outcome": a.outcome,
                "error": a.error,
                "http_status": a.http_status,
                "latency_ms": a.latency_ms,
                "actor": a.actor,
                "at": ser.iso(a.created_at),
            }
            for a in attempts
        ],
    }


@router.get("/api/servicenow/attempts")
def list_attempts(page: Page = Depends(page_params), _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    def row(a: ServiceNowSyncAttempt) -> dict[str, Any]:
        rec = db.get(ServiceNowRecord, a.record_id) if a.record_id else None
        return {
            "id": a.id,
            "record_number": rec.number if rec else None,
            "operation": a.operation,
            "table": a.table_name,
            "outcome": a.outcome,
            "error": a.error,
            "http_status": a.http_status,
            "latency_ms": a.latency_ms,
            "actor": a.actor,
            "at": ser.iso(a.created_at),
        }

    return paginate(db, select(ServiceNowSyncAttempt).order_by(ServiceNowSyncAttempt.created_at.desc()), page, row)


@router.post("/api/servicenow/refresh")
def refresh_all(principal: Principal = Depends(require(Permission.SERVICENOW_SYNC)), db: Session = Depends(get_db)) -> dict:
    from app.services.workflow_ops import refresh_servicenow_status

    records = refresh_servicenow_status(db, principal)
    return {"refreshed": len(records)}


@router.get("/api/servicenow/simulator/records")
def simulator_records(table: str = "change_request", _: Principal = Reader, db: Session = Depends(get_db)) -> list[dict]:
    if get_settings().servicenow_mode != "mock":
        raise HTTPException(400, "Simulator not active")
    rows = db.scalars(
        select(SnSimRecord).where(SnSimRecord.table_name == table).order_by(SnSimRecord.sys_created_on.desc()).limit(200)
    )
    return [
        {
            "sys_id": r.sys_id,
            "number": r.number,
            "table": r.table_name,
            "state": r.fields.get("state"),
            "state_label": CHANGE_STATES.get(str(r.fields.get("state"))) if table == "change_request" else r.fields.get("state"),
            "short_description": r.fields.get("short_description") or r.fields.get("name"),
            "correlation_id": r.fields.get("correlation_id"),
            "close_code": r.fields.get("close_code"),
            "created_by": r.sys_created_by,
            "created_on": ser.iso(r.sys_created_on),
            "updated_on": ser.iso(r.sys_updated_on),
        }
        for r in rows
    ]


# ------------------------------------------------------------------ simulation console
class FailureBody(BaseModel):
    mode: Literal["none", "auth_failure", "timeout", "server_error", "lost_response"]
    remaining: int = Field(default=1, ge=-1, le=20)


@router.post("/api/simulation/servicenow/failure")
def set_failure(
    body: FailureBody, principal: Principal = Depends(require(Permission.SIMULATION_CONTROL)), db: Session = Depends(get_db)
) -> dict:
    with domain_errors():
        return simulation.set_failure_mode(db, body.mode, body.remaining, principal)


class AdvanceBody(BaseModel):
    target_state: str | None = Field(default=None, pattern=r"^-?[0-9]$")
    close_code: Literal["successful", "successful_issues", "unsuccessful"] = "successful"


@router.post("/api/simulation/servicenow/records/{record_id}/advance")
def advance(
    record_id: str,
    body: AdvanceBody,
    principal: Principal = Depends(require(Permission.SIMULATION_CONTROL)),
    db: Session = Depends(get_db),
) -> dict:
    with domain_errors():
        result = simulation.advance_change(db, record_id, principal, body.target_state, body.close_code)
    rec = db.get(ServiceNowRecord, record_id)
    from app.services.workflow_ops import refresh_servicenow_status

    if rec:
        refresh_servicenow_status(db, principal, rec.plan_id)
    return result


class PatchBody(BaseModel):
    vendor: str = Field(max_length=64)
    product: str = Field(max_length=64)
    version: str = Field(min_length=1, max_length=64, pattern=r"^[\w.\-+]+$")


@router.post("/api/simulation/devices/{device_id}/patch")
def patch_device(
    device_id: str,
    body: PatchBody,
    principal: Principal = Depends(require(Permission.SIMULATION_CONTROL)),
    db: Session = Depends(get_db),
) -> dict:
    with domain_errors():
        return simulation.apply_patch(db, device_id, body.vendor, body.product, body.version, principal)


@router.get("/api/simulation/devices")
def list_devices(page: Page = Depends(page_params), _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    def row(d: SimDevice) -> dict[str, Any]:
        return {
            "device_id": d.id,
            "computer_dns_name": d.computer_dns_name,
            "os_platform": d.os_platform,
            "last_ip_address": d.last_ip_address,
            "risk_score": d.risk_score,
            "last_seen": ser.iso(d.last_seen),
            "software": [
                {"vendor": s.vendor, "product": s.product, "display_name": s.display_name, "version": s.version}
                for s in d.software
            ],
        }

    return paginate(db, select(SimDevice).order_by(SimDevice.computer_dns_name), page, row)


# ------------------------------------------------------------------ threat intelligence
@router.get("/api/threat-intel/status")
def threat_status(_: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    ti = ThreatIntelService(db)
    snap = ti.snapshot
    cache = dict(db.execute(select(ThreatIntelCache.source, func.count()).group_by(ThreatIntelCache.source)).all())
    vulns = list(db.scalars(select(Vulnerability)))
    return {
        "mode": ti.mode,
        "kev": ti.kev_status(),
        "snapshot": {
            "generated_at": snap.get("generated_at"),
            "cves": len(snap.get("nvd", {})),
            "notice": snap.get("notice"),
            "sources": snap.get("sources"),
        },
        "cache_counts": cache,
        "coverage": {
            "vulnerabilities": len(vulns),
            "kev_known": sum(1 for v in vulns if v.kev is not None),
            "kev_listed": sum(1 for v in vulns if v.kev),
            "epss_known": sum(1 for v in vulns if v.epss_score is not None),
            "nvd_verified": sum(1 for v in vulns if v.evidence_status == "verified"),
        },
        "vulnerabilities": [
            {
                "cve_id": v.cve_id,
                "severity": v.severity,
                "cvss_score": v.cvss_score,
                "kev": v.kev,
                "kev_date_added": v.kev_date_added,
                "kev_due_date": v.kev_due_date,
                "kev_ransomware_use": v.kev_ransomware_use,
                "epss_score": v.epss_score,
                "epss_percentile": v.epss_percentile,
                "epss_date": v.epss_date,
                "intel_sources": v.intel_sources,
                "affected_product": v.affected_product,
            }
            for v in sorted(vulns, key=lambda v: -(v.epss_score or 0))
        ],
    }


@router.get("/api/threat-intel/lookup/{cve_id}")
def lookup(cve_id: str, principal: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    from app.services.normalization import normalize_cve_id

    cve = normalize_cve_id(cve_id)
    if cve is None:
        raise HTTPException(422, "Invalid CVE identifier")
    ti = ThreatIntelService(db)
    out = {
        "cve_id": cve,
        "kev": ti.get_kev(cve).to_dict(),
        "epss": ti.get_epss(cve).to_dict(),
        "nvd": ti.get_nvd(cve, allow_live=True).to_dict(),
    }
    db.commit()
    return out


@router.post("/api/threat-intel/kev/refresh")
def refresh_kev(principal: Principal = Depends(require(Permission.INTEGRATIONS_MANAGE)), db: Session = Depends(get_db)) -> dict:
    """Fetch the live CISA KEV catalog into the cache (works in either mode; offline mode keeps using the snapshot)."""
    try:
        meta = ThreatIntelService(db, mode="live").refresh_kev_catalog()
    except Exception as exc:
        db.commit()
        raise HTTPException(502, f"KEV refresh failed: {type(exc).__name__}: {str(exc)[:200]}") from exc
    record_audit(db, actor=principal, action="kev_refreshed", target_type="integration", target_id="cisa_kev", details=meta)
    db.commit()
    return meta


@router.post("/api/threat-intel/re-enrich")
def re_enrich(principal: Principal = Depends(require(Permission.INTEGRATIONS_MANAGE)), db: Session = Depends(get_db)) -> dict:
    """Re-apply KEV/EPSS/NVD to every vulnerability and re-score open findings."""
    from app.services.vuln_intel import enrich_vulnerability

    ti = ThreatIntelService(db)
    vulns = list(db.scalars(select(Vulnerability)))
    for v in vulns:
        enrich_vulnerability(db, v, ti, v.affected_vendor)
    rescored = 0
    for v in vulns:
        for f in v.findings:
            if f.status in ("open", "in_remediation"):
                assess_finding(db, f)
                rescored += 1
    record_audit(
        db,
        actor=principal,
        action="threat_intel_reenriched",
        target_type="vulnerabilities",
        details={"vulnerabilities": len(vulns), "rescored": rescored, "mode": ti.mode},
    )
    db.commit()
    return {"vulnerabilities": len(vulns), "findings_rescored": rescored, "mode": ti.mode}


# ------------------------------------------------------------------ integrations overview
@router.get("/api/integrations")
def integrations(_: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    ti = ThreatIntelService(db)
    kev = ti.kev_status()
    live_kev = kev.get("live") or {}
    epss_live = db.scalar(select(func.max(ThreatIntelCache.fetched_at)).where(ThreatIntelCache.source == "epss"))
    defender_real = DefenderApiAdapter(s).status()
    imports = db.scalar(select(func.count()).select_from(ScanImport)) or 0

    def item(key: str, name: str, status: str, mode: str, detail: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"key": key, "name": name, "status": status, "mode": mode, "detail": detail, **(extra or {})}

    sn_status = (
        "Mock"
        if s.servicenow_mode == "mock"
        else "Not Configured"
        if not s.servicenow_configured
        else "Connected"
        if _last_success(db)
        else "Unverified"
    )
    return {
        "integrations": [
            item(
                "servicenow",
                "ServiceNow",
                sn_status,
                s.servicenow_mode,
                "Persistent simulator with CMDB, change requests and failure injection"
                if s.servicenow_mode == "mock"
                else f"Table API at {s.servicenow_instance_url or '(not set)'}; writes {'enabled' if s.enable_servicenow_writes else 'disabled'}",
            ),
            item(
                "defender_mock",
                "Microsoft Defender for Endpoint (simulated)",
                "Mock",
                "mock",
                MockDefenderAdapter(db).status().detail,
            ),
            item("defender", "Microsoft Defender for Endpoint", defender_real.status, "live", defender_real.detail),
            item(
                "cisa_kev",
                "CISA KEV",
                "Connected"
                if live_kev.get("status") == "ok"
                else "Error"
                if live_kev.get("status") == "error"
                else "Mock"
                if s.threat_intel_mode == "offline"
                else "Unverified",
                s.threat_intel_mode,
                (
                    f"Live catalog {live_kev.get('catalog_version')} fetched {live_kev.get('fetched_at')}"
                    if live_kev.get("status") == "ok"
                    else f"Offline snapshot of real catalog {kev['snapshot'].get('catalog_version')} "
                    f"({kev['snapshot'].get('age_hours')} h old)"
                ),
            ),
            item(
                "first_epss",
                "FIRST EPSS",
                "Connected" if epss_live else "Mock" if s.threat_intel_mode == "offline" else "Unverified",
                s.threat_intel_mode,
                f"Last live fetch {ser.iso(epss_live)}" if epss_live else "Offline snapshot of real EPSS scores",
            ),
            item(
                "nvd",
                "NVD CVE API (optional)",
                "Mock" if s.threat_intel_mode == "offline" else "Unverified",
                s.threat_intel_mode,
                "Offline snapshot of real NVD records; live lookups are rate limited (5 req/30 s without API key)",
            ),
            item("file_import", "CSV / JSON import", "Connected", "file", f"{imports} import(s) processed"),
            item(
                "ai_provider",
                "AI model provider",
                provider_status(s)["status"],
                s.ai_provider,
                f"{provider_status(s)['provider']} / {provider_status(s)['model'] or 'n/a'} {provider_status(s)['detail']}",
            ),
            item(
                "langfuse",
                "Langfuse (optional)",
                "Not Configured" if not s.langfuse_public_key else "Unverified",
                "live",
                "Local tracing is always available in Agent Workflows; Langfuse export is optional",
            ),
            *[
                {"key": a.name, "name": a.display_name, "status": "Unsupported", "mode": "none", "detail": a.status().detail}
                for a in (
                    UnsupportedScannerAdapter("tenable", "Tenable Vulnerability Management", "the Tenable.io exports API"),
                    UnsupportedScannerAdapter("qualys", "Qualys VMDR", "the Qualys VM detection API"),
                )
            ],
        ]
    }


@router.post("/api/integrations/defender/test")
def test_defender(principal: Principal = Depends(require(Permission.INTEGRATIONS_MANAGE)), db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    if not s.defender_configured:
        return {"ok": False, "detail": "Defender credentials not configured"}
    result = DefenderApiAdapter(s).test_connection()
    record_audit(
        db,
        actor=principal,
        action="defender_test_connection",
        target_type="integration",
        target_id="defender",
        details={"ok": result["ok"]},
        outcome="success" if result["ok"] else "error",
    )
    db.commit()
    return result


# ------------------------------------------------------------------ settings / admin
@router.get("/api/settings")
def get_settings_view(_: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    policy = get_risk_policy(db)
    return {
        "risk_policy": policy.model_dump() | {"policy_version": policy.policy_version},
        "environment": {
            "app_env": s.app_env,
            "ai_provider": s.ai_provider,
            "ai_model": s.ai_model or None,
            "servicenow_mode": s.servicenow_mode,
            "threat_intel_mode": s.threat_intel_mode,
            "defender_mode": s.defender_mode,
            "separation_of_duties": s.separation_of_duties,
            "enable_servicenow_writes": s.enable_servicenow_writes,
            "session_ttl_minutes": s.session_ttl_minutes,
        },
        "roles": {role: sorted(p.value for p in perms) for role, perms in ROLE_PERMISSIONS.items()},
    }


@router.put("/api/settings/risk-policy")
def update_policy(
    body: RiskPolicy, principal: Principal = Depends(require(Permission.SETTINGS_MANAGE)), db: Session = Depends(get_db)
) -> dict:
    try:
        policy = set_risk_policy(db, body, principal)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    db.commit()
    return policy.model_dump() | {"policy_version": policy.policy_version}


@router.get("/api/users")
def list_users(_: Principal = Reader, db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "last_login_at": ser.iso(u.last_login_at),
        }
        for u in db.scalars(select(User).order_by(User.role, User.email))
    ]


@router.get("/api/audit")
def list_audit(
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    outcome: str | None = None,
    actor: str | None = None,
    page: Page = Depends(page_params),
    _: Principal = Depends(require(Permission.AUDIT_READ)),
    db: Session = Depends(get_db),
) -> dict:
    q = select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if action:
        q = q.where(AuditEvent.action.in_(action.split(",")))
    if target_type:
        q = q.where(AuditEvent.target_type == target_type)
    if target_id:
        q = q.where(AuditEvent.target_id == target_id)
    if outcome:
        q = q.where(AuditEvent.outcome == outcome)
    if actor:
        q = q.where(AuditEvent.actor_label.ilike(f"%{actor}%"))
    return paginate(
        db,
        q,
        page,
        lambda e: {
            "id": e.id,
            "actor": e.actor_label,
            "action": e.action,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "previous_state": e.previous_state,
            "new_state": e.new_state,
            "details": e.details,
            "outcome": e.outcome,
            "correlation_id": e.correlation_id,
            "ip_address": e.ip_address,
            "created_at": ser.iso(e.created_at),
        },
    )
