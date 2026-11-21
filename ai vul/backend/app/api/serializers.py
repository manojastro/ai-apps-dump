"""Response serialisers (explicit field lists - nothing sensitive leaks by accident)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.approvals.state_machine import lifecycle_stage
from app.models.enterprise import Asset, BusinessService
from app.models.remediation import ApprovalRequest, RemediationPlan, RiskAssessment
from app.models.servicenow import ServiceNowRecord
from app.models.vulnerability import Finding, ScanEvidence, Vulnerability
from app.models.workflow import AgentExecution, ToolCall, WorkflowEvent, WorkflowRun
from app.services.servicenow_sync import state_label


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def vulnerability(v: Vulnerability) -> dict[str, Any]:
    return {
        "id": v.id,
        "cve_id": v.cve_id,
        "title": v.title,
        "description": v.description,
        "severity": v.severity,
        "cvss_score": v.cvss_score,
        "cvss_vector": v.cvss_vector,
        "cvss_version": v.cvss_version,
        "cwes": v.cwes,
        "published_at": iso(v.published_at),
        "epss_score": v.epss_score,
        "epss_percentile": v.epss_percentile,
        "epss_date": v.epss_date,
        "kev": v.kev,
        "kev_date_added": v.kev_date_added,
        "kev_due_date": v.kev_due_date,
        "kev_ransomware_use": v.kev_ransomware_use,
        "kev_required_action": v.kev_required_action,
        "affected_vendor": v.affected_vendor,
        "affected_product": v.affected_product,
        "references": v.references,
        "source": v.source,
        "evidence_status": v.evidence_status,
        "intel_sources": v.intel_sources,
        "first_detected_at": iso(v.first_detected_at),
        "last_detected_at": iso(v.last_detected_at),
        "intel_updated_at": iso(v.intel_updated_at),
    }


def service(s: BusinessService | None) -> dict[str, Any] | None:
    if s is None:
        return None
    return {
        "id": s.id,
        "name": s.name,
        "division": s.division,
        "criticality": s.criticality,
        "owner_team": s.owner_team,
        "description": s.description,
        "cmdb_sys_id": s.cmdb_sys_id,
    }


def asset(a: Asset | None) -> dict[str, Any] | None:
    if a is None:
        return None
    return {
        "id": a.id,
        "hostname": a.hostname,
        "fqdn": a.fqdn,
        "ip_address": a.ip_address,
        "asset_type": a.asset_type,
        "operating_system": a.operating_system,
        "os_version": a.os_version,
        "environment": a.environment,
        "business_criticality": a.business_criticality,
        "business_service": service(a.business_service),
        "owner": a.owner,
        "support_group": a.support_group,
        "internet_exposed": a.internet_exposed,
        "cloud_provider": a.cloud_provider,
        "location": a.location,
        "operational_status": a.operational_status,
        "cmdb_sys_id": a.cmdb_sys_id,
        "defender_device_id": a.defender_device_id,
        "last_sync_at": iso(a.last_sync_at),
    }


def finding_row(f: Finding) -> dict[str, Any]:
    v, a = f.vulnerability, f.asset
    return {
        "id": f.id,
        "cve_id": v.cve_id,
        "severity": v.severity,
        "cvss_score": v.cvss_score,
        "epss_score": v.epss_score,
        "kev": v.kev,
        "risk_score": f.risk_score,
        "risk_level": f.risk_level,
        "priority": f.priority,
        "asset_id": f.asset_id,
        "hostname": a.hostname if a else f.reported_asset_identifier,
        "environment": a.environment if a else None,
        "business_service": a.business_service.name if a and a.business_service else None,
        "software": f.software_name,
        "software_version": f.software_version,
        "scanner": f.scanner,
        "status": f.status,
        "verification_state": f.verification_state,
        "correlation_status": f.correlation_status,
        "sla_due_at": iso(f.sla_due_at),
        "first_seen_at": iso(f.first_seen_at),
        "last_seen_at": iso(f.last_seen_at),
    }


def risk_assessment(r: RiskAssessment | None) -> dict[str, Any] | None:
    if r is None:
        return None
    return {
        "id": r.id,
        "score": r.score,
        "score_lower": r.score_lower,
        "score_upper": r.score_upper,
        "risk_level": r.risk_level,
        "priority": r.priority,
        "business_impact": r.business_impact,
        "coverage": r.coverage,
        "policy_version": r.policy_version,
        "factors": r.factors,
        "missing_factors": r.missing_factors,
        "requires_immediate_review": r.requires_immediate_review,
        "rationale": r.rationale,
        "calculated_at": iso(r.calculated_at),
        "workflow_run_id": r.workflow_run_id,
    }


def sn_record(r: ServiceNowRecord) -> dict[str, Any]:
    return {
        "id": r.id,
        "plan_id": r.plan_id,
        "approval_request_id": r.approval_request_id,
        "mode": r.mode,
        "instance": r.instance,
        "table_name": r.table_name,
        "sys_id": r.sys_id,
        "number": r.number,
        "record_url": r.record_url,
        "sync_state": r.sync_state,
        "external_state": r.external_state,
        "external_state_label": state_label(r),
        "external_close_code": r.external_close_code,
        "attempts": r.attempts,
        "last_error": r.last_error,
        "last_sync_at": iso(r.last_sync_at),
        "created_at": iso(r.created_at),
        "parent_record_id": r.parent_record_id,
        "payload": r.payload,
    }


def approval(r: ApprovalRequest, db: Session | None = None) -> dict[str, Any]:
    from app.models.identity import User

    def name(uid: str | None) -> str | None:
        if not uid or db is None:
            return None
        u = db.get(User, uid)
        return u.full_name if u else None

    return {
        "id": r.id,
        "plan_id": r.plan_id,
        "state": r.state,
        "risk_level": r.risk_level,
        "requested_by": r.requested_by,
        "requested_by_name": name(r.requested_by),
        "assigned_approver_id": r.assigned_approver_id,
        "assigned_approver_name": name(r.assigned_approver_id),
        "decided_by": r.decided_by,
        "decided_by_name": name(r.decided_by),
        "decided_at": iso(r.decided_at),
        "decision_comment": r.decision_comment,
        "request_comment": r.request_comment,
        "payload_hash": r.payload_hash,
        "payload_snapshot": r.payload_snapshot,
        "policy_version": r.policy_version,
        "separation_of_duties": r.separation_of_duties,
        "created_at": iso(r.created_at),
        "decisions": [
            {
                "id": d.id,
                "actor_id": d.actor_id,
                "actor_name": name(d.actor_id),
                "decision": d.decision,
                "outcome": d.outcome,
                "comment": d.comment,
                "reason": d.reason,
                "created_at": iso(d.created_at),
            }
            for d in r.decisions
        ],
    }


def plan(p: RemediationPlan, db: Session, full: bool = True) -> dict[str, Any]:
    finding = db.get(Finding, p.finding_id)
    change = db.scalar(
        select(ServiceNowRecord)
        .where(ServiceNowRecord.plan_id == p.id, ServiceNowRecord.parent_record_id.is_(None))
        .order_by(ServiceNowRecord.created_at.desc())
    )
    stage = lifecycle_stage(
        p.status,
        p.remediation_state,
        change.sync_state if change else None,
        finding.verification_state if finding else "not_started",
        finding.status if finding else "open",
    )
    latest_approval = db.scalar(
        select(ApprovalRequest).where(ApprovalRequest.plan_id == p.id).order_by(ApprovalRequest.created_at.desc())
    )
    out: dict[str, Any] = {
        "id": p.id,
        "finding_id": p.finding_id,
        "workflow_run_id": p.workflow_run_id,
        "revision": p.revision,
        "status": p.status,
        "remediation_state": p.remediation_state,
        "lifecycle_stage": stage,
        "title": p.title,
        "summary": p.summary,
        "target_version": p.target_version,
        "requires_expert_validation": p.requires_expert_validation,
        "generated_by": p.generated_by,
        "created_at": iso(p.created_at),
        "updated_at": iso(p.updated_at),
        "cve_id": finding.vulnerability.cve_id if finding else None,
        "hostname": (
            finding.asset.hostname if finding and finding.asset else finding.reported_asset_identifier if finding else None
        ),
        "business_service": (
            finding.asset.business_service.name if finding and finding.asset and finding.asset.business_service else None
        ),
        "risk_score": finding.risk_score if finding else None,
        "risk_level": finding.risk_level if finding else None,
        "priority": finding.priority if finding else None,
        "approval_state": latest_approval.state if latest_approval else None,
        "approval_request_id": latest_approval.id if latest_approval else None,
        "servicenow_number": change.number if change else None,
        "sync_state": change.sync_state if change else None,
    }
    if full:
        out |= {
            "recommended_action": p.recommended_action,
            "prerequisites": p.prerequisites,
            "implementation_steps": p.implementation_steps,
            "verification_steps": p.verification_steps,
            "rollback_steps": p.rollback_steps,
            "testing_requirements": p.testing_requirements,
            "expected_impact": p.expected_impact,
            "maintenance_window": p.maintenance_window,
            "required_approvers": p.required_approvers,
            "evidence_refs": p.evidence_refs,
            "assumptions": p.assumptions,
            "change_impact": p.change_impact,
            "validation": p.validation,
            "content_hash": p.content_hash,
            "created_by": p.created_by,
            "edited_by": p.edited_by,
        }
    return out


def evidence(e: ScanEvidence) -> dict[str, Any]:
    return {
        "id": e.id,
        "finding_id": e.finding_id,
        "asset_identifier": e.asset_identifier,
        "device_id": e.device_id,
        "cve_id": e.cve_id,
        "scanner": e.scanner,
        "scan_id": e.scan_id,
        "scanned_at": iso(e.scanned_at),
        "vulnerable": e.vulnerable,
        "software_name": e.software_name,
        "software_version": e.software_version,
        "kind": e.kind,
        "raw": e.raw,
        "submitted_by": e.submitted_by,
        "created_at": iso(e.created_at),
    }


def workflow_run(r: WorkflowRun, db: Session) -> dict[str, Any]:
    f = db.get(Finding, r.finding_id)
    return {
        "id": r.id,
        "kind": r.kind,
        "finding_id": r.finding_id,
        "status": r.status,
        "current_node": r.current_node,
        "waiting_reason": r.waiting_reason,
        "plan_id": r.plan_id,
        "provider": r.provider,
        "model": r.model,
        "prompt_tokens": r.prompt_tokens,
        "completion_tokens": r.completion_tokens,
        "estimated_cost_usd": r.estimated_cost_usd,
        "error": r.error,
        "resume_count": r.resume_count,
        "summary": r.summary,
        "started_by": r.started_by,
        "started_at": iso(r.started_at),
        "updated_at": iso(r.updated_at),
        "completed_at": iso(r.completed_at),
        "cve_id": f.vulnerability.cve_id if f else None,
        "hostname": (f.asset.hostname if f and f.asset else f.reported_asset_identifier if f else None),
        "risk_score": f.risk_score if f else None,
        "risk_level": f.risk_level if f else None,
    }


def agent_execution(e: AgentExecution) -> dict[str, Any]:
    return {
        "id": e.id,
        "agent_name": e.agent_name,
        "node_name": e.node_name,
        "status": e.status,
        "attempt": e.attempt,
        "input_summary": e.input_summary,
        "output": e.output,
        "error": e.error,
        "validation_errors": e.validation_errors,
        "model_provider": e.model_provider,
        "model_name": e.model_name,
        "prompt_tokens": e.prompt_tokens,
        "completion_tokens": e.completion_tokens,
        "estimated_cost_usd": e.estimated_cost_usd,
        "latency_ms": e.latency_ms,
        "started_at": iso(e.started_at),
        "completed_at": iso(e.completed_at),
    }


def tool_call(t: ToolCall) -> dict[str, Any]:
    return {
        "id": t.id,
        "agent_execution_id": t.agent_execution_id,
        "caller": t.caller,
        "tool_name": t.tool_name,
        "mutating": t.mutating,
        "arguments": t.arguments,
        "result_summary": t.result_summary,
        "status": t.status,
        "error": t.error,
        "latency_ms": t.latency_ms,
        "created_at": iso(t.created_at),
    }


def event(e: WorkflowEvent) -> dict[str, Any]:
    return {
        "id": e.id,
        "event_type": e.event_type,
        "node": e.node,
        "message": e.message,
        "payload": e.payload,
        "created_at": iso(e.created_at),
    }
