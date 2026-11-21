"""Agent 5: Remediation Planning. Produces a *proposal*; never executes anything."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.agents.base import Agent, AgentContext
from app.approvals.service import compute_plan_hash
from app.core.versions import match_cpe_ranges
from app.llm.base import StructuredTask, untrusted
from app.models.enums import PlanStatus
from app.models.remediation import RemediationPlan, RiskAssessment
from app.models.vulnerability import Finding


class PlanStep(BaseModel):
    step: str = Field(max_length=600)
    evidence_refs: list[str] = Field(default_factory=list)


class RemediationPlanDraft(BaseModel):
    title: str = Field(max_length=200)
    summary: str = Field(max_length=2000)
    recommended_action: str = Field(max_length=1500)
    target_version: str | None = Field(default=None, max_length=64, description="Only a version present in the evidence")
    prerequisites: list[str] = Field(default_factory=list, max_length=12)
    implementation_steps: list[PlanStep] = Field(min_length=1, max_length=15)
    verification_steps: list[str] = Field(min_length=1, max_length=10)
    rollback_steps: list[str] = Field(min_length=1, max_length=10)
    testing_requirements: list[str] = Field(default_factory=list, max_length=10)
    expected_impact: str = Field(max_length=1500)
    maintenance_window: str = Field(max_length=500)
    required_approver_roles: list[str] = Field(default_factory=list, max_length=6)
    evidence_refs: list[str] = Field(default_factory=list)
    requires_expert_validation: bool
    assumptions: list[str] = Field(default_factory=list, max_length=10)


class PlanningOutput(BaseModel):
    plan_id: str
    revision: int
    title: str
    target_version: str | None
    requires_expert_validation: bool
    evidence_count: int
    generated_by: str


SYSTEM_PROMPT = """You are the Remediation Planning Agent of AegisRemediate AI, an enterprise vulnerability
remediation platform. Produce a remediation PROPOSAL for a human change approver.

Hard rules:
- Use only facts present in the evidence items (E1, E2, ...). Cite them in evidence_refs.
- Never invent patch versions, vendor advisories, KB numbers, commands or downtime estimates.
- target_version must be null unless a fixed version appears verbatim in the evidence.
- If the fix, compatibility or rollback cannot be confirmed from evidence, set requires_expert_validation=true.
- Rollback steps are proposals for the service owner to validate, never claimed as tested.
- Do not propose disabling security controls, firewall changes, or running scripts from the internet.
- You cannot execute anything; you only write the plan."""


def build_evidence(ctx: AgentContext, finding: Finding, state: dict[str, Any]) -> list[dict[str, Any]]:
    vuln, asset = finding.vulnerability, finding.asset
    ev: list[dict[str, Any]] = []

    def add(kind: str, title: str, content: Any, source: str, reference: str | None = None) -> str:
        eid = f"E{len(ev) + 1}"
        ev.append({"id": eid, "type": kind, "title": title, "content": content, "source": source, "reference": reference})
        return eid

    nvd_ref = (vuln.intel_sources or {}).get("nvd", {}).get("reference", vuln.source)
    if vuln.description:
        add(
            "vulnerability",
            f"{vuln.cve_id} description",
            vuln.description,
            nvd_ref if vuln.evidence_status == "verified" else "scanner (unverified)",
            f"https://nvd.nist.gov/vuln/detail/{vuln.cve_id}",
        )
    if vuln.cvss_score is not None:
        add(
            "severity",
            "CVSS base score",
            f"CVSS {vuln.cvss_version} {vuln.cvss_score} ({vuln.severity}) {vuln.cvss_vector}",
            nvd_ref,
        )
    if finding.software_vendor and finding.software_version and vuln.affected_product:
        m = match_cpe_ranges(vuln.affected_ranges or [], finding.software_vendor, vuln.affected_product, finding.software_version)
        if m.matched:
            content = {
                "installed": f"{finding.software_name} {finding.software_version}",
                "match": m.reason,
                "cpe": m.criteria,
                "first_unaffected_version": m.fixed_version,
                "affected_through_inclusive": m.upper_bound_inclusive,
            }
            add("affected_range", "Installed version within NVD affected range", content, nvd_ref)
    if vuln.kev:
        add(
            "kev",
            "CISA KEV listing",
            {
                "date_added": vuln.kev_date_added,
                "due_date": vuln.kev_due_date,
                "required_action": vuln.kev_required_action,
                "ransomware": vuln.kev_ransomware_use,
            },
            (vuln.intel_sources or {}).get("kev", {}).get("reference", "CISA KEV"),
            "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        )
    if vuln.epss_score is not None:
        add(
            "epss",
            "EPSS probability",
            f"{vuln.epss_score:.4f} (percentile {vuln.epss_percentile:.2f}, {vuln.epss_date}); estimate only",
            "FIRST EPSS",
        )
    if asset:
        add(
            "asset",
            "CMDB context",
            {
                "hostname": asset.hostname,
                "environment": asset.environment,
                "criticality": asset.business_criticality,
                "internet_exposed": asset.internet_exposed,
                "service": asset.business_service.name if asset.business_service else None,
                "owner": asset.owner,
                "support_group": asset.support_group,
                "os": asset.operating_system,
            },
            f"CMDB CI {asset.cmdb_sys_id}",
        )
    corr = state.get("asset_context") or {}
    if corr.get("used_by") or corr.get("depends_on"):
        add(
            "dependencies",
            "CMDB relationships",
            {"used_by": corr.get("used_by"), "depends_on": corr.get("depends_on")},
            "CMDB cmdb_rel_ci",
        )
    risk = state.get("risk") or {}
    if risk:
        add(
            "risk",
            "Deterministic risk assessment",
            {k: risk.get(k) for k in ("risk_score", "risk_level", "priority", "coverage", "missing_factors")},
            risk.get("policy_version", "risk engine"),
        )
    vendor_refs = [r for r in (vuln.references or []) if "nvd.nist.gov" not in r][:4]
    if vendor_refs:
        add("references", "Advisory references listed by NVD (not retrieved)", vendor_refs, nvd_ref)
    return ev


def _ev(evidence: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    return next((e for e in evidence if e["type"] == kind), None)


def template_plan(finding: Finding, evidence: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic evidence-grounded plan (used by the mock provider and as a reference)."""
    vuln, asset = finding.vulnerability, finding.asset
    host = asset.hostname if asset else finding.reported_asset_identifier
    product = finding.software_name or vuln.affected_product or "the affected software"
    installed = finding.software_version or "unknown"
    rng = _ev(evidence, "affected_range")
    kev = _ev(evidence, "kev")
    ids = {e["type"]: e["id"] for e in evidence}
    fixed = rng["content"].get("first_unaffected_version") if rng else None
    through = rng["content"].get("affected_through_inclusive") if rng else None
    refs_range = [x for x in [ids.get("affected_range")] if x]
    expert = False
    assumptions: list[str] = []

    if fixed:
        action = (
            f"Upgrade {product} on {host} from {installed} to {fixed} or a later vendor-supported release "
            f"({fixed} is the first version outside the NVD affected range [{ids['affected_range']}])."
        )
    elif through:
        action = (
            f"Upgrade {product} on {host} to a release later than {through}; the evidence does not name the "
            f"first fixed release, so the target version must be confirmed from the vendor advisory."
        )
        expert = True
    else:
        action = (
            f"Apply the vendor-recommended fix for {vuln.cve_id} to {product} on {host}. The collected evidence "
            "does not identify a fixed version; an expert must confirm the remediation from the vendor advisory."
        )
        expert = True
    if kev:
        action += f" CISA required action: {kev['content'].get('required_action')} [{kev['id']}]"
    if vuln.evidence_status != "verified":
        expert = True
        assumptions.append("Vulnerability details are scanner-provided and not verified against NVD")
    assumptions.append("Rollback steps are proposals and have not been tested; the service owner must validate them")
    if not asset or not asset.owner:
        assumptions.append("Asset owner is not recorded in the CMDB; change approver must assign an implementer")

    is_prod = bool(asset and asset.environment == "production")
    critical = (state.get("risk") or {}).get("risk_level") in ("critical", "high")
    dependents = (state.get("asset_context") or {}).get("used_by") or []
    steps = [
        {
            "step": f"Review the vendor advisory for {vuln.cve_id} and confirm the target release for {product}"
            + (f" (evidence indicates {fixed})" if fixed else ""),
            "evidence_refs": refs_range or [ids.get("vulnerability", "E1")],
        },
        {
            "step": f"Confirm compatibility of the target {product} release with applications hosted on {host} with the service owner",
            "evidence_refs": [x for x in [ids.get("asset")] if x],
        },
        {
            "step": f"Take a snapshot/backup of {host} and record the currently installed version ({installed})",
            "evidence_refs": refs_range,
        },
        {
            "step": f"Within the approved maintenance window, upgrade {product} to the confirmed target release using the "
            "organisation's standard package/deployment process",
            "evidence_refs": refs_range,
        },
        {
            "step": f"Restart dependent services on {host} and monitor application health and error rates",
            "evidence_refs": [x for x in [ids.get("dependencies")] if x],
        },
    ]
    if kev:
        steps.insert(
            0,
            {
                "step": "Follow CISA KEV required action and check for indicators of compromise before patching",
                "evidence_refs": [kev["id"]],
            },
        )
    verification = [
        f"Trigger a Defender rescan of {host} and confirm {vuln.cve_id} is no longer reported",
        f"Confirm the installed {product} version is outside the NVD affected range" + (f" (>= {fixed})" if fixed else ""),
        "Run service health checks and confirm no new errors in application logs",
    ]
    rollback = [
        f"Restore {product} {installed} from the internal artifact repository or restore the pre-change snapshot",
        "Restart affected services and confirm health checks pass",
        "Record the rollback in the change record and keep the vulnerability open for re-planning",
    ]
    testing = ["Validate the upgrade in a non-production environment with the same application stack before production"]
    if dependents:
        testing.append(f"Smoke-test dependent systems: {', '.join(dependents[:6])}")
    impact = (
        f"Possible interruption of {product} on {host} during upgrade/restart"
        + (f"; dependent systems: {', '.join(dependents[:6])}" if dependents else "")
        + ". Downtime duration is not estimated: no historical change data in evidence."
    )
    window = (
        "Expedited change in the next available production maintenance window"
        + (f" (CISA KEV due date {kev['content'].get('due_date')})" if kev else "")
        if is_prod and critical
        else "Standard change in the next scheduled maintenance window"
        if is_prod
        else "Any time agreed with the system owner (non-production)"
    )
    approvers = ["Infrastructure owner" + (f" ({asset.owner})" if asset and asset.owner else " (unassigned)"), "Change approver"]
    if critical:
        approvers.append("Security operations lead")
    return {
        "title": f"Remediate {vuln.cve_id} in {product} on {host}"[:200],
        "summary": (
            f"{vuln.cve_id} ({vuln.severity}, CVSS {vuln.cvss_score}) affects {product} {installed} on {host}. "
            f"Risk is {(state.get('risk') or {}).get('risk_level', 'unassessed')} "
            f"({(state.get('risk') or {}).get('priority', '-')}) under the deterministic policy."
            + (" The CVE is listed in CISA KEV (confirmed exploitation)." if kev else "")
        ),
        "recommended_action": action,
        "target_version": fixed,
        "prerequisites": [
            "Confirm the vendor advisory and supported target version",
            "Approved change request and assigned implementer",
            "Verified backup or snapshot of the asset",
        ]
        + (["Production maintenance window booked"] if is_prod else []),
        "implementation_steps": steps,
        "verification_steps": verification,
        "rollback_steps": rollback,
        "testing_requirements": testing,
        "expected_impact": impact,
        "maintenance_window": window,
        "required_approver_roles": approvers,
        "evidence_refs": [e["id"] for e in evidence],
        "requires_expert_validation": expert,
        "assumptions": assumptions,
    }


class RemediationPlanningAgent(Agent):
    name = "Remediation Planning Agent"
    node = "plan_remediation"
    description = "Builds an evidence-linked remediation proposal with rollback, verification and approval requirements."
    tools = {"threat_get_cve", "asset_get_dependencies"}
    boundary = "Generates a proposal only. Cannot execute, request approval, or write externally."
    uses_llm = True
    evaluation = ["plan completeness", "no unsupported version claims", "valid evidence citations"]
    Output = PlanningOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> PlanningOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        assert finding is not None
        evidence = build_evidence(ctx, finding, state)
        task = StructuredTask(
            name="remediation_plan",
            system=SYSTEM_PROMPT,
            user=(
                "Create the remediation plan for this finding.\n\n"
                f"Finding id: {finding.id}\nAsset: {finding.asset.hostname if finding.asset else finding.reported_asset_identifier}\n\n"
                f"Evidence items:\n{untrusted('evidence', json.dumps(evidence, default=str, indent=1))}"
            ),
            output_model=RemediationPlanDraft,
            mock_response=lambda: template_plan(finding, evidence, state),
            max_output_tokens=2500,
        )
        draft = ctx.llm(task)
        provider = ctx.execution.model_provider or "unknown"
        model = ctx.execution.model_name or ""

        existing = list(ctx.db.scalars(select(RemediationPlan).where(RemediationPlan.workflow_run_id == ctx.run_id)))
        for old in existing:  # retried node: supersede the earlier draft instead of duplicating
            if old.status == PlanStatus.DRAFT:
                old.status = PlanStatus.SUPERSEDED
        ra_id = (state.get("risk") or {}).get("risk_assessment_id")
        prior = ctx.db.scalar(
            select(RemediationPlan).where(RemediationPlan.finding_id == finding.id).order_by(RemediationPlan.revision.desc())
        )
        plan = RemediationPlan(
            finding_id=finding.id,
            workflow_run_id=ctx.run_id,
            risk_assessment_id=ra_id if ra_id and ctx.db.get(RiskAssessment, ra_id) else None,
            revision=(prior.revision + 1) if prior else 1,
            status=PlanStatus.DRAFT,
            title=draft.title,
            summary=draft.summary,
            recommended_action=draft.recommended_action,
            target_version=draft.target_version,
            prerequisites=draft.prerequisites,
            implementation_steps=[s.model_dump() for s in draft.implementation_steps],
            verification_steps=draft.verification_steps,
            rollback_steps=draft.rollback_steps,
            testing_requirements=draft.testing_requirements,
            expected_impact=draft.expected_impact,
            maintenance_window=draft.maintenance_window,
            required_approvers=draft.required_approver_roles,
            evidence_refs=[e | {"cited": e["id"] in set(draft.evidence_refs)} for e in evidence]
            + [
                {"id": r, "type": "unknown", "title": "Citation not found in evidence set", "cited": True, "invalid": True}
                for r in draft.evidence_refs
                if r not in {e["id"] for e in evidence}
            ],
            assumptions=draft.assumptions,
            requires_expert_validation=draft.requires_expert_validation,
            generated_by=f"{provider}/{model}",
            content_hash="",
            created_by=state.get("started_by"),
        )
        ctx.db.add(plan)
        ctx.db.flush()
        plan.content_hash = compute_plan_hash(plan)
        ctx.event("plan_created", f"Remediation plan revision {plan.revision} drafted", {"plan_id": plan.id})
        return PlanningOutput(
            plan_id=plan.id,
            revision=plan.revision,
            title=plan.title,
            target_version=plan.target_version,
            requires_expert_validation=plan.requires_expert_validation,
            evidence_count=len(evidence),
            generated_by=plan.generated_by,
        )
