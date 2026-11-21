"""Incident/problem operations on the Table API (M3).

No Scripted REST. Problem linking uses the standard PDI
`incident.problem_id` reference + a problem work note (assumption
documented in BUILD_STATE M3; revisit only if a PDI proves otherwise).

All functions take explicit business params — credentials are NEVER
parameters (they live in ServiceNowClient config from env).
"""

from __future__ import annotations

from typing import Any

from common.logging_setup import get_logger
from .client import ServiceNowClient

logger = get_logger(__name__)

INCIDENT_TABLE = "incident"
PROBLEM_TABLE = "problem"

_SAFE_INCIDENT_FIELDS = ("sys_id", "number", "state", "priority", "urgency",
                         "impact", "short_description", "description",
                         "work_notes", "close_code", "close_notes",
                         "problem_id", "assignment_group", "assigned_to")
_SAFE_PROBLEM_FIELDS = ("sys_id", "number", "state", "short_description",
                        "description", "work_notes")

# Guardrail: LLM/coded tools may only write these incident fields.
WRITABLE_INCIDENT_FIELDS = frozenset({
    "state", "priority", "urgency", "impact", "assignment_group",
    "assigned_to", "work_notes", "comments", "close_code", "close_notes",
    "problem_id", "short_description", "description", "category",
    "caller_id",
})

RESOLVED_STATE = "6"  # PDI default Resolved


def _pick(record: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {k: record.get(k, "") for k in keys if k in record or k in
            ("sys_id", "number", "state")}


def _filtered(fields: dict[str, Any]) -> dict[str, Any]:
    rejected = sorted(set(fields) - WRITABLE_INCIDENT_FIELDS)
    if rejected:
        raise ValueError(f"refusing to write non-allowlisted fields: {rejected}")
    return dict(fields)


def create_incident(client: ServiceNowClient, short_description: str,
                    description: str = "", caller_id: str = "",
                    category: str = "", urgency: str = "3",
                    impact: str = "3") -> dict[str, Any]:
    if not short_description.strip():
        raise ValueError("short_description is required")
    body: dict[str, Any] = {"short_description": short_description,
                            "urgency": urgency, "impact": impact}
    if description:
        body["description"] = description
    if caller_id:
        body["caller_id"] = caller_id
    if category:
        body["category"] = category
    record = client.create(INCIDENT_TABLE, _filtered(body))
    logger.debug("snow incident created %s", record.get("number", "?"))
    return _pick(record, _SAFE_INCIDENT_FIELDS)


def get_incident(client: ServiceNowClient, sys_id: str) -> dict[str, Any]:
    return _pick(client.get(INCIDENT_TABLE, sys_id), _SAFE_INCIDENT_FIELDS)


def search_incidents(client: ServiceNowClient, query: str,
                     limit: int = 20) -> list[dict[str, Any]]:
    records = client.list(INCIDENT_TABLE, query_str=query, limit=limit)
    return [_pick(r, _SAFE_INCIDENT_FIELDS) for r in records]


def update_incident(client: ServiceNowClient, sys_id: str,
                    fields: dict[str, Any]) -> dict[str, Any]:
    record = client.update(INCIDENT_TABLE, sys_id, _filtered(fields))
    return _pick(record, _SAFE_INCIDENT_FIELDS)


def add_work_note(client: ServiceNowClient, sys_id: str,
                  note: str) -> dict[str, Any]:
    if not note.strip():
        raise ValueError("work note text is required")
    return update_incident(client, sys_id, {"work_notes": note})


def resolve_incident(client: ServiceNowClient, sys_id: str,
                     close_notes: str,
                     close_code: str = "Solved remotely") -> dict[str, Any]:
    if not close_notes.strip():
        raise ValueError("close_notes required to resolve (no silent resolves)")
    return update_incident(client, sys_id, {
        "state": RESOLVED_STATE, "close_code": close_code,
        "close_notes": close_notes,
        "work_notes": f"Resolved: {close_notes}",
    })


def escalate_incident(client: ServiceNowClient, sys_id: str, note: str,
                      priority: str = "1") -> dict[str, Any]:
    if not note.strip():
        raise ValueError("escalation note is required")
    return update_incident(client, sys_id, {
        "priority": priority, "urgency": "1",
        "work_notes": f"Escalated (P{priority}): {note}",
    })


def create_problem(client: ServiceNowClient, short_description: str,
                   description: str = "") -> dict[str, Any]:
    if not short_description.strip():
        raise ValueError("short_description is required")
    body: dict[str, Any] = {"short_description": short_description}
    if description:
        body["description"] = description
    record = client.create(PROBLEM_TABLE, body)
    logger.debug("snow problem created %s", record.get("number", "?"))
    return _pick(record, _SAFE_PROBLEM_FIELDS)


def link_incident_to_problem(client: ServiceNowClient, incident_sys_id: str,
                             problem_sys_id: str) -> dict[str, Any]:
    record = update_incident(client, incident_sys_id,
                             {"problem_id": problem_sys_id})
    try:
        client.update(PROBLEM_TABLE, problem_sys_id, {
            "work_notes": f"Linked incident {record.get('number', incident_sys_id)}"})
    except Exception as e:  # linking must not hide the incident update
        logger.debug("snow problem work-note failed: %s", type(e).__name__)
    return record
