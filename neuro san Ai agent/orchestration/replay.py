"""Known-workflow replay (M22): same issue → approved workflow → policy
re-check → execute per autonomy → verify → metrics. Policy is re-evaluated
on EVERY reuse; a changed posture (deny/non-compliant) aborts the replay.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_MISS = "miss"
_HIT = "hit"

_STOPWORDS = frozenset({
    "the", "and", "for", "with", "how", "what", "when", "where", "who",
    "are", "was", "were", "been", "have", "has", "had", "will", "would",
    "should", "could", "does", "doing", "about", "into", "from", "that",
    "this", "your", "you", "our", "their", "they", "them", "then", "than",
    "also", "such", "only", "more", "most", "other", "some", "any", "all",
    "can", "may", "laptop", "keeps", "very", "stopped", "working",
})


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower())
            if len(w) > 2 and w not in _STOPWORDS}


def match_signature(request_text: str, failure_signature: str) -> float:
    """Overlap of signature terms in the request (0-1). Hit at >= 0.5."""
    sig_terms = _terms(failure_signature.replace("_", " "))
    if not sig_terms:
        return 0.0
    return round(len(sig_terms & _terms(request_text)) / len(sig_terms), 3)


@dataclass
class ReplayResult:
    status: str = _MISS  # hit | miss
    workflow_id: str = ""
    action_id: str = ""
    autonomy: str = ""
    policy_decision: str = ""
    human_intervention: str = "NONE"
    execution: Any = None
    verification: Any = None
    reasons: list[str] = field(default_factory=list)


def find_matching_workflow(conn: Any, request_text: str) -> dict[str, Any] | None:
    """Best approved workflow whose signature overlaps the request."""
    rows = conn.execute("SELECT * FROM workflows WHERE approval_state='approved'").fetchall()
    best, best_score = None, 0.0
    for row in rows:
        record = dict(row)
        score = match_signature(request_text, record.get("failure_signature", ""))
        if score >= 0.5 and score > best_score:
            best, best_score = record, score
    return best


def try_known_workflow(conn: Any, estate: Any, case_id: str, request_text: str,
                       device_id: str, user_id: str, user_role: str = "employee",
                       seed: int = 42) -> ReplayResult:
    """Replay one approved workflow end to end. Miss → caller investigates."""
    from control_plane.execution import AWAITING, EXECUTED, request_execution
    from control_plane.learning import recheck_workflow, record_workflow_run
    from control_plane.rollback import verify_and_recover

    match = find_matching_workflow(conn, request_text)
    if match is None:
        return ReplayResult(reasons=["no approved workflow matches"])
    workflow_id, action_id = match["workflow_id"], match["action_id"]

    try:
        device = estate.get(device_id)
    except LookupError:
        return ReplayResult(reasons=[f"unknown device {device_id}"])
    verdict = recheck_workflow(
        conn, workflow_id, user_id, user_role, device_id,
        device_group=device.device_group,
        device_compliant=device.compliance_state == "compliant")
    if verdict.decision == "DENY":
        return ReplayResult(status=_HIT, workflow_id=workflow_id, action_id=action_id,
                            policy_decision="DENY", human_intervention="REQUIRED",
                            reasons=["policy re-check DENYs this device; full investigation"])
    level = str(match.get("autonomy_level", "L2"))
    if level in ("L0", "L1"):
        return ReplayResult(status=_HIT, workflow_id=workflow_id, action_id=action_id,
                            autonomy=level, policy_decision=verdict.decision,
                            human_intervention="REQUIRED",
                            reasons=[f"autonomy {level} never auto-executes"])

    executed = request_execution(conn, estate, case_id, action_id, device_id, user_id,
                                 user_role=user_role)
    if executed.status == AWAITING:
        # No outcome yet — metrics record on the eventual execution, not the pause.
        return ReplayResult(status=_HIT, workflow_id=workflow_id, action_id=action_id,
                            autonomy=level, policy_decision=verdict.decision,
                            human_intervention="REQUIRED",
                            execution=executed, reasons=[f"approval {executed.approval_id} pending"])
    if executed.status != EXECUTED:
        record_workflow_run(conn, workflow_id, case_id, verdict.decision, "n/a", False)
        return ReplayResult(status=_HIT, workflow_id=workflow_id, action_id=action_id,
                            autonomy=level, policy_decision=verdict.decision,
                            human_intervention="REQUIRED", execution=executed,
                            reasons=executed.reasons)
    recovered = verify_and_recover(conn, estate, executed.run_id, case_id)
    ok = recovered["outcome"] == "verified"
    record_workflow_run(conn, workflow_id, case_id, verdict.decision,
                        "APPROVED" if level == "L2" else "auto", ok)
    return ReplayResult(status=_HIT, workflow_id=workflow_id, action_id=action_id,
                        autonomy=level, policy_decision=verdict.decision,
                        human_intervention="NONE" if level in ("L3", "L4") else "APPROVED",
                        execution=executed, verification=recovered,
                        reasons=["known failure signature; approved workflow found"])
