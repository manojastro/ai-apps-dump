"""RCA engine (M10): competing hypotheses with refutation, conflict,
missing-evidence and temporal analysis over NORMALIZED evidence.

Pure functions (no I/O) so the LLM path (coded tools) and the runner path
share one logic core. Thresholds: >=90 proceed, 70-89 confirm, <70 no
autonomous remediation. Conflicts or missing mandatory evidence → escalate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROCEED_AT = 90.0
CONFIRM_AT = 70.0

# Missing-evidence key -> follow-up tool (used by the runner, M8/M10).
MISSING_TO_TOOL = {
    "process breakdown": "query_processes",
    "identity correlation": "query_signin_history",
    "change correlation": "query_recent_changes",
    "software versions": "query_software_inventory",
}


def _num(item: dict[str, Any]) -> float:
    try:
        return float(str(item.get("value", "0")).rstrip("%"))
    except (TypeError, ValueError):
        return 0.0


def _blob(item: dict[str, Any]) -> str:
    return (f"{item.get('measurement')} {item.get('value')} "
            f"{item.get('sanitized_summary')}")


def propose_candidates(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Threshold triggers only — healthy readings never form hypotheses."""
    teams_mem = [str(e.get("evidence_id")) for e in evidence
                 if e.get("measurement") == "process_memory" and _num(e) >= 3000
                 and "teams" in _blob(e).lower()]
    teams_unhealthy = [str(e.get("evidence_id")) for e in evidence
                       if "UNHEALTHY" in str(e.get("sanitized_summary", ""))
                       and "Teams" in str(e.get("sanitized_summary", ""))]
    teams_change = [str(e.get("evidence_id")) for e in evidence
                    if e.get("measurement") == "change"
                    and "teams" in str(e.get("sanitized_summary", "")).lower()]
    disk_full = [str(e.get("evidence_id")) for e in evidence
                 if e.get("measurement") == "disk" and _num(e) >= 80]
    vpn_down = [str(e.get("evidence_id")) for e in evidence
                if e.get("measurement") == "vpn"
                and (str(e.get("value", "True")) == "False"
                     or "stale" in str(e.get("sanitized_summary", "")).lower()
                     or "DOWN" in str(e.get("sanitized_summary", "")))]
    candidates = []
    if teams_mem or teams_unhealthy:
        candidates.append({"title": "Teams excessive memory after update",
                           "supporting": sorted(set(teams_mem + teams_unhealthy + teams_change))})
    if disk_full:
        candidates.append({"title": "Disk exhaustion", "supporting": disk_full})
    if vpn_down:
        candidates.append({"title": "Stale secure-access token", "supporting": vpn_down})
    return candidates


def refuting_for(title: str, evidence: list[dict[str, Any]]) -> list[str]:
    """Contradictory readings for a candidate (empty = uncontested)."""
    lowered = title.lower()
    if "teams" in lowered:
        return [str(e.get("evidence_id")) for e in evidence
                if (e.get("measurement") == "process_memory"
                    and "teams" in str(e.get("sanitized_summary", "")).lower()
                    and _num(e) < 1500)
                or (e.get("measurement") == "software_version"
                    and "Teams" in str(e.get("sanitized_summary", ""))
                    and "UNHEALTHY" not in str(e.get("sanitized_summary", "")))]
    if "disk" in lowered:
        return [str(e.get("evidence_id")) for e in evidence
                if e.get("measurement") == "disk" and _num(e) < 80]
    if "token" in lowered or "vpn" in lowered:
        return [str(e.get("evidence_id")) for e in evidence
                if e.get("measurement") == "vpn"
                and str(e.get("value", "False")) == "True"
                and "stale" not in str(e.get("sanitized_summary", "")).lower()]
    return []


def score_candidate(supporting: list[str], refuting: list[str]) -> dict[str, Any]:
    total = len(supporting) + len(refuting)
    confidence = round(100 * len(supporting) / total, 1) if total else 0.0
    return {"confidence": confidence, "supporting": len(supporting),
            "refuting": len(refuting),
            "status": "SUPPORTED" if confidence >= 70 else "REJECTED"
            if refuting else "INSUFFICIENT EVIDENCE"}


def confidence_band(confidence: float) -> dict[str, Any]:
    if confidence >= 90:
        return {"level": "high", "may_auto_remediate": True,
                "action": "proceed under policy"}
    if confidence >= 70:
        return {"level": "medium", "may_auto_remediate": False,
                "action": "recommendation / human confirmation"}
    return {"level": "low", "may_auto_remediate": False,
            "action": "escalate — insufficient evidence for safe automation"}


def correlate(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    by_entity: dict[str, list[str]] = {}
    for item in evidence:
        entity = str(item.get("entity", "unknown"))
        by_entity.setdefault(entity, []).append(str(item.get("evidence_id", "?")))
    changes = [e for e in evidence if "change" in str(e.get("tool", "")).lower()
               or "change" in str(e.get("measurement", "")).lower()]
    return {"groups": [{"entity": k, "evidence_ids": v} for k, v in by_entity.items()],
            "change_adjacent": [e.get("evidence_id") for e in changes],
            "count": len(evidence)}


def temporal_links(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Change→symptom pairs by entity/name overlap (same-change context)."""
    links = []
    changes = [e for e in evidence if e.get("measurement") == "change"]
    others = [e for e in evidence if e.get("measurement") != "change"]
    for change in changes:
        change_blob = _blob(change).lower()
        matched = [str(o.get("evidence_id")) for o in others
                   if str(o.get("entity", "")).lower()
                   and (str(o.get("entity", "")).lower() in change_blob
                        or any(w in _blob(o).lower() for w in change_blob.split()[:4]
                               if len(w) > 4))]
        if matched:
            links.append({"change_id": str(change.get("evidence_id")),
                          "symptom_ids": sorted(set(matched)),
                          "summary": str(change.get("sanitized_summary", ""))})
    return links


def missing_evidence(evidence: list[dict[str, Any]]) -> list[str]:
    """Mandatory gaps that must block autonomous remediation."""
    missing = []
    pressured = any(e.get("measurement") in ("ram", "cpu") and _num(e) >= 85
                    for e in evidence)
    if pressured and not any(e.get("measurement") == "process_memory" for e in evidence):
        missing.append("process breakdown")
    vpn_fault = any(e.get("measurement") == "vpn"
                    and (str(e.get("value", "True")) == "False" or "stale" in _blob(e).lower())
                    for e in evidence)
    if vpn_fault and not any(e.get("measurement") == "signin" for e in evidence):
        missing.append("identity correlation")
    big_proc = any(e.get("measurement") == "process_memory" and _num(e) >= 3000
                   for e in evidence)
    if big_proc and not any(e.get("measurement") == "change" for e in evidence):
        missing.append("change correlation")
    return missing


# Titles in the same performance domain that cannot BOTH be the root cause.
_CONFLICT_PAIRS = frozenset({("Teams excessive memory after update", "Disk exhaustion")})


def find_conflicts(scored: list[dict[str, Any]]) -> list[list[str]]:
    supported = {h["title"] for h in scored if h.get("status") == "SUPPORTED"}
    return [sorted(pair) for pair in _CONFLICT_PAIRS if set(pair) <= supported]


def causal_graph(evidence: list[dict[str, Any]], root_cause: str = "") -> dict[str, Any]:
    nodes = [{"id": str(e.get("evidence_id", f"E{i}")),
              "label": str(e.get("sanitized_summary", e.get("measurement", "")))}
             for i, e in enumerate(evidence)]
    edges = [{"from": nodes[i]["id"], "to": nodes[i + 1]["id"]}
             for i in range(len(nodes) - 1)]
    if root_cause and nodes:
        nodes.append({"id": "ROOT_CAUSE", "label": root_cause})
        edges.append({"from": nodes[-2]["id"], "to": "ROOT_CAUSE"})
    lines = ["graph TD"]
    for edge in edges:
        lines.append(f"    {edge['from']} --> {edge['to']}")
    return {"nodes": nodes, "edges": edges,
            "mermaid": "\n".join(lines) if edges else "graph TD"}


@dataclass
class RcaResult:
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    verdict: str = "INSUFFICIENT"  # PROCEED | CONFIRM | ESCALATE | INSUFFICIENT
    top_confidence: float = 0.0
    conflicts: list[list[str]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    temporal: list[dict[str, Any]] = field(default_factory=list)


def diagnose(evidence: list[dict[str, Any]]) -> RcaResult:
    """Full RCA pass: propose → refute → score → conflict/missing → verdict."""
    result = RcaResult(temporal=temporal_links(evidence), missing=missing_evidence(evidence))
    scored = []
    for candidate in propose_candidates(evidence):
        # Contradicted candidates stay visible as REJECTED (never silently dropped).
        refuting = refuting_for(candidate["title"], evidence)
        scored_out = score_candidate(candidate["supporting"], refuting)
        scored.append({"title": candidate["title"],
                       "evidence": candidate["supporting"],
                       "refuting": refuting, **scored_out,
                       "band": confidence_band(scored_out["confidence"])["level"]})
    result.hypotheses = scored
    result.top_confidence = max((h["confidence"] for h in scored), default=0.0)
    result.conflicts = find_conflicts(scored)
    if not scored:
        result.verdict = "INSUFFICIENT"
    elif result.conflicts:
        result.verdict = "ESCALATE"
    elif result.missing:
        result.verdict = "ESCALATE"
    elif result.top_confidence >= PROCEED_AT:
        result.verdict = "PROCEED"
    elif result.top_confidence >= CONFIRM_AT:
        result.verdict = "CONFIRM"
    else:
        result.verdict = "ESCALATE"
    return result
