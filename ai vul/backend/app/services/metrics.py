"""Dashboard and analytics metrics. Every number is computed from persisted data, with a definition."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
from statistics import mean
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.types import utcnow
from app.models.enterprise import Asset, BusinessService
from app.models.remediation import ApprovalRequest, RemediationPlan
from app.models.servicenow import ServiceNowRecord
from app.models.vulnerability import Finding, Vulnerability
from app.models.workflow import AgentExecution, ToolCall, WorkflowRun

OPEN = ("open", "in_remediation")


def _week(dt: Any) -> str:
    start = dt - timedelta(days=dt.weekday())
    return start.strftime("%Y-%m-%d")


def dashboard(db: Session) -> dict[str, Any]:
    findings = list(db.scalars(select(Finding)))
    open_f = [f for f in findings if f.status in OPEN]
    now = utcnow()
    kpis = {
        "open_findings": len(open_f),
        "open_vulnerabilities": len({f.vulnerability_id for f in open_f}),
        "critical_findings": sum(1 for f in open_f if f.risk_level == "critical"),
        "high_risk_assets": len({f.asset_id for f in open_f if f.asset_id and f.risk_level in ("critical", "high")}),
        "known_exploited_findings": sum(1 for f in open_f if f.vulnerability.kev),
        "known_exploited_cves": len({f.vulnerability_id for f in open_f if f.vulnerability.kev}),
        "pending_approvals": db.scalar(
            select(func.count()).select_from(ApprovalRequest).where(ApprovalRequest.state == "PENDING")
        )
        or 0,
        "plans_in_progress": db.scalar(
            select(func.count())
            .select_from(RemediationPlan)
            .join(Finding, RemediationPlan.finding_id == Finding.id)
            .where(RemediationPlan.status == "APPROVED", Finding.verification_state != "verified_remediated")
        )
        or 0,
        "verified_remediations": sum(1 for f in findings if f.verification_state == "verified_remediated"),
        "sync_failures": db.scalar(
            select(func.count()).select_from(ServiceNowRecord).where(ServiceNowRecord.sync_state == "SYNC_FAILED")
        )
        or 0,
        "unresolved_asset_matches": sum(1 for f in open_f if f.correlation_status != "matched"),
    }
    sev_order = ["critical", "high", "medium", "low", "none", "unknown"]
    sev = Counter(f.vulnerability.severity for f in open_f)
    buckets = Counter(min((f.risk_score or 0) // 10, 9) for f in open_f if f.risk_score is not None)
    weeks = [_week(now - timedelta(weeks=i)) for i in range(11, -1, -1)]
    disc = Counter(_week(f.first_seen_at) for f in findings)
    rem = Counter(_week(f.remediated_at) for f in findings if f.remediated_at)
    by_service: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "critical": 0, "high": 0})
    for f in open_f:
        name = f.asset.business_service.name if f.asset and f.asset.business_service else "Unmapped / endpoints"
        by_service[name]["total"] += 1
        if f.risk_level in ("critical", "high"):
            by_service[name][f.risk_level] += 1
    sla: dict[str, dict[str, int]] = {p: {"overdue": 0, "due_7d": 0, "within_sla": 0} for p in ("P1", "P2", "P3", "P4")}
    for f in open_f:
        if not f.priority or not f.sla_due_at:
            continue
        bucket = "overdue" if f.sla_due_at < now else "due_7d" if f.sla_due_at < now + timedelta(days=7) else "within_sla"
        sla[f.priority][bucket] += 1
    top = sorted(open_f, key=lambda f: f.risk_score or 0, reverse=True)[:8]
    return {
        "kpis": kpis,
        "by_severity": [{"severity": s, "count": sev.get(s, 0)} for s in sev_order if sev.get(s)],
        "risk_distribution": [
            {"bucket": f"{b * 10}-{b * 10 + 9 if b < 9 else 100}", "count": buckets.get(b, 0)} for b in range(10)
        ],
        "discovery_trend": [{"week": w, "discovered": disc.get(w, 0), "remediated": rem.get(w, 0)} for w in weeks],
        "by_business_service": sorted(({"service": k, **v} for k, v in by_service.items()), key=lambda r: -r["total"]),
        "sla_exposure": [{"priority": p, **v} for p, v in sla.items()],
        "top_risks": [
            {
                "finding_id": f.id,
                "cve_id": f.vulnerability.cve_id,
                "hostname": f.asset.hostname if f.asset else f.reported_asset_identifier,
                "risk_score": f.risk_score,
                "risk_level": f.risk_level,
                "kev": f.vulnerability.kev,
                "business_service": f.asset.business_service.name if f.asset and f.asset.business_service else None,
            }
            for f in top
        ],
        "generated_at": now.isoformat(),
    }


def _hours(values: list[float]) -> float | None:
    return round(mean(values), 2) if values else None


def analytics(db: Session) -> dict[str, Any]:
    runs = list(db.scalars(select(WorkflowRun)))
    now = utcnow()
    investigation_hours = []
    for r in runs:
        done = db.scalar(
            select(AgentExecution.completed_at)
            .where(
                AgentExecution.workflow_run_id == r.id,
                AgentExecution.node_name == "validate_evidence",
                AgentExecution.status == "completed",
            )
            .order_by(AgentExecution.completed_at)
        )
        if done:
            investigation_hours.append((done - r.started_at).total_seconds() / 3600)
    findings = list(db.scalars(select(Finding)))
    mttr = [(f.remediated_at - f.first_seen_at).total_seconds() / 86400 for f in findings if f.remediated_at]
    decided = list(db.scalars(select(ApprovalRequest).where(ApprovalRequest.decided_at.is_not(None))))
    turnaround = [(a.decided_at - a.created_at).total_seconds() / 3600 for a in decided if a.decided_at]
    finished = [r for r in runs if r.status not in ("queued", "running")]
    succeeded = [r for r in finished if r.plan_id and r.status != "failed"]
    approved_plans = list(db.scalars(select(RemediationPlan).where(RemediationPlan.status == "APPROVED")))
    approved_findings = {p.finding_id for p in approved_plans}
    verified = {f.id for f in findings if f.verification_state == "verified_remediated"}
    tool_total = db.scalar(select(func.count()).select_from(ToolCall)) or 0
    tool_errors = db.scalar(select(func.count()).select_from(ToolCall).where(ToolCall.status == "error")) or 0
    tool_denied = db.scalar(select(func.count()).select_from(ToolCall).where(ToolCall.status == "denied")) or 0
    by_provider: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"runs": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "cost_known": True}
    )
    for r in runs:
        p = by_provider[f"{r.provider}/{r.model or '-'}"]
        p["runs"] += 1
        p["prompt_tokens"] += r.prompt_tokens
        p["completion_tokens"] += r.completion_tokens
        if r.estimated_cost_usd is None:
            p["cost_known"] = False
        else:
            p["cost_usd"] = round(p["cost_usd"] + r.estimated_cost_usd, 6)
    backlog = Counter(f.priority for f in findings if f.status in OPEN)
    weeks = [now - timedelta(weeks=i) for i in range(11, -1, -1)]
    exposure = []
    for w in weeks:
        count = sum(
            1
            for f in findings
            if f.risk_level == "critical" and f.first_seen_at <= w and (f.remediated_at is None or f.remediated_at > w)
        )
        exposure.append({"week": _week(w), "open_critical": count})
    agent_stats = db.execute(
        select(AgentExecution.agent_name, AgentExecution.status, func.count(), func.avg(AgentExecution.latency_ms)).group_by(
            AgentExecution.agent_name, AgentExecution.status
        )
    ).all()
    agents: dict[str, dict[str, Any]] = defaultdict(lambda: {"completed": 0, "failed": 0, "avg_latency_ms": None})
    for name, status, count, avg_latency in agent_stats:
        agents[name][status] = count
        if status == "completed":
            agents[name]["avg_latency_ms"] = round(avg_latency or 0)

    def metric(value: Any, unit: str, definition: str, n: int | None = None) -> dict[str, Any]:
        return {"value": value, "unit": unit, "definition": definition, "sample_size": n}

    return {
        "metrics": {
            "mean_investigation_duration": metric(
                _hours(investigation_hours),
                "hours",
                "Mean time from investigation start to completed evidence validation (plan ready for approval).",
                len(investigation_hours),
            ),
            "mean_time_to_remediation": metric(
                round(mean(mttr), 1) if mttr else None,
                "days",
                "Mean time from first detection to scanner-verified remediation (verified findings only).",
                len(mttr),
            ),
            "remediation_backlog": metric(sum(backlog.values()), "findings", "Open or in-remediation findings.", None),
            "approval_turnaround": metric(
                _hours(turnaround), "hours", "Mean time from approval request to decision.", len(turnaround)
            ),
            "investigation_success_rate": metric(
                round(len(succeeded) / len(finished), 3) if finished else None,
                "ratio",
                "Finished investigations that produced a validated remediation plan / finished investigations.",
                len(finished),
            ),
            "verification_completion_rate": metric(
                round(len(approved_findings & verified) / len(approved_findings), 3) if approved_findings else None,
                "ratio",
                "Findings with an approved plan that are verified remediated by fresh scan evidence.",
                len(approved_findings),
            ),
            "agent_cost": metric(
                round(sum(p["cost_usd"] for p in by_provider.values()), 6),
                "USD",
                "Sum of estimated model cost (only where pricing is configured; mock provider costs 0).",
                len(runs),
            ),
            "tool_failure_rate": metric(
                round(tool_errors / tool_total, 4) if tool_total else None,
                "ratio",
                "Tool calls ending in error / all tool calls (denied calls reported separately).",
                tool_total,
            ),
            "tool_denials": metric(tool_denied, "calls", "Tool calls blocked by allowlists or permissions.", tool_total),
        },
        "backlog_by_priority": [{"priority": p, "count": backlog.get(p, 0)} for p in ("P1", "P2", "P3", "P4")],
        "critical_exposure_trend": exposure,
        "cost_by_provider": [{"provider_model": k, **v} for k, v in by_provider.items()],
        "agent_performance": [{"agent": k, **v} for k, v in sorted(agents.items())],
        "assets_total": db.scalar(select(func.count()).select_from(Asset)) or 0,
        "services_total": db.scalar(select(func.count()).select_from(BusinessService)) or 0,
        "vulnerabilities_total": db.scalar(select(func.count()).select_from(Vulnerability)) or 0,
        "generated_at": now.isoformat(),
    }
