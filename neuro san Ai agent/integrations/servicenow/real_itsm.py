"""Real ITSM adapter: ITSMProvider over the M3 Table API client."""

from __future__ import annotations

from typing import Any

from integrations.ports import IncidentDTO, ProblemDTO
from integrations.servicenow import incidents as ops
from integrations.servicenow.client import ServiceNowClient


def _incident_dto(record: dict[str, Any]) -> IncidentDTO:
    return IncidentDTO(sys_id=str(record.get("sys_id", "")),
                       number=str(record.get("number", "")),
                       state=str(record.get("state", "")),
                       short_description=str(record.get("short_description", "")))


def _problem_dto(record: dict[str, Any]) -> ProblemDTO:
    return ProblemDTO(sys_id=str(record.get("sys_id", "")),
                      number=str(record.get("number", "")),
                      state=str(record.get("state", "")),
                      short_description=str(record.get("short_description", "")))


class RealServiceNowITSM:
    """ITSMProvider backed by a live PDI. Requires env creds (M3)."""

    source = "servicenow-table-api"

    def __init__(self, client: ServiceNowClient) -> None:
        self._client = client

    def create_incident(self, short_description: str, description: str = "",
                        caller_id: str = "") -> IncidentDTO:
        return _incident_dto(ops.create_incident(
            self._client, short_description, description=description,
            caller_id=caller_id))

    def get_incident(self, sys_id: str) -> IncidentDTO:
        return _incident_dto(ops.get_incident(self._client, sys_id))

    def search_incidents(self, query: str, limit: int = 20) -> list[IncidentDTO]:
        return [_incident_dto(r) for r in
                ops.search_incidents(self._client, query, limit=limit)]

    def update_incident(self, sys_id: str, fields: dict[str, Any]) -> IncidentDTO:
        return _incident_dto(ops.update_incident(self._client, sys_id, fields))

    def add_work_note(self, sys_id: str, note: str) -> IncidentDTO:
        return _incident_dto(ops.add_work_note(self._client, sys_id, note))

    def resolve_incident(self, sys_id: str, close_notes: str) -> IncidentDTO:
        return _incident_dto(ops.resolve_incident(self._client, sys_id, close_notes))

    def escalate_incident(self, sys_id: str, note: str) -> IncidentDTO:
        return _incident_dto(ops.escalate_incident(self._client, sys_id, note))

    def create_problem(self, short_description: str, description: str = "") -> ProblemDTO:
        return _problem_dto(ops.create_problem(
            self._client, short_description, description=description))

    def link_incident_to_problem(self, incident_sys_id: str, problem_sys_id: str) -> IncidentDTO:
        return _incident_dto(ops.link_incident_to_problem(
            self._client, incident_sys_id, problem_sys_id))
