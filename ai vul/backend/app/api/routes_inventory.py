"""Dashboard, analytics, vulnerabilities, findings, assets."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.api import serializers as ser
from app.api.deps import Page, domain_errors, page_params, paginate
from app.core.db import get_db
from app.graphs.runner import get_runner
from app.integrations.defender.mock import MockDefenderAdapter
from app.integrations.scanners.file_import import parse_csv, parse_json
from app.models.enterprise import Asset, AssetDependency, BusinessService
from app.models.remediation import RemediationPlan, RiskAssessment
from app.models.servicenow import ServiceNowRecord
from app.models.simulation import SimDevice
from app.models.vulnerability import Finding, ScanEvidence, ScanImport, Vulnerability
from app.models.workflow import WorkflowRun
from app.security.auth import Principal, require
from app.security.permissions import Permission
from app.services import metrics, workflow_ops
from app.services.audit import record_audit
from app.services.cmdb_sync import sync_cmdb
from app.services.ingestion import ingest_findings
from app.services.risk_service import assess_finding

router = APIRouter(tags=["inventory"])
Reader = Depends(require(Permission.READ))


@router.get("/api/dashboard")
def get_dashboard(_: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    return metrics.dashboard(db)


@router.get("/api/analytics")
def get_analytics(_: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    return metrics.analytics(db)


# ------------------------------------------------------------------ vulnerabilities (aggregated per CVE)
def _vuln_rows(db: Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for v in db.scalars(select(Vulnerability)):
        fs = v.findings
        open_fs = [f for f in fs if f.status in ("open", "in_remediation")]
        scores = [f.risk_score for f in fs if f.risk_score is not None]
        top = max(fs, key=lambda f: f.risk_score or 0) if fs else None
        services = sorted({f.asset.business_service.name for f in fs if f.asset and f.asset.business_service})
        impact = None
        if top and top.asset:
            impact = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}.get(
                top.asset.business_criticality or ""
            )
        statuses = {f.status for f in fs}
        status = (
            "remediated" if statuses <= {"remediated", "closed"} else "in_remediation" if "in_remediation" in statuses else "open"
        )
        rows.append(
            {
                "id": v.id,
                "cve_id": v.cve_id,
                "title": v.title,
                "severity": v.severity,
                "cvss_score": v.cvss_score,
                "max_risk_score": max(scores) if scores else None,
                "risk_level": top.risk_level if top else None,
                "epss_score": v.epss_score,
                "epss_percentile": v.epss_percentile,
                "kev": v.kev,
                "affected_assets": len({f.asset_id or f.reported_asset_identifier for f in fs}),
                "open_findings": len(open_fs),
                "business_services": services,
                "business_impact": impact,
                "remediation_status": status,
                "last_detected_at": ser.iso(v.last_detected_at),
                "affected_product": v.affected_product,
                "evidence_status": v.evidence_status,
            }
        )
    return rows


SORTABLE = {"cve_id", "severity", "cvss_score", "max_risk_score", "epss_score", "affected_assets", "last_detected_at"}


@router.get("/api/vulnerabilities")
def list_vulnerabilities(
    q: str | None = None,
    severity: str | None = None,
    kev: bool | None = None,
    status: str | None = None,
    min_risk: int | None = Query(None, ge=0, le=100),
    sort: str = "max_risk_score",
    order: Literal["asc", "desc"] = "desc",
    page: Page = Depends(page_params),
    _: Principal = Reader,
    db: Session = Depends(get_db),
) -> dict:
    rows = _vuln_rows(db)
    if q:
        ql = q.lower()
        rows = [
            r
            for r in rows
            if ql in r["cve_id"].lower()
            or ql in (r["affected_product"] or "").lower()
            or any(ql in s.lower() for s in r["business_services"])
            or ql in (r["title"] or "").lower()
        ]
    if severity:
        rows = [r for r in rows if r["severity"] in severity.split(",")]
    if kev is not None:
        rows = [r for r in rows if bool(r["kev"]) == kev]
    if status:
        rows = [r for r in rows if r["remediation_status"] == status]
    if min_risk is not None:
        rows = [r for r in rows if (r["max_risk_score"] or 0) >= min_risk]
    key = sort if sort in SORTABLE else "max_risk_score"
    rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "none": 1, "unknown": 0}
    present = sorted(
        (r for r in rows if r[key] is not None),
        key=lambda r: rank.get(r[key], 0) if key == "severity" else r[key],
        reverse=order == "desc",
    )
    rows = present + [r for r in rows if r[key] is None]  # unknown values always last
    total = len(rows)
    start = (page.page - 1) * page.page_size
    return {"items": rows[start : start + page.page_size], "total": total, "page": page.page, "page_size": page.page_size}


@router.get("/api/vulnerabilities/export.csv")
def export_vulnerabilities(ids: str | None = None, _: Principal = Reader, db: Session = Depends(get_db)) -> StreamingResponse:
    rows = _vuln_rows(db)
    if ids:
        wanted = set(ids.split(","))
        rows = [r for r in rows if r["id"] in wanted or r["cve_id"] in wanted]
    buf = io.StringIO()
    cols = [
        "cve_id",
        "severity",
        "cvss_score",
        "max_risk_score",
        "risk_level",
        "epss_score",
        "kev",
        "affected_assets",
        "open_findings",
        "business_impact",
        "remediation_status",
        "last_detected_at",
    ]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r[k] is None else r[k]) for k in cols})
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aegis-vulnerabilities.csv"},
    )


@router.get("/api/vulnerabilities/{cve_id}")
def get_vulnerability(cve_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    v = db.scalar(select(Vulnerability).where(Vulnerability.cve_id == cve_id.upper()))
    if v is None:
        raise HTTPException(404, "Vulnerability not found")
    findings = sorted(v.findings, key=lambda f: f.risk_score or 0, reverse=True)
    return {"vulnerability": ser.vulnerability(v), "findings": [ser.finding_row(f) for f in findings]}


# ------------------------------------------------------------------ findings
def _finding_query(
    q: str | None, risk_level: str | None, status: str | None, kev: bool | None, service: str | None, correlation: str | None
) -> Select[Any]:
    query = select(Finding).join(Vulnerability).outerjoin(Asset, Finding.asset_id == Asset.id).outerjoin(BusinessService)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(Vulnerability.cve_id).like(like),
                func.lower(Finding.reported_asset_identifier).like(like),
                func.lower(func.coalesce(Asset.hostname, "")).like(like),
            )
        )
    if risk_level:
        query = query.where(Finding.risk_level.in_(risk_level.split(",")))
    if status:
        query = query.where(Finding.status.in_(status.split(",")))
    if kev is not None:
        query = query.where(Vulnerability.kev.is_(kev))
    if service:
        query = query.where(BusinessService.name == service)
    if correlation:
        query = query.where(Finding.correlation_status == correlation)
    return query.order_by(Finding.risk_score.desc().nulls_last(), Finding.id)


@router.get("/api/findings")
def list_findings(
    q: str | None = None,
    risk_level: str | None = None,
    status: str | None = None,
    kev: bool | None = None,
    service: str | None = None,
    correlation: str | None = None,
    page: Page = Depends(page_params),
    _: Principal = Reader,
    db: Session = Depends(get_db),
) -> dict:
    return paginate(db, _finding_query(q, risk_level, status, kev, service, correlation), page, ser.finding_row)


@router.get("/api/findings/{finding_id}")
def get_finding(finding_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    f = db.get(Finding, finding_id)
    if f is None:
        raise HTTPException(404, "Finding not found")
    risk = db.scalar(
        select(RiskAssessment).where(RiskAssessment.finding_id == f.id).order_by(RiskAssessment.calculated_at.desc())
    )
    plans = list(
        db.scalars(select(RemediationPlan).where(RemediationPlan.finding_id == f.id).order_by(RemediationPlan.created_at.desc()))
    )
    runs = list(db.scalars(select(WorkflowRun).where(WorkflowRun.finding_id == f.id).order_by(WorkflowRun.started_at.desc())))
    evidence = list(db.scalars(select(ScanEvidence).where(ScanEvidence.finding_id == f.id).order_by(ScanEvidence.scanned_at)))
    records = list(db.scalars(select(ServiceNowRecord).where(ServiceNowRecord.plan_id.in_([p.id for p in plans]))))
    device = db.get(SimDevice, f.reported_device_id) if f.reported_device_id else None
    return {
        "finding": ser.finding_row(f)
        | {
            "reported_asset_identifier": f.reported_asset_identifier,
            "reported_ip": f.reported_ip,
            "reported_device_id": f.reported_device_id,
            "software_vendor": f.software_vendor,
            "correlation_confidence": f.correlation_confidence,
            "correlation_candidates": f.correlation_candidates,
            "source_evidence": f.source_evidence,
            "scanner_finding_id": f.scanner_finding_id,
            "duplicate_count": f.duplicate_count,
            "remediated_at": ser.iso(f.remediated_at),
        },
        "vulnerability": ser.vulnerability(f.vulnerability),
        "asset": ser.asset(f.asset),
        "risk": ser.risk_assessment(risk),
        "plans": [ser.plan(p, db, full=False) for p in plans],
        "workflow_runs": [ser.workflow_run(r, db) for r in runs],
        "evidence": [ser.evidence(e) for e in evidence],
        "servicenow_records": [ser.sn_record(r) for r in records],
        "simulated_device": None
        if device is None
        else {
            "device_id": device.id,
            "computer_dns_name": device.computer_dns_name,
            "software": [
                {"vendor": s.vendor, "product": s.product, "display_name": s.display_name, "version": s.version}
                for s in device.software
            ],
        },
    }


@router.post("/api/findings/{finding_id}/investigate", status_code=202)
def investigate(
    finding_id: str, principal: Principal = Depends(require(Permission.INVESTIGATE)), db: Session = Depends(get_db)
) -> dict:
    with domain_errors():
        run = get_runner().start(finding_id, principal.id)
    record_audit(
        db,
        actor=principal,
        action="investigation_started",
        target_type="finding",
        target_id=finding_id,
        details={"workflow_run_id": run.id},
    )
    db.commit()
    return {"workflow_run_id": run.id, "status": run.status}


@router.post("/api/findings/{finding_id}/reassess")
def reassess(
    finding_id: str, principal: Principal = Depends(require(Permission.INVESTIGATE)), db: Session = Depends(get_db)
) -> dict:
    f = db.get(Finding, finding_id)
    if f is None:
        raise HTTPException(404, "Finding not found")
    ra, _ = assess_finding(db, f)
    record_audit(
        db, actor=principal, action="risk_reassessed", target_type="finding", target_id=f.id, new_state={"score": ra.score}
    )
    db.commit()
    return ser.risk_assessment(ra) or {}


@router.post("/api/findings/{finding_id}/rescan")
def rescan(finding_id: str, principal: Principal = Depends(require(Permission.VERIFY)), db: Session = Depends(get_db)) -> dict:
    with domain_errors():
        ev = workflow_ops.submit_rescan(db, finding_id, principal)
    return ser.evidence(ev)


class EvidenceUpload(BaseModel):
    asset_identifier: str = Field(max_length=255)
    device_id: str | None = Field(default=None, max_length=64)
    scanner: str = Field(default="upload", max_length=32)
    scan_id: str | None = Field(default=None, max_length=64)
    scanned_at: datetime
    vulnerable: bool
    software_name: str | None = Field(default=None, max_length=128)
    software_version: str | None = Field(default=None, max_length=64)


@router.post("/api/findings/{finding_id}/evidence")
def upload_evidence(
    finding_id: str,
    body: EvidenceUpload,
    principal: Principal = Depends(require(Permission.VERIFY)),
    db: Session = Depends(get_db),
) -> dict:
    with domain_errors():
        ev = workflow_ops.submit_uploaded_evidence(db, finding_id, principal, body.model_dump())
    return ser.evidence(ev)


@router.post("/api/findings/import")
async def import_findings(
    file: UploadFile = File(...),
    scanner: str = Form("csv_import"),
    principal: Principal = Depends(require(Permission.IMPORT_FINDINGS)),
    db: Session = Depends(get_db),
) -> dict:
    content = await file.read()
    name = (file.filename or "upload")[:255]
    fmt = "json" if name.lower().endswith(".json") else "csv"
    scanner = "".join(c for c in scanner.lower() if c.isalnum() or c == "_")[:32] or f"{fmt}_import"
    with domain_errors():
        rows = parse_json(content, scanner) if fmt == "json" else parse_csv(content, scanner)
    report = ingest_findings(db, rows, submitted_by=principal.email)
    imp = ScanImport(
        filename=name,
        file_format=fmt,
        scanner=scanner,
        uploaded_by=principal.email,
        total_rows=report.total,
        created=report.created,
        duplicates=report.duplicates,
        invalid=report.invalid,
        errors=report.errors[:100],
    )
    db.add(imp)
    record_audit(
        db,
        actor=principal,
        action="findings_imported",
        target_type="scan_import",
        target_id=imp.id,
        details={k: v for k, v in report.to_dict().items() if k not in ("finding_ids", "errors")},
    )
    db.commit()
    return {"import_id": imp.id} | {k: v for k, v in report.to_dict().items()}


@router.get("/api/findings-imports")
def list_imports(_: Principal = Reader, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(ScanImport).order_by(ScanImport.created_at.desc()).limit(50))
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "format": r.file_format,
            "scanner": r.scanner,
            "uploaded_by": r.uploaded_by,
            "total_rows": r.total_rows,
            "created": r.created,
            "duplicates": r.duplicates,
            "invalid": r.invalid,
            "errors": r.errors,
            "created_at": ser.iso(r.created_at),
        }
        for r in rows
    ]


@router.post("/api/scanners/defender/refresh")
def refresh_defender(principal: Principal = Depends(require(Permission.IMPORT_FINDINGS)), db: Session = Depends(get_db)) -> dict:
    """Pull the latest Defender findings (simulated tenant in mock mode) through the ingestion pipeline."""
    report = ingest_findings(db, MockDefenderAdapter(db).refresh_findings(), submitted_by=principal.email)
    record_audit(
        db,
        actor=principal,
        action="defender_refresh",
        target_type="scanner",
        target_id="mock_defender",
        details={"created": report.created, "duplicates": report.duplicates},
    )
    db.commit()
    return {k: v for k, v in report.to_dict().items() if k != "finding_ids"}


# ------------------------------------------------------------------ assets
@router.get("/api/assets")
def list_assets(
    q: str | None = None,
    environment: str | None = None,
    criticality: str | None = None,
    service: str | None = None,
    exposed: bool | None = None,
    page: Page = Depends(page_params),
    _: Principal = Reader,
    db: Session = Depends(get_db),
) -> dict:
    query = select(Asset).outerjoin(BusinessService)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(Asset.hostname).like(like),
                func.lower(func.coalesce(Asset.fqdn, "")).like(like),
                Asset.id.like(f"%{q.upper()}%"),
            )
        )
    if environment:
        query = query.where(Asset.environment == environment)
    if criticality:
        query = query.where(Asset.business_criticality == criticality)
    if service:
        query = query.where(BusinessService.name == service)
    if exposed is not None:
        query = query.where(Asset.internet_exposed.is_(exposed))
    query = query.order_by(Asset.id)

    def row(a: Asset) -> dict[str, Any]:
        open_f = [f for f in a.findings if f.status in ("open", "in_remediation")]
        return (ser.asset(a) or {}) | {
            "open_findings": len(open_f),
            "max_risk_score": max((f.risk_score or 0 for f in open_f), default=None),
        }

    return paginate(db, query, page, row)


@router.get("/api/assets/{asset_id}")
def get_asset(asset_id: str, _: Principal = Reader, db: Session = Depends(get_db)) -> dict:
    a = db.get(Asset, asset_id)
    if a is None:
        raise HTTPException(404, "Asset not found")
    deps = db.scalars(select(AssetDependency).where(AssetDependency.source_asset_id == a.id))
    used = db.scalars(select(AssetDependency).where(AssetDependency.target_asset_id == a.id))
    return {
        "asset": ser.asset(a),
        "findings": [ser.finding_row(f) for f in a.findings],
        "depends_on": [ser.asset(db.get(Asset, d.target_asset_id)) for d in deps],
        "used_by": [ser.asset(db.get(Asset, d.source_asset_id)) for d in used],
    }


@router.get("/api/business-services")
def list_services(_: Principal = Reader, db: Session = Depends(get_db)) -> list[dict]:
    out = []
    for s in db.scalars(select(BusinessService).order_by(BusinessService.name)):
        open_f = [f for a in s.assets for f in a.findings if f.status in ("open", "in_remediation")]
        out.append(
            (ser.service(s) or {})
            | {
                "assets": len(s.assets),
                "open_findings": len(open_f),
                "critical_findings": sum(1 for f in open_f if f.risk_level == "critical"),
            }
        )
    return out


@router.post("/api/assets/sync")
def sync_assets(principal: Principal = Depends(require(Permission.INTEGRATIONS_MANAGE)), db: Session = Depends(get_db)) -> dict:
    try:
        stats = sync_cmdb(db, actor=principal.email)
    except Exception as exc:
        db.commit()
        raise HTTPException(502, f"CMDB synchronisation failed: {type(exc).__name__}: {str(exc)[:200]}") from exc
    record_audit(db, actor=principal, action="cmdb_sync", target_type="cmdb", details=stats)
    db.commit()
    return stats
