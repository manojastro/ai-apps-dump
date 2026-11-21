"""ServiceNow lifecycle composer (M18): case outcomes → ITSM records.

Runs on any ITSMProvider (simulated today, live PDI when env creds exist —
factory decides, callers never branch). Hard rule: resolve_verified REFUSES
unless verification passed. Local incidents rows mirror ITSM state for the
dashboard and audit trail.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from database.models import utcnow
from evidence.store import ensure_case
from integrations.ports import IncidentDTO, ITSMProvider, ProblemDTO


def open_incident(itsm: ITSMProvider, conn: sqlite3.Connection, case_id: str,
                  short_description: str, description: str = "") -> IncidentDTO:
    """Idempotent per case: existing row is reused, never duplicated."""
    ensure_case(conn, case_id)
    row = conn.execute("SELECT incident_id FROM incidents WHERE case_id=? "
                       "ORDER BY created_at LIMIT 1", (case_id,)).fetchone()
    if row is not None:
        try:
            return itsm.get_incident(row["servicenow_sys_id"] or row["incident_id"])
        except Exception:
            # Refresh is best-effort; the local row dedupes either way.
            existing = dict(row)
            return IncidentDTO(sys_id=existing.get("servicenow_sys_id", ""),
                               number=existing.get("incident_id", ""),
                               state=existing.get("state", ""))
    created = itsm.create_incident(short_description, description)
    conn.execute(
        "INSERT INTO incidents(incident_id, case_id, servicenow_sys_id, state, "
        "short_description) VALUES (?,?,?,?,?)",
        (created.number, case_id, created.sys_id, created.state, short_description))
    conn.commit()
    return created


def note_investigation(itsm: ITSMProvider, incident_sys_id: str,
                       agents: list[str], tools: list[str],
                       hypotheses: list[dict[str, Any]], confidence: float) -> None:
    lines = [f"Agents: {', '.join(agents)}", f"Tools: {', '.join(tools)}"]
    for hyp in hypotheses:
        lines.append(f"{hyp.get('title')}: {hyp.get('confidence')}% {hyp.get('status')}")
    lines.append(f"Top confidence: {confidence}%")
    itsm.add_work_note(incident_sys_id, "Investigation trace — " + " | ".join(lines))


def resolve_verified(itsm: ITSMProvider, conn: sqlite3.Connection, case_id: str,
                     verification: dict[str, Any], close_notes: str) -> IncidentDTO:
    """Resolve ONLY on passed verification. Anything else raises."""
    if not verification.get("passed"):
        failed = verification.get("failed", verification.get("checks", []))
        raise ValueError(f"refusing to resolve {case_id} without passed verification "
                         f"(failed={failed})")
    row = conn.execute("SELECT * FROM incidents WHERE case_id=? ORDER BY created_at LIMIT 1",
                       (case_id,)).fetchone()
    if row is None:
        raise LookupError(f"no incident for case {case_id}")
    incident = dict(row)
    sys_id = incident["servicenow_sys_id"] or incident["incident_id"]
    itsm.add_work_note(sys_id, f"Verification passed — {close_notes}")
    resolved = itsm.resolve_incident(sys_id, close_notes)
    conn.execute("UPDATE incidents SET state=?, resolved_at=? WHERE incident_id=?",
                 (resolved.state, utcnow(), incident["incident_id"]))
    conn.commit()
    return resolved


def escalate_recovery(itsm: ITSMProvider, conn: sqlite3.Connection, case_id: str,
                      reason: str, failed: list[str],
                      rollback_info: str = "") -> IncidentDTO:
    """Escalate after rollback or unrecoverable failure, with the full trail."""
    row = conn.execute("SELECT * FROM incidents WHERE case_id=? ORDER BY created_at LIMIT 1",
                       (case_id,)).fetchone()
    if row is None:
        raise LookupError(f"no incident for case {case_id}")
    incident = dict(row)
    sys_id = incident["servicenow_sys_id"] or incident["incident_id"]
    note = f"{reason} | failed={failed} | rollback={rollback_info or 'n/a'}"
    itsm.add_work_note(sys_id, note)
    escalated = itsm.escalate_incident(sys_id, note)
    conn.execute("UPDATE incidents SET state=?, priority='1', updated_at=? WHERE incident_id=?",
                 (escalated.state, utcnow(), incident["incident_id"]))
    conn.commit()
    return escalated


def open_problem(itsm: ITSMProvider, conn: sqlite3.Connection, short_description: str,
                 description: str, incident_sys_ids: list[str]) -> ProblemDTO:
    """Fleet-wide pattern → problem record with linked incidents."""
    problem = itsm.create_problem(short_description, description)
    for sys_id in incident_sys_ids:
        try:
            itsm.link_incident_to_problem(sys_id, problem.sys_id)
        except (LookupError, ValueError):
            continue
    return problem
