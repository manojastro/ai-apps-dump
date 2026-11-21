"""Evidence-driven investigation runner (M8).

Proves the central differentiator WITHOUT a live LLM: every tool choice
after initial intent routing is a pure function of accumulated EVIDENCE
(numbers), never of the request string. Same text + different device state
yields different tool sequences; healthy devices abstain early.

Pipeline: context → ranked routing → round-1 probes → evidence predicates →
RCA hypotheses + scoring + thresholds → bounded follow-up (max 1) → verdict.
Stop rules: confidence >= 90, tool budget (8), or no new informative call.
Evidence is normalized per evidence/normalize.py (M9) and optionally stored
to SQLite when case_id is given (agents operate on normalized rows).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

MAX_TOOL_CALLS = 8
# Thresholds live in orchestration/rca.py (single source); verdicts here map
# diagnose() output (PROCEED/CONFIRM/ESCALATE/INSUFFICIENT) to the trace.

# agent -> first-probe tools (round 1 only; everything after is evidence-led)
_FIRST_PROBES = {
    "endpoint_agent": ("query_device_health",),
    "software_agent": ("query_software_inventory",),
    "network_agent": ("query_vpn_state", "query_network"),
    "identity_agent": ("query_account_state", "query_signin_history"),
}

_TOOL_TO_AGENT = {
    "query_device_health": "endpoint_agent", "query_nexthink": "endpoint_agent",
    "query_tanium": "endpoint_agent", "query_processes": "endpoint_agent",
    "query_disk_health": "endpoint_agent", "query_endpoint_events": "endpoint_agent",
    "query_intune": "software_agent", "query_software_inventory": "software_agent",
    "query_software_catalog": "software_agent", "query_recent_changes": "software_agent",
    "query_patch_history": "software_agent", "query_network": "network_agent",
    "query_zscaler": "network_agent", "query_cloudflare": "network_agent",
    "query_dns": "network_agent", "query_vpn_state": "network_agent",
    "query_network_path": "network_agent", "query_entra": "identity_agent",
    "query_signin_history": "identity_agent", "query_account_state": "identity_agent",
    "query_mfa_state": "identity_agent", "query_access_state": "identity_agent",
}

_TOOL_TO_CLASS = {
    "query_device_health": ("observe", "QueryDeviceHealth"),
    "query_nexthink": ("observe", "QueryNexthink"),
    "query_tanium": ("observe", "QueryTanium"),
    "query_processes": ("observe", "QueryProcesses"),
    "query_disk_health": ("observe", "QueryDiskHealth"),
    "query_endpoint_events": ("observe", "QueryEndpointEvents"),
    "query_intune": ("observe", "QueryIntune"),
    "query_software_inventory": ("observe", "QuerySoftwareInventory"),
    "query_software_catalog": ("observe", "QuerySoftwareCatalog"),
    "query_recent_changes": ("observe", "QueryRecentChanges"),
    "query_patch_history": ("observe", "QueryPatchHistory"),
    "query_network": ("observe", "QueryNetwork"),
    "query_zscaler": ("observe", "QueryZscaler"),
    "query_cloudflare": ("observe", "QueryCloudflare"),
    "query_dns": ("observe", "QueryDns"),
    "query_vpn_state": ("observe", "QueryVpnState"),
    "query_network_path": ("observe", "QueryNetworkPath"),
    "query_entra": ("observe", "QueryEntra"),
    "query_signin_history": ("observe", "QuerySigninHistory"),
    "query_account_state": ("observe", "QueryAccountState"),
    "query_mfa_state": ("observe", "QueryMfaState"),
    "query_access_state": ("observe", "QueryAccessState"),
    "search_enterprise_knowledge": ("knowledge", "SearchEnterpriseKnowledge"),
}


@dataclass
class TraceStep:
    agent: str
    tool: str
    summary: str


@dataclass
class Investigation:
    request_text: str
    device_id: str
    user_id: str
    case_id: str = ""
    steps: list[TraceStep] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    verdict: str = "ESCALATE"
    confidence: float = 0.0
    follow_up_used: bool = False
    stored_ids: list[str] = field(default_factory=list)

    @property
    def agents_involved(self) -> list[str]:
        seen: list[str] = []
        for step in self.steps:
            if step.agent not in seen:
                seen.append(step.agent)
        return seen

    @property
    def tools_consulted(self) -> list[str]:
        return [step.tool for step in self.steps]


def _load_tool(tool_name: str):
    import importlib
    module_name, class_name = _TOOL_TO_CLASS[tool_name]
    module = importlib.import_module(f"coded_tools.digital_workplace.{module_name}")
    return getattr(module, class_name)()


async def _call(tool_name: str, args: dict[str, Any]) -> Any:
    return await _load_tool(tool_name).async_invoke(dict(args), {})


def _persist(case_id: str, db_path: str | None, inv: Investigation,
             evidence: list[dict[str, Any]]) -> None:
    """Store one normalized batch + ranked hypotheses (no-op without case_id)."""
    if not case_id or not evidence:
        return
    from common.config import load_settings
    from database.bootstrap import get_connection, init_db
    from evidence.store import ensure_case, save_evidence, save_hypotheses
    path = db_path or load_settings(env_file=".env").db_path
    init_db(path)
    conn = get_connection(path)
    try:
        ensure_case(conn, case_id, inv.user_id, inv.device_id, inv.request_text)
        inv.stored_ids = save_evidence(conn, case_id, evidence)
        save_hypotheses(conn, case_id, inv.hypotheses)
    finally:
        conn.close()


def _next_tools(facts: dict[str, Any]) -> list[tuple[str, str]]:
    """Evidence predicates → follow-up (tool, reason). No request-text input."""
    follow: list[tuple[str, str]] = []
    health = facts.get("query_device_health", {})
    if health:
        try:
            ram, cpu, disk = float(health.get("ram_pct", 0)), float(health.get("cpu_pct", 0)), float(health.get("disk_pct", 0))
        except (TypeError, ValueError):
            ram = cpu = disk = 0.0
        if ram >= 85 or cpu >= 85:
            follow.append(("query_processes", f"ram {ram}%/cpu {cpu}% needs process breakdown"))
        elif disk >= 80:
            follow.append(("query_disk_health", f"disk {disk}% needs health detail"))
    procs = facts.get("query_processes", {}).get("processes", [])
    if any(float(p.get("mem_mb", 0)) >= 3000 for p in procs):
        follow.append(("query_recent_changes", "multi-GB process needs change correlation"))
        follow.append(("query_software_inventory", "multi-GB process needs version check"))
    vpn = facts.get("query_vpn_state", {})
    if vpn and not vpn.get("connected", True):
        follow.append(("query_signin_history", "vpn down needs identity correlation"))
        follow.append(("query_zscaler", "vpn down needs secure-access view"))
    account = facts.get("query_account_state", {})
    if account and (account.get("locked") or account.get("account_state") != "active"):
        follow.append(("query_mfa_state", "account trouble needs MFA state"))
    return follow


async def investigate(request_text: str, device_id: str = "DEVICE_001",
                      user_id: str = "USER_001", seed: int = 42,
                      case_id: str = "", db_path: str | None = None) -> Investigation:
    """Run one evidence-driven investigation. Deterministic for (seed, device).

    When case_id is given, normalized evidence + ranked hypotheses are
    stored to SQLite (M9/M10).
    """
    from coded_tools.digital_workplace.commander_tools import RouteRequest
    from evidence.normalize import normalize
    from orchestration.rca import MISSING_TO_TOOL, RcaResult, diagnose

    inv = Investigation(request_text=request_text, device_id=device_id,
                        user_id=user_id, case_id=case_id)
    base = {"device_id": device_id, "user_id": user_id, "seed": seed}
    called: set[tuple[str, str]] = set()
    called_names: set[str] = set()
    facts: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []

    # Audit trail (M19): per-call rows only when a case is open. Closed on
    # every return path below via _close_audit.
    audit_conn = None
    if case_id:
        from common.config import load_settings
        from database.bootstrap import get_connection, init_db
        _audit_path = db_path or load_settings(env_file=".env").db_path
        init_db(_audit_path)
        audit_conn = get_connection(_audit_path)

    def _audit(agent: str, event_type: str, tool: str, action: str = "",
              decision: str = "", duration_ms: int = 0, success: int = 1) -> None:
        if audit_conn is None:
            return
        from audit.logger import log_event
        from database.models import AuditEvent
        log_event(audit_conn, AuditEvent(
            case_id=case_id, agent=agent, event_type=event_type, tool=tool,
            sanitized_input=f"{tool} {device_id} {user_id}",
            sanitized_output=action or "ok", action=action, decision=decision,
            duration_ms=duration_ms, success=success))

    def _close_audit() -> None:
        if audit_conn is not None:
            audit_conn.close()

    async def run_tool(agent: str, tool_name: str, extra: dict[str, Any] | None = None) -> Any:
        target = extra.get("user_id", device_id) if extra else device_id
        if (tool_name, target) in called or len(inv.steps) >= MAX_TOOL_CALLS:
            return None
        called.add((tool_name, target))
        called_names.add(tool_name)
        started = time.perf_counter()
        try:
            result = await _call(tool_name, {**base, **(extra or {})})
        except (LookupError, ValueError) as e:
            # Missing telemetry must degrade to escalation, never crash.
            duration_ms = int((time.perf_counter() - started) * 1000)
            inv.steps.append(TraceStep(agent, tool_name, f"{tool_name} FAILED: {e}"))
            _audit(agent, "tool", tool_name, action=str(e),
                   duration_ms=duration_ms, success=0)
            return None
        duration_ms = int((time.perf_counter() - started) * 1000)
        facts[tool_name] = result
        evidence.extend(normalize(tool_name, result, case_id=case_id,
                                  device_id=device_id, start=len(evidence) + 1))
        inv.steps.append(TraceStep(agent, tool_name, f"{tool_name} -> ok"))
        _audit(agent, "tool", tool_name, duration_ms=duration_ms)
        return result

    started = time.perf_counter()
    routing = await RouteRequest().async_invoke({"request_text": request_text}, {})
    _audit("commander", "routing", "route_request",
           action=",".join(r["agent"] for r in routing["ranked"] if r["score"] > 0),
           duration_ms=int((time.perf_counter() - started) * 1000))
    ranked = [r["agent"] for r in routing["ranked"] if r["score"] > 0]

    if ranked and ranked[0] == "knowledge_agent":
        from coded_tools.digital_workplace.knowledge import SearchEnterpriseKnowledge
        from evidence.store import ensure_case
        if audit_conn is not None:
            ensure_case(audit_conn, case_id, user_id, device_id, request_text)
        result = await SearchEnterpriseKnowledge().async_invoke(
            {"query": request_text, "user_role": "employee"}, {})
        inv.steps.append(TraceStep("knowledge_agent", "search_enterprise_knowledge",
                                   f"results={len(result['results'])}"))
        _audit("knowledge_agent", "tool", "search_enterprise_knowledge")
        inv.verdict = "KNOWLEDGE"
        _close_audit()
        return inv

    # Round 1: first probes of the top-2 ranked specialists.
    for agent in ranked[:2]:
        for tool_name in _FIRST_PROBES.get(agent, ()):
            extra = {"user_id": user_id} if "identity" in agent or "signin" in tool_name or "account" in tool_name or "mfa" in tool_name or "access" in tool_name or "entra" in tool_name else None
            await run_tool(_TOOL_TO_AGENT[tool_name], tool_name, extra)

    # Round 2+: evidence predicates to a fixpoint (new facts may unlock more).
    # Bounded by the tool budget and the called-set (dedupe) — always terminates.
    while len(inv.steps) < MAX_TOOL_CALLS:
        queued = [(t, r) for t, r in _next_tools(facts)
                  if t not in called_names]
        if not queued:
            break
        for tool_name, _reason in queued:
            await run_tool(_TOOL_TO_AGENT[tool_name], tool_name,
                           {"user_id": user_id} if tool_name == "query_signin_history" else None)

    async def rca_round() -> RcaResult:
        started = time.perf_counter()
        result = diagnose(evidence)
        inv.hypotheses = [{"title": h["title"], "evidence": h["evidence"],
                           "refuting": h["refuting"], "confidence": h["confidence"],
                           "status": h["status"], "band": h["band"]}
                          for h in result.hypotheses]
        inv.confidence = result.top_confidence
        _audit("rca_agent", "rca", "diagnose", decision=result.verdict,
               duration_ms=int((time.perf_counter() - started) * 1000))
        return result

    result = await rca_round()
    if result.verdict == "PROCEED":
        inv.verdict = "PROCEED"
        _persist(case_id, db_path, inv, evidence)
        _close_audit()
        return inv

    # Bounded follow-up: RCA names the missing evidence; fetch it once.
    wanted: list[tuple[str, dict[str, Any] | None]] = [
        (MISSING_TO_TOOL[m], {"user_id": user_id}
         if MISSING_TO_TOOL[m] == "query_signin_history" else None)
        for m in result.missing if m in MISSING_TO_TOOL]
    if (result.top_confidence == 0
            and not any("query_processes" in s.tool for s in inv.steps)
            and facts.get("query_device_health")):
        wanted.append(("query_processes", None))
    if wanted and len(inv.steps) < MAX_TOOL_CALLS:
        inv.follow_up_used = True
        for tool_name, extra in wanted:
            await run_tool(_TOOL_TO_AGENT[tool_name], tool_name, extra)
        while len(inv.steps) < MAX_TOOL_CALLS:
            queued = [(t, r) for t, r in _next_tools(facts)
                      if t not in called_names]
            if not queued:
                break
            for tool_name, _reason in queued:
                await run_tool(_TOOL_TO_AGENT[tool_name], tool_name,
                               {"user_id": user_id} if tool_name == "query_signin_history" else None)
        result = await rca_round()

    inv.verdict = {"PROCEED": "PROCEED", "CONFIRM": "CONFIRM"}.get(result.verdict, "ESCALATE")
    _audit("commander", "verdict", "", decision=inv.verdict)
    _persist(case_id, db_path, inv, evidence)
    _close_audit()
    return inv


def investigate_sync(request_text: str, device_id: str = "DEVICE_001",
                     user_id: str = "USER_001", seed: int = 42,
                     case_id: str = "", db_path: str | None = None) -> Investigation:
    return asyncio.run(investigate(request_text, device_id, user_id, seed,
                                   case_id, db_path))
