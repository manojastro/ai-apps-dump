"""Agent 6: Change Risk Analysis (dependency-aware, uncertainty-explicit)."""

from __future__ import annotations

import json
from collections import deque
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.agents.base import Agent, AgentContext
from app.llm.base import StructuredTask, untrusted
from app.models.enterprise import Asset, AssetDependency
from app.models.remediation import RemediationPlan
from app.models.vulnerability import Finding
from app.tools.registry import ToolError

MAX_DEPTH = 3


class ChangeImpactNarrative(BaseModel):
    summary: str = Field(max_length=1500)
    recommended_review_steps: list[str] = Field(min_length=1, max_length=8)


class ChangeImpactOutput(BaseModel):
    plan_id: str
    risk_category: str
    business_impact: str
    affected_services: list[dict[str, Any]]
    impacted_assets: list[dict[str, Any]]
    known_dependencies: int
    unknown_dependencies: list[str]
    maintenance_window_required: bool
    downtime_estimate: str
    historical_changes: dict[str, Any]
    summary: str
    recommended_review_steps: list[str]
    confidence: str
    evidence: list[str]


def _traverse_dependents(db: Any, start: Asset) -> list[tuple[Asset, int]]:
    """BFS over 'used_by' edges: everything that (transitively) depends on the asset."""
    seen = {start.id}
    out: list[tuple[Asset, int]] = []
    queue: deque[tuple[str, int]] = deque([(start.id, 0)])
    while queue:
        aid, depth = queue.popleft()
        if depth >= MAX_DEPTH:
            continue
        for dep in db.scalars(select(AssetDependency).where(AssetDependency.target_asset_id == aid)):
            if dep.source_asset_id in seen:
                continue
            seen.add(dep.source_asset_id)
            asset = db.get(Asset, dep.source_asset_id)
            if asset:
                out.append((asset, depth + 1))
                queue.append((asset.id, depth + 1))
    return out


class ChangeRiskAnalysisAgent(Agent):
    name = "Change Risk Analysis Agent"
    node = "analyze_change_impact"
    description = "Analyses upstream/downstream CMDB dependencies, affected business services and change history."
    tools = {"asset_get_dependencies", "servicenow_search_records"}
    uses_llm = True
    evaluation = ["affected services match the CMDB graph", "unknown dependencies flagged", "no fabricated downtime"]
    Output = ChangeImpactOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> ChangeImpactOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        plan = ctx.db.get(RemediationPlan, state["plan_id"])
        assert finding is not None and plan is not None
        asset = finding.asset
        evidence: list[str] = []
        unknown: list[str] = []
        services: dict[str, dict[str, Any]] = {}
        impacted: list[dict[str, Any]] = []
        history: dict[str, Any] = {"available": False}

        if asset is None:
            unknown.append("Asset not resolved in CMDB: dependency analysis impossible")
        else:
            if asset.business_service:
                services[asset.business_service.name] = {
                    "name": asset.business_service.name,
                    "criticality": asset.business_service.criticality,
                    "relation": "direct",
                }
            deps = ctx.tool("asset_get_dependencies", asset_id=asset.id)
            evidence.append(
                f"CMDB relationships for {asset.hostname}: {len(deps['used_by'])} dependents, "
                f"{len(deps['depends_on'])} dependencies"
            )
            for dep_asset, depth in _traverse_dependents(ctx.db, asset):
                svc = dep_asset.business_service
                impacted.append(
                    {
                        "asset_id": dep_asset.id,
                        "hostname": dep_asset.hostname,
                        "depth": depth,
                        "environment": dep_asset.environment,
                        "service": svc.name if svc else None,
                    }
                )
                if svc and svc.name not in services:
                    services[svc.name] = {
                        "name": svc.name,
                        "criticality": svc.criticality,
                        "relation": f"dependent (depth {depth})",
                    }
                if svc is None:
                    unknown.append(f"{dep_asset.hostname} depends on this asset but has no business service in CMDB")
            if not deps["used_by"] and not deps["depends_on"]:
                unknown.append(f"No CMDB relationships recorded for {asset.hostname}; dependents may exist but are unknown")
            if asset.cmdb_sys_id:
                try:
                    hist = ctx.tool(
                        "servicenow_search_records", table="change_request", field="cmdb_ci", value=asset.cmdb_sys_id, limit=25
                    )
                    recs = hist["records"]
                    history = {
                        "available": True,
                        "total": len(recs),
                        "closed": sum(1 for r in recs if str(r.get("state")) == "3"),
                        "open": sum(1 for r in recs if str(r.get("state")) not in ("3", "4")),
                    }
                    evidence.append(f"{len(recs)} prior change requests on this CI in ServiceNow")
                except ToolError as exc:
                    unknown.append(f"Change history unavailable: {exc}")

        prod = bool(asset and asset.environment == "production")
        crit_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        top = max((crit_rank.get(s["criticality"], 0) for s in services.values()), default=-1)
        if asset is None:
            category = "unknown"
        elif prod and (top >= 2 or len(services) > 1):
            category = "high"
        elif prod or top >= 1:
            category = "medium"
        else:
            category = "low"
        impact = {3: "high", 2: "high", 1: "medium", 0: "low"}.get(top, "unknown")
        window = prod
        downtime = (
            "Unknown - requires restart of the affected component; duration not estimated "
            "because no historical outage data exists in evidence"
        )
        confidence = "low" if unknown else "medium" if not history.get("available") else "high"

        facts = {
            "asset": asset.hostname if asset else None,
            "environment": asset.environment if asset else None,
            "risk_category": category,
            "affected_services": list(services.values()),
            "impacted_assets": impacted[:20],
            "unknown_dependencies": unknown,
            "history": history,
            "plan_action": plan.recommended_action,
        }

        def mock() -> dict[str, Any]:
            names = ", ".join(services) or "no mapped business service"
            steps = ["Confirm the maintenance window with the owners of: " + names]
            if impacted:
                steps.append(f"Notify owners of {len(impacted)} dependent system(s) and agree smoke tests")
            if unknown:
                steps.append("Resolve unknown dependencies with the CMDB owner before scheduling")
            steps.append("Verify the rollback procedure with the service owner before implementation")
            return {
                "summary": (
                    f"Change on {facts['asset'] or 'an unresolved asset'} ({facts['environment'] or 'unknown env'}) "
                    f"is rated {category} change risk. Affected business services: {names}. "
                    f"{len(impacted)} dependent system(s) identified from CMDB relationships; "
                    f"{len(unknown)} dependency gap(s). Downtime is not estimated."
                ),
                "recommended_review_steps": steps,
            }

        narrative = ctx.llm(
            StructuredTask(
                name="change_impact_narrative",
                system=(
                    "You summarise change impact for a change advisory board. Use only the provided facts. "
                    "Do not estimate downtime durations. Highlight unknown dependencies."
                ),
                user=f"Facts:\n{untrusted('change_impact_facts', json.dumps(facts, default=str))}",
                output_model=ChangeImpactNarrative,
                mock_response=mock,
                max_output_tokens=800,
            )
        )
        report = ChangeImpactOutput(
            plan_id=plan.id,
            risk_category=category,
            business_impact=impact,
            affected_services=list(services.values()),
            impacted_assets=impacted,
            known_dependencies=len(impacted),
            unknown_dependencies=unknown,
            maintenance_window_required=window,
            downtime_estimate=downtime,
            historical_changes=history,
            summary=narrative.summary,
            recommended_review_steps=narrative.recommended_review_steps,
            confidence=confidence,
            evidence=evidence,
        )
        plan.change_impact = report.model_dump(mode="json")
        return report
