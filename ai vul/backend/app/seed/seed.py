"""Seed the simulated enterprise end to end through the real pipelines.

Order of operations (each step uses production code paths, not raw inserts):
1. Demo users (development-only credentials).
2. Simulated ServiceNow CMDB (services, servers, relationships, change history).
3. CMDB -> asset inventory sync through the ServiceNow adapter.
4. Simulated Defender tenant (devices + installed software).
5. Defender scan -> normalisation -> dedup -> enrichment -> correlation -> risk scoring.
6. Historical investigations run through the LangGraph workflow, with real approvals,
   ServiceNow synchronisation, simulated patching and verification.

Usage:  python -m app.seed.seed [--reset] [--no-history]
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import random
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import Base, get_engine, session_scope
from app.core.types import utcnow
from app.integrations.defender.mock import MockDefenderAdapter
from app.integrations.servicenow.mock import MockServiceNowClient
from app.models import (
    ApprovalDecision,
    ApprovalRequest,
    AuditEvent,
    Finding,
    RemediationPlan,
    RiskAssessment,
    ScanEvidence,
    ServiceNowRecord,
    ServiceNowSyncAttempt,
    SimDevice,
    SimDeviceSoftware,
    SnSimRecord,
    User,
    WorkflowEvent,
    WorkflowRun,
)
from app.models.workflow import AgentExecution, ToolCall
from app.security.auth import Principal
from app.security.passwords import hash_password
from app.seed.northstar import (
    CRIT,
    DEMO_USERS,
    DEPENDENCIES,
    DEV_ONLY_PASSWORD,
    DOMAIN,
    EXTRA_DEVICES,
    HOSTS,
    LINUX_BASE,
    OCTET,
    PACKAGES,
    SERVICES,
    SUBDOMAIN,
    WINDOWS_SERVER_BASE,
    WORKSTATION_BASE,
    Host,
)
from app.services.cmdb_sync import sync_cmdb
from app.services.ingestion import ingest_findings

log = logging.getLogger("aegis.seed")
RNG_SEED = 20261025


def device_id(name: str, salt: str = "") -> str:
    return hashlib.sha1(f"northstar-{name}-{salt}".encode()).hexdigest()


def _sys_id(name: str) -> str:
    return hashlib.md5(f"sn-{name}".encode()).hexdigest()


def seed_users(db: Session) -> dict[str, User]:
    settings = get_settings()
    password = os.environ.get("SEED_DEMO_PASSWORD", DEV_ONLY_PASSWORD)
    if settings.app_env == "production" and password == DEV_ONLY_PASSWORD:
        raise RuntimeError("Refusing to seed development demo passwords in production; set SEED_DEMO_PASSWORD")
    users: dict[str, User] = {}
    for email, name, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, full_name=name, role=role, password_hash=hash_password(password))
            db.add(user)
        users[email] = user
    db.flush()
    return users


def _host_meta(h: Host, idx: int) -> dict[str, Any]:
    sub = SUBDOMAIN[h.service]
    fqdn = h.fqdn_override or f"{h.hostname}.{sub}.{DOMAIN}"
    ip = h.ip_override or f"10.{OCTET[h.service]}.{(idx // 50) + 1}.{(idx % 50) + 10}"
    return {"fqdn": fqdn, "ip": ip}


def seed_servicenow_cmdb() -> None:
    """Populate the ServiceNow simulator through the same client used at runtime."""
    client = MockServiceNowClient(actor="cmdb.import")
    with session_scope() as db:
        if db.scalar(select(func.count()).select_from(SnSimRecord).where(SnSimRecord.table_name == "cmdb_ci_server")):
            return
    with session_scope() as db:
        for key, (name, division, crit, svc_owner, desc) in SERVICES.items():
            db.add(
                SnSimRecord(
                    table_name="cmdb_ci_service",
                    sys_id=_sys_id(f"svc-{key}"),
                    number=None,
                    fields={
                        "name": name,
                        "busines_criticality": crit,
                        "u_division": division,
                        "owned_by.name": svc_owner,
                        "short_description": desc,
                    },
                    sys_created_by="cmdb.import",
                )
            )
        for idx, h in enumerate(HOSTS):
            meta = _host_meta(h, idx)
            owner: str | None = (
                SERVICES[h.service][3]
                if (h.owner == "default" and h.service)
                else ("End User Computing" if h.platform == "workstation" else "Infrastructure Operations")
                if h.owner == "default"
                else h.owner
            )
            sys_class = {
                "linux": "cmdb_ci_linux_server",
                "windows_server": "cmdb_ci_win_server",
                "workstation": "cmdb_ci_computer",
            }[h.platform]
            if h.cloud:
                sys_class = "cmdb_ci_vm_instance"
            os_name = {
                "linux": "Linux Red Hat",
                "windows_server": "Windows 2022 Datacenter",
                "workstation": "Windows 11 Enterprise",
            }[h.platform]
            fields = {
                "asset_tag": f"ASSET-{1001 + idx}",
                "name": h.hostname,
                "fqdn": meta["fqdn"],
                "ip_address": meta["ip"],
                "os": os_name,
                "os_version": {"linux": "9.4", "windows_server": "21H2", "workstation": "23H2"}[h.platform],
                "environment": h.env.capitalize(),
                "busines_criticality": CRIT[h.criticality],
                "owned_by.name": owner or "",
                "support_group.name": f"{SERVICES[h.service][0]} Support" if h.service else "Service Desk",
                "operational_status": h.operational,
                "u_internet_facing": "" if h.internet is None else str(h.internet).lower(),
                "location.name": {"aws": "AWS us-east-1", "azure": "Azure West Europe"}.get(h.cloud or "", "Frankfurt DC1"),
                "u_business_service": _sys_id(f"svc-{h.service}") if h.service else "",
                "u_defender_device_id": device_id(h.hostname) if (h.defender and idx % 2 == 0) else "",
                "sys_class_name": sys_class,
                "u_cloud_provider": h.cloud or "",
            }
            db.add(
                SnSimRecord(
                    table_name="cmdb_ci_server",
                    sys_id=_sys_id(f"ci-{idx}-{h.hostname}"),
                    fields=fields,
                    sys_created_by="cmdb.import",
                )
            )
        first_idx: dict[str, int] = {}
        for idx, h in enumerate(HOSTS):
            first_idx.setdefault(h.hostname, idx)
        for parent, child in DEPENDENCIES:
            db.add(
                SnSimRecord(
                    table_name="cmdb_rel_ci",
                    sys_id=_sys_id(f"rel-{parent}-{child}"),
                    fields={
                        "parent": _sys_id(f"ci-{first_idx[parent]}-{parent}"),
                        "child": _sys_id(f"ci-{first_idx[child]}-{child}"),
                        "type": "Depends on::Used by",
                    },
                    sys_created_by="cmdb.import",
                )
            )
    # Historical (pre-Aegis) change requests so change-risk analysis has history to read.
    history = [
        ("mq-broker-01", "Upgrade JVM on message broker", "successful"),
        ("mq-broker-01", "Rotate broker TLS certificates", "successful"),
        ("pay-api-01", "Deploy payments API release 4.2", "successful"),
        ("pay-api-01", "Emergency rollback of release 4.1", "unsuccessful"),
        ("store-web-01", "Apache configuration hardening", "successful"),
    ]
    first = {h.hostname: i for i, h in reversed(list(enumerate(HOSTS)))}
    for host, desc, code in history:
        client.create(
            "change_request",
            {
                "short_description": desc,
                "description": desc,
                "type": "normal",
                "cmdb_ci": _sys_id(f"ci-{first[host]}-{host}"),
                "state": "3",
                "close_code": code,
                "close_notes": "Historical change (simulated)",
                "approval": "approved",
            },
        )


def seed_defender(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(SimDevice)):
        return
    rng = random.Random(RNG_SEED)
    now = utcnow()

    def add_device(name: str, dns: str, platform: str, ip: str, vulns: list[tuple[str, str]], cloud: bool, dev_id: str) -> None:
        dev = SimDevice(
            id=dev_id,
            computer_dns_name=dns,
            os_platform={"linux": "Linux", "windows_server": "WindowsServer2022", "workstation": "Windows11"}[platform],
            os_version={"linux": "RHEL 9.4", "windows_server": "21H2", "workstation": "23H2"}[platform],
            last_ip_address=ip,
            health_status="Active",
            is_cloud=cloud,
            risk_score="High" if vulns else "Low",
            exposure_level="Medium" if vulns else "Low",
            machine_tags=["cloud"] if cloud else [],
            last_seen=now - timedelta(hours=rng.randint(1, 20)),
        )
        base = {"linux": LINUX_BASE, "windows_server": WINDOWS_SERVER_BASE, "workstation": WORKSTATION_BASE}[platform]
        installed = dict.fromkeys(base, None) | dict(vulns)
        for key, vuln_version in installed.items():
            vendor, product, display, safe, edition = PACKAGES[key]
            days = rng.randint(5, 80) if vuln_version else rng.randint(30, 200)
            dev.software.append(
                SimDeviceSoftware(
                    vendor=vendor,
                    product=product,
                    display_name=display,
                    version=vuln_version or safe,
                    sw_edition=edition,
                    updated_at=now - timedelta(days=days, hours=rng.randint(0, 23)),
                )
            )
        db.add(dev)

    for idx, h in enumerate(HOSTS):
        if not h.defender:
            continue
        meta = _host_meta(h, idx)
        dns = h.hostname if h.platform == "workstation" else meta["fqdn"]
        add_device(h.hostname, dns, h.platform, meta["ip"], h.vulns, bool(h.cloud), device_id(h.hostname))
    for extra in EXTRA_DEVICES:
        add_device(
            extra["name"],
            extra["name"],
            extra["platform"],
            extra["ip"],
            extra["vulns"],
            False,
            device_id(extra["name"], "unmanaged"),
        )
    db.flush()


# ---------------------------------------------------------------------------------- history
def _finding(db: Session, hostname: str, cve: str) -> Finding:
    from app.models.vulnerability import Vulnerability

    f = db.scalar(
        select(Finding)
        .join(Vulnerability)
        .where(Vulnerability.cve_id == cve, Finding.reported_asset_identifier.like(f"{hostname}%"))
    )
    if f is None:
        raise RuntimeError(f"seed history: finding {hostname}/{cve} not found")
    return f


HISTORY = [
    # (hostname, cve, outcome, days_ago)
    ("ledger-app-01", "CVE-2022-22965", "verified", 34),
    ("store-web-02", "CVE-2022-3602", "in_progress", 21),
    ("order-edi-01", "CVE-2022-3602", "scheduled", 12),
    ("ci-jenkins-01", "CVE-2024-23897", "closed_unverified", 18),
    ("collab-chat-01", "CVE-2023-45853", "synced", 6),
    ("mes-hmi-01", "CVE-2025-0411", "rejected", 9),
    ("collab-wiki-01", "CVE-2023-22515", "pending", 2),
    ("ws-fin-0142", "CVE-2023-38831", "pending", 1),
    ("pay-db-01", "CVE-2022-0847", "draft", 4),
    ("idp-02", "CVE-2023-38545", "draft", 3),
    ("ledger-recon-01", "CVE-2022-42889", "draft", 5),
    ("scm-portal-02", "CVE-2024-3094", "draft", 7),
    ("mq-monitor-01", "CVE-2024-6387", "draft", 8),
    ("ci-runner-01", "CVE-2023-38545", "draft", 10),
    ("order-worker-01", "CVE-2022-42889", "draft", 11),
    ("legacy-erp-01", "CVE-2021-41773", "manual_review", 3),
]


def seed_history(users: dict[str, User]) -> None:
    from app.graphs.runner import WorkflowRunner, set_runner
    from app.services import simulation, workflow_ops

    runner = WorkflowRunner(synchronous=True)
    set_runner(runner)
    analyst = Principal.from_user(users["analyst@northstar.example"])
    approver = Principal.from_user(users["approver@northstar.example"])
    run_offsets: dict[str, int] = {}
    with session_scope() as db:
        if db.scalar(select(func.count()).select_from(WorkflowRun)):
            return
        targets = [(_finding(db, h, c).id, outcome, days) for h, c, outcome, days in HISTORY]
    for finding_id, outcome, days in targets:
        run = runner.start(finding_id, analyst.id)
        run_offsets[run.id] = days
        if outcome == "manual_review":
            continue
        with session_scope() as db:
            plan = db.scalar(select(RemediationPlan).where(RemediationPlan.workflow_run_id == run.id))
            assert plan is not None, f"no plan for {run.id}"
            plan_id = plan.id
        if outcome == "draft":
            continue
        with session_scope() as db:
            req = workflow_ops.request_approval(db, plan_id, analyst, "Please review: generated by investigation")
            req_id = req.id
        if outcome == "pending":
            continue
        with session_scope() as db:
            if outcome == "rejected":
                workflow_ops.decide_approval(
                    db,
                    req_id,
                    approver,
                    "reject",
                    "OT vendor certification required before patching HMI software; re-plan with the plant systems team",
                )
                continue
            workflow_ops.decide_approval(db, req_id, approver, "approve", "Approved for the next maintenance window")
        with session_scope() as db:
            change = db.scalar(
                select(ServiceNowRecord).where(
                    ServiceNowRecord.plan_id == plan_id, ServiceNowRecord.table_name == "change_request"
                )
            )
            if change is None:
                continue
            # New -> Assess -> Authorize -> Scheduled -> Implement -> Review -> Closed
            steps = {"verified": 6, "in_progress": 4, "scheduled": 3, "closed_unverified": 6, "synced": 0}[outcome]
            for _ in range(steps):
                simulation.advance_change(db, change.id, analyst)
            workflow_ops.refresh_servicenow_status(db, analyst, plan_id)
        if outcome == "verified":
            with session_scope() as db:
                f = db.get(Finding, finding_id)
                assert f is not None
                vendor = f.software_vendor or ""
                product = next(v[1] for v in PACKAGES.values() if v[0] == vendor and f.software_name == v[2])
                safe = next(v[3] for v in PACKAGES.values() if v[0] == vendor and v[1] == product)
                simulation.apply_patch(db, f.reported_device_id or "", vendor, product, safe, analyst)
            with session_scope() as db:
                workflow_ops.submit_rescan(db, finding_id, analyst)
    _backdate(run_offsets)
    set_runner(None)


def _backdate(offsets: dict[str, int]) -> None:
    """Spread seeded history over past weeks so trend analytics have a realistic shape.

    Implemented with ORM loops (not SQL date arithmetic) so it is portable across databases.
    """

    def shift(rows: Any, cols: list[str], delta: timedelta) -> None:
        for row in rows:
            for col in cols:
                value = getattr(row, col)
                if value is not None:
                    setattr(row, col, value - delta)

    with session_scope() as db:
        for run_id, days in offsets.items():
            delta = timedelta(days=days)
            run = db.get(WorkflowRun, run_id)
            if run is None:
                continue
            plans = list(db.scalars(select(RemediationPlan).where(RemediationPlan.workflow_run_id == run_id)))
            plan_ids = [p.id for p in plans]
            approvals = list(db.scalars(select(ApprovalRequest).where(ApprovalRequest.plan_id.in_(plan_ids))))
            approval_ids = [a.id for a in approvals]
            records = list(db.scalars(select(ServiceNowRecord).where(ServiceNowRecord.plan_id.in_(plan_ids))))
            record_ids = [r.id for r in records]
            executions = list(db.scalars(select(AgentExecution).where(AgentExecution.workflow_run_id == run_id)))
            exec_ids = [e.id for e in executions]
            shift([run], ["started_at", "updated_at", "completed_at"], delta)
            shift(executions, ["started_at", "completed_at"], delta)
            shift(db.scalars(select(WorkflowEvent).where(WorkflowEvent.workflow_run_id == run_id)), ["created_at"], delta)
            shift(db.scalars(select(ToolCall).where(ToolCall.agent_execution_id.in_(exec_ids))), ["created_at"], delta)
            shift(db.scalars(select(RiskAssessment).where(RiskAssessment.workflow_run_id == run_id)), ["calculated_at"], delta)
            shift(plans, ["created_at", "updated_at"], delta)
            shift(approvals, ["created_at"], delta)
            shift(approvals, ["decided_at"], delta - timedelta(hours=20))  # decided ~20h after request
            shift(
                db.scalars(select(ApprovalDecision).where(ApprovalDecision.approval_request_id.in_(approval_ids))),
                ["created_at"],
                delta - timedelta(hours=20),
            )
            shift(records, ["created_at", "updated_at", "last_sync_at"], delta - timedelta(hours=22))
            shift(
                db.scalars(select(ServiceNowSyncAttempt).where(ServiceNowSyncAttempt.record_id.in_(record_ids))),
                ["created_at"],
                delta - timedelta(hours=22),
            )
            shift(
                db.scalars(
                    select(ScanEvidence).where(ScanEvidence.finding_id == run.finding_id, ScanEvidence.kind != "baseline")
                ),
                ["scanned_at", "created_at"],
                delta - timedelta(days=4),
            )
            finding = db.get(Finding, run.finding_id)
            if finding is not None and finding.remediated_at is not None:
                finding.remediated_at -= delta - timedelta(days=4)
            targets = [run_id, run.finding_id, *plan_ids, *approval_ids, *record_ids]
            shift(db.scalars(select(AuditEvent).where(AuditEvent.target_id.in_(targets))), ["created_at"], delta)


def seed_all(with_history: bool = True) -> dict[str, Any]:
    with session_scope() as db:
        users = seed_users(db)
    seed_servicenow_cmdb()
    with session_scope() as db:
        stats: dict[str, Any] = dict(sync_cmdb(db, actor="seed"))
    with session_scope() as db:
        seed_defender(db)
    with session_scope() as db:
        if not db.scalar(select(func.count()).select_from(Finding)):
            report = ingest_findings(db, MockDefenderAdapter(db).list_findings(), submitted_by="seed")
            stats |= {
                "findings_created": report.created,
                "invalid": report.invalid,
                "ambiguous": report.ambiguous_assets,
                "unmatched": report.unmatched_assets,
            }
    if with_history:
        with session_scope() as db:
            users = {u.email: u for u in db.scalars(select(User))}
            for u in users.values():
                db.expunge(u)
        seed_history(users)
    with session_scope() as db:
        stats |= {
            "findings": db.scalar(select(func.count()).select_from(Finding)),
            "plans": db.scalar(select(func.count()).select_from(RemediationPlan)),
            "approvals": db.scalar(select(func.count()).select_from(ApprovalRequest)),
            "servicenow_records": db.scalar(select(func.count()).select_from(ServiceNowRecord)),
            "workflow_runs": db.scalar(select(func.count()).select_from(WorkflowRun)),
        }
    log.info("seed complete", extra={"stats": stats})
    return stats


def main() -> None:
    from app.observability.logging import configure_logging

    parser = argparse.ArgumentParser(description="Seed the AegisRemediate simulated enterprise")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first (destroys data)")
    parser.add_argument("--no-history", action="store_true", help="skip seeded historical investigations")
    parser.add_argument("--create-tables", action="store_true", help="create tables without Alembic (SQLite dev only)")
    args = parser.parse_args()
    configure_logging(get_settings().log_level, json_logs=False)
    import app.models  # noqa: F401

    if args.reset:
        if get_settings().app_env == "production":
            raise SystemExit("--reset is disabled in production")
        Base.metadata.drop_all(get_engine())
        args.create_tables = True
    if args.create_tables:
        Base.metadata.create_all(get_engine())
    stats = seed_all(with_history=not args.no_history)
    print("Seed complete:", stats)


if __name__ == "__main__":
    main()
