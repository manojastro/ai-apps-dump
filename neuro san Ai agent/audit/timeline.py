"""Decision trace (M19): one chronological timeline per case + final card.

Merges audit_events, policy_decisions, remediation_runs, hypotheses,
evidence, incidents and approvals. All secrets were redacted at write time;
the timeline re-scans on read (defense in depth) and reports any leak.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from common.redaction import scan_prompt_for_secrets


def _ts(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def build_timeline(conn: sqlite3.Connection, case_id: str) -> list[dict[str, Any]]:
    """Chronological entries across every record type for one case."""
    entries: list[dict[str, Any]] = []

    def add(timestamp: str, kind: str, agent: str, summary: str,
            success: int = 1, ref: str = "") -> None:
        entries.append({"timestamp": timestamp or "", "kind": kind, "agent": agent,
                        "summary": summary, "success": success, "ref": ref})

    for row in conn.execute("SELECT * FROM audit_events WHERE case_id=?", (case_id,)):
        event = f"{row['event_type']}:{row['tool']}" if row["tool"] else row["event_type"]
        add(row["timestamp"], "audit", row["agent"] or "system",
            f"{event} {row['action'] or ''} {row['decision'] or ''}".strip()
            or "event", row["success"], f"event:{row['event_id']}")
    for row in conn.execute("SELECT * FROM policy_decisions WHERE case_id=?", (case_id,)):
        add(row["created_at"], "policy", "policy-engine",
            f"{row['script_id']} -> {row['decision']}", 1, f"policy:{row['decision_id']}")
    for row in conn.execute("SELECT * FROM remediation_runs WHERE case_id=?", (case_id,)):
        add(row["started_at"], "execution", "execution_controller",
            f"{row['script_id']} on {row['device_id']} "
            f"(verify: {bool(row['verification_result'])})", row["success"],
            f"run:{row['run_id']}")
    for row in conn.execute("SELECT * FROM hypotheses WHERE case_id=?", (case_id,)):
        add(row["created_at"], "rca", "rca_agent",
            f"{row['title']} {row['confidence']}% {row['status']}", 1,
            f"hyp:{row['hypothesis_id']}")
    for row in conn.execute("SELECT COUNT(*) AS n FROM evidence WHERE case_id=?", (case_id,)):
        if row["n"]:
            first = conn.execute("SELECT timestamp FROM evidence WHERE case_id=? "
                                 "ORDER BY evidence_id LIMIT 1", (case_id,)).fetchone()
            add(first["timestamp"] if first else "", "evidence", "specialists",
                f"{row['n']} normalized evidence records", 1, "evidence")
    for row in conn.execute("SELECT * FROM incidents WHERE case_id=?", (case_id,)):
        add(row["created_at"], "itsm", "servicenow_agent",
            f"{row['incident_id']} opened", 1, f"inc:{row['incident_id']}")
        if row["resolved_at"]:
            add(row["resolved_at"], "itsm", "servicenow_agent",
                f"{row['incident_id']} resolved", 1, f"inc:{row['incident_id']}")
    for row in conn.execute(
            "SELECT * FROM approvals WHERE case_id=? AND state != 'PENDING'", (case_id,)):
        add(row["decided_at"] or row["requested_at"], "approval",
            row["approver"] or "human", f"{row['script_id']} {row['state']}", 1,
            f"approval:{row['approval_id']}")
    entries.sort(key=lambda e: (_ts(e["timestamp"]), e["kind"], e["ref"]))
    return entries


def scan_timeline(entries: list[dict[str, Any]]) -> list[str]:
    """Secret shapes found anywhere in the timeline (empty = clean)."""
    blob = json.dumps(entries, default=str)
    return scan_prompt_for_secrets(blob)


def render_timeline_markdown(entries: list[dict[str, Any]]) -> str:
    lines = ["# Incident timeline", ""]
    for entry in entries:
        mark = "ok" if entry["success"] else "FAIL"
        lines.append(f"- {entry['timestamp']} [{entry['kind']}] {entry['agent']}: "
                     f"{entry['summary']} ({mark})")
    return "\n".join(lines) + "\n"


def build_final_card(conn: sqlite3.Connection, case_id: str) -> dict[str, Any]:
    """User-facing final card (spec shape). Fleet fields arrive in M23/M24."""
    card: dict[str, Any] = {"case_id": case_id}
    hyp = conn.execute("SELECT * FROM hypotheses WHERE case_id=? AND status='SUPPORTED' "
                       "ORDER BY confidence DESC LIMIT 1", (case_id,)).fetchone()
    card["root_cause"] = hyp["title"] if hyp else ""
    card["confidence"] = hyp["confidence"] if hyp else 0.0
    agents = [r["agent"] for r in conn.execute(
        "SELECT DISTINCT agent FROM audit_events WHERE case_id=? AND agent != ''",
        (case_id,))]
    card["agents_involved"] = sorted(agents)
    card["tools_consulted"] = sorted({r["tool"] for r in conn.execute(
        "SELECT DISTINCT tool FROM audit_events WHERE case_id=? AND tool != ''",
        (case_id,))})
    decision = conn.execute("SELECT * FROM policy_decisions WHERE case_id=? "
                            "ORDER BY created_at DESC LIMIT 1", (case_id,)).fetchone()
    card["policy"] = decision["decision"] if decision else ""
    run = conn.execute("SELECT * FROM remediation_runs WHERE case_id=? "
                       "ORDER BY started_at DESC LIMIT 1", (case_id,)).fetchone()
    if run:
        card["action"] = run["script_id"]
        before, after = json.loads(run["before_state"] or "{}"), json.loads(run["after_state"] or "{}")
        card["before"] = {k: before.get(k) for k in ("cpu_pct", "ram_pct", "teams_mb") if k in before}
        card["after"] = {k: after.get(k) for k in ("cpu_pct", "ram_pct", "teams_mb") if k in after}
        verification = json.loads(run["verification_result"] or "{}")
        card["verification"] = "PASS" if verification.get("passed") else ("FAIL" if verification else "")
    else:
        card["action"] = ""
        card["before"], card["after"], card["verification"] = {}, {}, ""
    incident = conn.execute("SELECT * FROM incidents WHERE case_id=? "
                            "ORDER BY created_at LIMIT 1", (case_id,)).fetchone()
    card["servicenow"] = incident["incident_id"] if incident else ""
    card["status"] = ("RESOLVED" if incident and incident["resolved_at"]
                      else "ESCALATED" if incident and incident["priority"] == "1"
                      else "OPEN" if incident else "")
    fleet = conn.execute("SELECT match_state, COUNT(*) AS n, SUM(verified) AS v "
                         "FROM fleet_matches WHERE case_id=? GROUP BY match_state",
                         (case_id,)).fetchall()
    card["fleet_matching"] = sum(r["n"] for r in fleet)
    card["fleet_healed"] = sum(r["v"] or 0 for r in fleet)
    prevented = conn.execute("SELECT value FROM metrics WHERE case_id=? AND name='prevented'",
                             (case_id,)).fetchone()
    card["fleet_prevented"] = int(prevented["value"]) if prevented else 0
    return card
