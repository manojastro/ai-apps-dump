"""Agent 7 (ServiceNow Orchestration) and Agent 8 (Remediation Verification)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.agents.base import Agent, AgentContext
from app.core.types import utcnow
from app.models.enums import FindingStatus, RemediationState, VerificationState
from app.models.remediation import RemediationPlan
from app.models.servicenow import ServiceNowRecord
from app.models.vulnerability import Finding, ScanEvidence
from app.security.auth import SYSTEM_PRINCIPAL
from app.services.audit import record_audit
from app.services.servicenow_sync import ServiceNowSyncService, state_label


class OrchestrationOutput(BaseModel):
    status: str  # synced | failed | denied
    approval_request_id: str
    records: list[dict[str, Any]] = Field(default_factory=list)
    gate_reasons: list[str] = Field(default_factory=list)
    error: str | None = None


class ServiceNowOrchestrationAgent(Agent):
    name = "ServiceNow Orchestration Agent"
    node = "sync_servicenow"
    description = "Proposes the approved change to ServiceNow through the deterministic write gate and idempotent sync service."
    tools = {"servicenow_search_records"}
    boundary = (
        "Cannot call ServiceNow write APIs directly. Writes happen only inside ServiceNowSyncService after "
        "authorize_write() re-validates the human approval from the database."
    )
    evaluation = ["no write without approval", "no duplicate records on retry", "failures surfaced"]
    Output = OrchestrationOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> OrchestrationOutput:
        approval_id = state["approval_request_id"]
        ctx.db.commit()  # release locks before the sync service performs remote I/O
        outcome = ServiceNowSyncService(ctx.db).sync_approved_plan(approval_id, SYSTEM_PRINCIPAL)
        records = [
            {
                "id": r.id,
                "table": r.table_name,
                "number": r.number,
                "sys_id": r.sys_id,
                "sync_state": r.sync_state,
                "attempts": r.attempts,
                "record_url": r.record_url,
                "mode": r.mode,
            }
            for r in outcome.records
        ]
        status = "synced" if outcome.ok else "denied" if outcome.gate_reasons else "failed"
        if outcome.ok:
            ctx.event("servicenow_synced", "ServiceNow records created/reconciled", {"records": [r["number"] for r in records]})
        return OrchestrationOutput(
            status=status,
            approval_request_id=approval_id,
            records=records,
            gate_reasons=outcome.gate_reasons,
            error=outcome.error,
        )


class VerificationOutput(BaseModel):
    verification_state: str
    finding_id: str
    baseline: dict[str, Any] | None
    latest_evidence: dict[str, Any] | None
    checks: dict[str, bool | None]
    servicenow_state: str | None
    explanation: list[str]


def _ev(e: ScanEvidence | None) -> dict[str, Any] | None:
    if e is None:
        return None
    return {
        "id": e.id,
        "scan_id": e.scan_id,
        "scanner": e.scanner,
        "scanned_at": e.scanned_at.isoformat(),
        "vulnerable": e.vulnerable,
        "asset_identifier": e.asset_identifier,
        "device_id": e.device_id,
        "software": e.software_name,
        "version": e.software_version,
        "kind": e.kind,
    }


def evaluate_verification(db: Any, finding: Finding, plan: RemediationPlan | None) -> VerificationOutput:
    """Evidence-based verification. A closed ServiceNow task alone NEVER verifies remediation."""
    explanation: list[str] = []
    baseline = db.scalar(
        select(ScanEvidence)
        .where(ScanEvidence.finding_id == finding.id, ScanEvidence.kind == "baseline")
        .order_by(ScanEvidence.scanned_at.desc())
    )
    change = None
    if plan is not None:
        change = db.scalar(
            select(ServiceNowRecord).where(ServiceNowRecord.plan_id == plan.id, ServiceNowRecord.parent_record_id.is_(None))
        )
    anchor = (change.created_at if change else None) or (baseline.scanned_at if baseline else finding.detected_at)
    latest = db.scalar(
        select(ScanEvidence)
        .where(ScanEvidence.finding_id == finding.id, ScanEvidence.kind != "baseline")
        .order_by(ScanEvidence.scanned_at.desc())
    )
    sn_state = state_label(change) if change else None
    if change and change.external_state == "3":
        explanation.append(f"ServiceNow change {change.number} is closed - this alone does not verify remediation")

    checks: dict[str, bool | None] = {
        "fresh_evidence": None,
        "asset_identity_matches": None,
        "scan_after_change": None,
        "vulnerability_absent": None,
    }
    if latest is None:
        explanation.append("No post-remediation scan evidence yet; awaiting rescan")
        return VerificationOutput(
            verification_state=VerificationState.PENDING_RESCAN,
            finding_id=finding.id,
            baseline=_ev(baseline),
            latest_evidence=None,
            checks=checks,
            servicenow_state=sn_state,
            explanation=explanation,
        )
    checks["fresh_evidence"] = True
    ident_ok = (
        finding.reported_device_id and latest.device_id == finding.reported_device_id
    ) or latest.asset_identifier.lower() in {
        finding.reported_asset_identifier.lower(),
        (finding.asset.hostname if finding.asset else "").lower(),
        (finding.asset.fqdn or "" if finding.asset else "").lower(),
    }
    checks["asset_identity_matches"] = bool(ident_ok)
    checks["scan_after_change"] = latest.scanned_at > anchor
    checks["vulnerability_absent"] = not latest.vulnerable
    if not ident_ok:
        explanation.append(f"Evidence is for '{latest.asset_identifier}', which does not match the affected asset")
        state = VerificationState.INCONCLUSIVE
    elif not checks["scan_after_change"]:
        explanation.append("Scan predates the remediation change; it cannot prove remediation")
        state = VerificationState.INCONCLUSIVE
    elif latest.vulnerable:
        explanation.append(
            f"Rescan {latest.scan_id} still detects {finding.vulnerability.cve_id} "
            f"({latest.software_name} {latest.software_version})"
        )
        state = VerificationState.FAILED
    elif not (latest.raw or {}).get("device_found", True):
        explanation.append("Scanner could not locate the device; absence of the finding is not proof")
        state = VerificationState.INCONCLUSIVE
    else:
        explanation.append(
            f"Rescan {latest.scan_id} at {latest.scanned_at.isoformat()} no longer detects "
            f"{finding.vulnerability.cve_id}; installed version {latest.software_version or 'n/a'}"
        )
        state = VerificationState.VERIFIED_REMEDIATED
    return VerificationOutput(
        verification_state=state,
        finding_id=finding.id,
        baseline=_ev(baseline),
        latest_evidence=_ev(latest),
        checks=checks,
        servicenow_state=sn_state,
        explanation=explanation,
    )


class RemediationVerificationAgent(Agent):
    name = "Remediation Verification Agent"
    node = "verify_remediation"
    description = "Compares before/after scan evidence for the same asset to verify remediation."
    tools = {"defender_get_vulnerabilities"}
    boundary = "Updates internal verification state only. Never closes records based on ticket status."
    evaluation = ["verified only with fresh matching evidence", "stale or mismatched evidence -> inconclusive"]
    Output = VerificationOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> VerificationOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        plan = ctx.db.get(RemediationPlan, state["plan_id"]) if state.get("plan_id") else None
        assert finding is not None
        result = evaluate_verification(ctx.db, finding, plan)
        previous = finding.verification_state
        finding.verification_state = result.verification_state
        if result.verification_state == VerificationState.VERIFIED_REMEDIATED:
            finding.status = FindingStatus.REMEDIATED
            finding.remediated_at = utcnow()
            if plan is not None:
                plan.remediation_state = RemediationState.IMPLEMENTED
        elif result.verification_state == VerificationState.FAILED and plan is not None:
            if plan.remediation_state == RemediationState.IMPLEMENTED:
                plan.remediation_state = RemediationState.REMEDIATION_IN_PROGRESS
        record_audit(
            ctx.db,
            actor=SYSTEM_PRINCIPAL,
            action="verification_evaluated",
            target_type="finding",
            target_id=finding.id,
            previous_state={"verification_state": previous},
            new_state={"verification_state": finding.verification_state},
            details={"checks": result.checks, "evidence": (result.latest_evidence or {}).get("scan_id")},
        )
        return result
