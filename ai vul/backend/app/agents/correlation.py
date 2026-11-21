"""Agent 2: Asset Correlation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import Agent, AgentContext, AgentFailure
from app.models.vulnerability import Finding
from app.services.asset_matching import AUTO_ACCEPT_THRESHOLD, correlate_asset
from app.tools.registry import ToolError


class AssetCorrelationOutput(BaseModel):
    status: str  # matched | ambiguous | unmatched
    asset_id: str | None
    hostname: str | None
    environment: str | None
    business_criticality: str | None
    internet_exposed: bool | None
    business_service: str | None
    owner: str | None
    support_group: str | None
    cmdb_sys_id: str | None
    cmdb_match_confidence: float | None
    match_rule: str | None
    match_explanation: str
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    defender_device: dict[str, Any] | None = None
    depends_on: list[str] = Field(default_factory=list)
    used_by: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    requires_human_review: bool


class AssetCorrelationAgent(Agent):
    name = "Asset Correlation Agent"
    node = "correlate_asset"
    description = "Correlates scanner identifiers with CMDB records, ownership, criticality, exposure and dependencies."
    tools = {"servicenow_get_asset", "defender_get_device", "asset_get_dependencies"}
    evaluation = ["correct asset match", "ambiguous matches never merged", "owner/criticality gaps reported"]
    Output = AssetCorrelationOutput

    def run(self, ctx: AgentContext, state: dict[str, Any]) -> AssetCorrelationOutput:
        finding = ctx.db.get(Finding, state["finding_id"])
        if finding is None:
            raise AgentFailure("finding not found")
        gaps: list[str] = []
        confidence: float | None
        rule: str | None
        asset_id: str | None
        if finding.correlation_status == "matched" and finding.source_evidence.get("match_rule") == "analyst_confirmed":
            status, asset_id = "matched", finding.asset_id
            confidence, rule, explanation, candidates = 1.0, "analyst_confirmed", "Match confirmed by an analyst", []
        else:
            m = correlate_asset(ctx.db, finding.reported_asset_identifier, finding.reported_ip, finding.reported_device_id)
            status, asset_id, confidence, rule = m.status, m.asset_id, m.confidence, m.rule
            explanation, candidates = m.explanation, m.candidates
            if status == "matched" and (confidence or 0) < AUTO_ACCEPT_THRESHOLD:
                status = "ambiguous"
            finding.correlation_status = status
            finding.asset_id = asset_id
            finding.correlation_confidence = confidence
            finding.correlation_candidates = candidates

        device = None
        try:
            if finding.reported_device_id:
                device = ctx.tool("defender_get_device", device_id=finding.reported_device_id)
            else:
                device = ctx.tool("defender_get_device", hostname=finding.reported_asset_identifier)
        except ToolError:
            gaps.append("Device not present in Defender inventory")

        if status != "matched" or asset_id is None:
            return AssetCorrelationOutput(
                status=status,
                asset_id=None,
                hostname=finding.reported_asset_identifier,
                environment=None,
                business_criticality=None,
                internet_exposed=None,
                business_service=None,
                owner=None,
                support_group=None,
                cmdb_sys_id=None,
                cmdb_match_confidence=confidence,
                match_rule=rule,
                match_explanation=explanation,
                candidates=candidates,
                defender_device=device,
                gaps=[*gaps, "Asset context unavailable until the CMDB match is resolved"],
                requires_human_review=True,
            )

        asset = ctx.tool("servicenow_get_asset", asset_id=asset_id)
        deps = ctx.tool("asset_get_dependencies", asset_id=asset_id)
        if not asset.get("owner"):
            gaps.append("CMDB record has no owner (owned_by empty)")
        if asset.get("business_criticality") is None:
            gaps.append("Business criticality missing in CMDB")
        if asset.get("internet_exposed") is None:
            gaps.append("Internet exposure unknown in CMDB")
        if not deps["depends_on"] and not deps["used_by"]:
            gaps.append("No CMDB relationships recorded: dependency information may be incomplete")
        if asset.get("cmdb_record_found") is False:
            gaps.append("Local asset references a CMDB CI that no longer exists")
        return AssetCorrelationOutput(
            status="matched",
            asset_id=asset_id,
            hostname=asset["hostname"],
            environment=asset["environment"],
            business_criticality=asset["business_criticality"],
            internet_exposed=asset["internet_exposed"],
            business_service=asset["business_service"],
            owner=asset["owner"],
            support_group=asset["support_group"],
            cmdb_sys_id=asset["cmdb_sys_id"],
            cmdb_match_confidence=confidence,
            match_rule=rule,
            match_explanation=explanation,
            candidates=candidates,
            defender_device=device,
            depends_on=[d["hostname"] for d in deps["depends_on"]],
            used_by=[d["hostname"] for d in deps["used_by"]],
            gaps=gaps,
            requires_human_review=False,
        )
