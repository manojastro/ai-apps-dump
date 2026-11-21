"""Contextual security assistant.

Scope is deliberately narrow: it answers questions about data already in the platform using
read-only tools under the *user's own* permissions, cites evidence, separates facts from
suggestions, and can only *propose* state-changing actions (the UI asks the user to confirm
and then calls the normal, permission-checked API).

* mock provider  -> deterministic intent router over the same tools
* real provider  -> bounded plan-act loop: the model picks one tool per step (max 4 steps)
"""

from __future__ import annotations

import json
import re
from datetime import timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.types import utcnow
from app.llm.base import StructuredTask, untrusted
from app.llm.factory import build_provider
from app.models.remediation import ApprovalRequest, RemediationPlan
from app.models.vulnerability import Vulnerability
from app.security.auth import Principal
from app.tools.catalog import READ_ONLY_TOOLS
from app.tools.registry import ToolContext, ToolError, registry

MAX_STEPS = 4


class Ref(BaseModel):
    type: Literal["finding", "plan", "approval", "vulnerability", "asset", "workflow"]
    id: str
    label: str


class Fact(BaseModel):
    text: str = Field(max_length=600)
    refs: list[Ref] = Field(default_factory=list)


class ProposedAction(BaseModel):
    type: Literal["start_investigation", "request_approval", "open_plan", "open_finding"]
    target_id: str
    label: str
    requires_confirmation: bool = True


class AssistantAnswer(BaseModel):
    answer: str = Field(max_length=3000)
    facts: list[Fact] = Field(default_factory=list, max_length=20)
    suggestions: list[str] = Field(default_factory=list, max_length=6)
    proposed_actions: list[ProposedAction] = Field(default_factory=list, max_length=5)


class StepDecision(BaseModel):
    tool: str | None = Field(default=None, description="Tool to call next, or null when ready to answer")
    arguments: dict[str, Any] = Field(default_factory=dict)
    final: AssistantAnswer | None = None


def _fref(f: dict[str, Any]) -> Ref:
    return Ref(type="finding", id=f["finding_id"], label=f"{f['cve_id']} on {f['asset']}")


def _finding_fact(f: dict[str, Any]) -> Fact:
    kev = "KEV-listed" if f.get("kev") else "not in KEV" if f.get("kev") is False else "KEV unknown"
    epss = f"EPSS {f['epss']:.3f}" if f.get("epss") is not None else "EPSS n/a"
    return Fact(
        text=f"{f['cve_id']} on {f['asset']} - risk {f['risk_score']} ({f['risk_level']}, {f['priority']}), {kev}, {epss}"
        + (f", service {f['business_service']}" if f.get("business_service") else ""),
        refs=[_fref(f)],
    )


class Assistant:
    def __init__(self, db: Session, principal: Principal) -> None:
        self.db = db
        self.principal = principal
        self.calls: list[dict[str, Any]] = []

    def tool(self, name: str, **args: Any) -> dict[str, Any]:
        ctx = ToolContext(self.db, self.principal, "assistant")
        result = registry.call(name, args, ctx, READ_ONLY_TOOLS)
        self.calls.append({"tool": name, "arguments": args})
        return result

    # ------------------------------------------------------------------ deterministic router (mock)
    def _mock(self, message: str, context: dict[str, Any]) -> AssistantAnswer:
        m = message.lower()
        num = re.search(r"\b(\d{1,2})\b", m)
        limit = min(int(num.group(1)), 20) if num else 5
        cve = re.search(r"cve-\d{4}-\d{4,7}", m)
        services = [
            "payment",
            "ledger",
            "storefront",
            "order",
            "identity",
            "manufacturing",
            "supply chain",
            "collaboration",
            "ci/cd",
            "messaging",
        ]

        if "pending" in m and "approval" in m:
            reqs = list(
                self.db.scalars(
                    select(ApprovalRequest).where(ApprovalRequest.state == "PENDING").order_by(ApprovalRequest.created_at)
                )
            )
            self.calls.append({"tool": "approvals(pending)", "arguments": {}})
            facts = []
            for r in reqs:
                plan = self.db.get(RemediationPlan, r.plan_id)
                facts.append(
                    Fact(
                        text=f"{plan.title if plan else r.plan_id} - risk {r.risk_level}, requested {r.created_at:%Y-%m-%d}",
                        refs=[Ref(type="approval", id=r.id, label="approval"), Ref(type="plan", id=r.plan_id, label="plan")],
                    )
                )
            return AssistantAnswer(
                answer=f"{len(reqs)} remediation plan(s) are pending approval.",
                facts=facts,
                suggestions=["Open the Approval Center to review them."] if reqs else [],
            )

        if ("why" in m or "explain" in m) and ("score" in m or "risk" in m):
            finding_id = context.get("finding_id")
            if not finding_id and cve:
                rows = self.tool("findings_search", cve_id=cve.group(0).upper(), limit=1)["findings"]
                finding_id = rows[0]["finding_id"] if rows else None
            if not finding_id:
                return AssistantAnswer(
                    answer="Tell me which finding or CVE you mean (e.g. 'Why was CVE-2021-44228 scored 100?')."
                )
            risk = self.tool("finding_get_risk", finding_id=finding_id)
            if not risk.get("assessed", True) and "score" not in risk:
                return AssistantAnswer(answer="That finding has not been risk-assessed yet.")
            facts = [
                Fact(
                    text=f"{v['label']}: {v['points']}/{v['max_points']} pts - {v['explanation']}",
                    refs=[Ref(type="finding", id=finding_id, label=risk["cve_id"])],
                )
                for v in risk["factors"].values()
            ]
            missing = f" Missing factors: {', '.join(risk['missing_factors'])}." if risk["missing_factors"] else ""
            return AssistantAnswer(
                answer=f"{risk['cve_id']} scored {risk['score']} ({risk['risk_level']}, {risk['priority']}) under policy {risk['policy_version']}. "
                f"Coverage {risk['coverage']:.0%}; the score band is {risk['band'][0]}-{risk['band'][1]}.{missing} "
                "The score is computed deterministically; the AI does not assign it.",
                facts=facts,
            )

        if ("prepare" in m and "plan" in m) or "remediation plan for" in m:
            finding_id = context.get("finding_id")
            if not finding_id and cve:
                rows = self.tool("findings_search", cve_id=cve.group(0).upper(), limit=1)["findings"]
                finding_id = rows[0]["finding_id"] if rows else None
            if not finding_id:
                return AssistantAnswer(
                    answer="Open a finding (or mention its CVE) and ask again; I will propose starting an investigation."
                )
            return AssistantAnswer(
                answer="Remediation plans are produced by the multi-agent investigation so they are evidence-linked and validated. "
                "I can start one for you after you confirm.",
                proposed_actions=[
                    ProposedAction(type="start_investigation", target_id=finding_id, label="Start AI investigation")
                ],
                suggestions=["The generated plan will still require human approval before any ServiceNow record is created."],
            )

        if "verified" in m or "resolved" in m:
            rows = self.tool("findings_search", verification_state="verified_remediated", limit=50)["findings"]
            if "week" in m:
                cutoff = utcnow() - timedelta(days=7)
                rows = [f for f in rows if f.get("remediated_at") and f["remediated_at"] >= cutoff.isoformat()]
            period = " in the last 7 days" if "week" in m else ""
            return AssistantAnswer(
                answer=f"{len(rows)} finding(s) were verified as remediated by fresh scan evidence{period}.",
                facts=[_finding_fact(f) for f in rows],
                suggestions=["Verification requires a post-change rescan; ServiceNow closure alone never counts."],
            )

        if "kev" in m or "known exploit" in m or ("confirmed" in m and "exploit" in m):
            rows = self.tool("findings_search", kev_only=True, status="open", limit=limit if num else 15)["findings"]
            return AssistantAnswer(
                answer=f"{len(rows)} open finding(s) involve CVEs listed in CISA KEV (confirmed exploitation).",
                facts=[_finding_fact(f) for f in rows],
                suggestions=["EPSS is a probability estimate; KEV listing is the confirmed-exploitation signal."],
            )

        service = next((s for s in services if s in m), None)
        if service:
            level = "critical" if "critical" in m else None
            rows = self.tool("findings_search", business_service=service, risk_level=level, status="open", limit=15)["findings"]
            return AssistantAnswer(
                answer=f"{len(rows)} open {'critical ' if level else ''}finding(s) affect the '{service}' business service.",
                facts=[_finding_fact(f) for f in rows],
            )

        if "highest" in m or "top" in m or "riskiest" in m or "most critical" in m:
            rows = self.tool("findings_search", status="open", limit=limit)["findings"]
            return AssistantAnswer(
                answer=f"Top {len(rows)} open findings by deterministic risk score:",
                facts=[_finding_fact(f) for f in rows],
                proposed_actions=[
                    ProposedAction(
                        type="open_finding",
                        target_id=rows[0]["finding_id"],
                        label="Open highest-risk finding",
                        requires_confirmation=False,
                    )
                ]
                if rows
                else [],
            )

        if cve:
            data = self.tool("threat_check_kev", cve_id=cve.group(0).upper())
            epss = self.tool("threat_get_epss", cve_id=cve.group(0).upper())
            vuln = self.db.scalar(select(Vulnerability).where(Vulnerability.cve_id == cve.group(0).upper()))
            facts = [
                Fact(text=f"KEV status: {data['status']} ({data['reference']})"),
                Fact(text=f"EPSS: {(epss.get('data') or {}).get('epss', 'n/a')} ({epss['reference']})"),
            ]
            if vuln:
                facts.insert(
                    0,
                    Fact(
                        text=f"{vuln.cve_id}: CVSS {vuln.cvss_score} {vuln.severity}; {len(vuln.findings)} finding(s)",
                        refs=[Ref(type="vulnerability", id=vuln.cve_id, label=vuln.cve_id)],
                    ),
                )
            return AssistantAnswer(answer=f"Here is what the platform knows about {cve.group(0).upper()}.", facts=facts)

        return AssistantAnswer(
            answer=(
                "I can answer questions about data in AegisRemediate, for example: 'What are the five highest-risk vulnerabilities?', "
                "'Which critical vulnerabilities affect payment systems?', 'Why was CVE-2021-44228 scored 100?', "
                "'Which remediation plans are pending approval?', 'Show vulnerabilities with confirmed known exploitation', "
                "'Prepare a remediation plan for this finding', 'Which findings were verified as resolved this week?'"
            )
        )

    # ------------------------------------------------------------------ LLM plan-act loop
    def _llm(self, message: str, context: dict[str, Any]) -> AssistantAnswer:
        provider = build_provider()
        tools = registry.describe(READ_ONLY_TOOLS)
        transcript: list[dict[str, Any]] = []
        system = (
            "You are the AegisRemediate security assistant. Answer ONLY from tool results. Cite findings/plans in refs. "
            "Separate facts (from tools) from suggestions. You cannot change state; propose actions instead. "
            f"Available read-only tools: {json.dumps(tools)[:12000]}"
        )
        for _ in range(MAX_STEPS):
            decision = provider.generate(
                StructuredTask(
                    name="assistant_step",
                    system=system,
                    output_model=StepDecision,
                    user=f"User question: {message}\nUI context: {json.dumps(context)}\n"
                    f"Tool results so far:\n{untrusted('tool_results', transcript)}",
                    mock_response=lambda: {"tool": None, "final": {"answer": "n/a"}},
                    max_output_tokens=1500,
                )
            ).output
            if decision.final is not None or not decision.tool:
                return decision.final or AssistantAnswer(answer="I could not find an answer in the available data.")
            try:
                result = self.tool(decision.tool, **decision.arguments)
            except ToolError as exc:
                result = {"error": str(exc)}
            transcript.append({"tool": decision.tool, "arguments": decision.arguments, "result": result})
        return AssistantAnswer(answer="I reached the tool-call limit before finishing; please narrow the question.")

    def ask(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        provider = build_provider()
        answer = self._mock(message, context) if provider.name == "mock" else self._llm(message, context)
        return answer.model_dump() | {
            "tool_calls": self.calls,
            "mode": provider.name,
            "disclaimer": "Facts come from platform data via read-only tools; suggestions are advisory.",
        }
