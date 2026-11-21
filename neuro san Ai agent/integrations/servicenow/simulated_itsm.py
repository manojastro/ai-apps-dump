"""Simulated ITSM (M4): deterministic in-memory PDI for demo/eval.

Used when live ServiceNow creds are absent (user decision: simulated data).
Same ITSMProvider interface as the real adapter — swap via factory with
zero caller changes. No network, no credentials, seeded numbering.
"""

from __future__ import annotations

from typing import Any

from integrations.ports import IncidentDTO, ProblemDTO


class SimulatedITSM:
    source = "simulated-servicenow"

    def __init__(self, seed: int = 42) -> None:
        self._n = int(seed) % 1000
        self._incidents: dict[str, dict[str, Any]] = {}
        self._problems: dict[str, dict[str, Any]] = {}

    def _next(self, prefix: str) -> tuple[str, str]:
        self._n += 1
        return f"SIM{self._n:06d}", f"{prefix}{1000 + self._n:07d}"

    @staticmethod
    def _incident_dto(record: dict[str, Any]) -> IncidentDTO:
        return IncidentDTO(sys_id=record["sys_id"], number=record["number"],
                           state=record["state"],
                           short_description=record.get("short_description", ""))

    def create_incident(self, short_description: str, description: str = "",
                        caller_id: str = "") -> IncidentDTO:
        if not short_description.strip():
            raise ValueError("short_description is required")
        sid, num = self._next("INC")
        record = {"sys_id": sid, "number": num, "state": "New",
                  "short_description": short_description,
                  "description": description, "caller_id": caller_id,
                  "work_notes": [], "problem_id": ""}
        self._incidents[sid] = record
        return self._incident_dto(record)

    def get_incident(self, sys_id: str) -> IncidentDTO:
        try:
            return self._incident_dto(self._incidents[sys_id])
        except KeyError:
            raise LookupError(f"incident {sys_id} not found") from None

    def search_incidents(self, query: str, limit: int = 20) -> list[IncidentDTO]:
        rows = list(self._incidents.values())
        if query.startswith("number="):
            rows = [r for r in rows if r["number"] == query.split("=", 1)[1]]
        elif query:
            rows = [r for r in rows if query.lower() in
                    r.get("short_description", "").lower()]
        return [self._incident_dto(r) for r in rows[:limit]]

    def update_incident(self, sys_id: str, fields: dict[str, Any]) -> IncidentDTO:
        record = self._incidents.get(sys_id)
        if record is None:
            raise LookupError(f"incident {sys_id} not found")
        allowed = {"state", "priority", "work_notes", "close_code",
                   "close_notes", "problem_id", "short_description",
                   "description", "assignment_group"}
        rejected = sorted(set(fields) - allowed)
        if rejected:
            raise ValueError(f"refusing fields: {rejected}")
        for key, value in fields.items():
            if key == "work_notes":
                record["work_notes"].append(str(value))
            else:
                record[key] = value
        return self._incident_dto(record)

    def add_work_note(self, sys_id: str, note: str) -> IncidentDTO:
        if not note.strip():
            raise ValueError("work note text is required")
        return self.update_incident(sys_id, {"work_notes": note})

    def resolve_incident(self, sys_id: str, close_notes: str) -> IncidentDTO:
        if not close_notes.strip():
            raise ValueError("close_notes required (no silent resolves)")
        record = self.update_incident(sys_id, {
            "state": "6", "close_code": "Solved remotely",
            "close_notes": close_notes,
            "work_notes": f"Resolved: {close_notes}"})
        return record

    def escalate_incident(self, sys_id: str, note: str) -> IncidentDTO:
        if not note.strip():
            raise ValueError("escalation note is required")
        return self.update_incident(sys_id, {
            "priority": "1", "work_notes": f"Escalated (P1): {note}"})

    def create_problem(self, short_description: str, description: str = "") -> ProblemDTO:
        if not short_description.strip():
            raise ValueError("short_description is required")
        sid, num = self._next("PRB")
        record = {"sys_id": sid, "number": num, "state": "New",
                  "short_description": short_description,
                  "description": description, "work_notes": []}
        self._problems[sid] = record
        return ProblemDTO(sys_id=sid, number=num, state="New",
                          short_description=short_description)

    def link_incident_to_problem(self, incident_sys_id: str, problem_sys_id: str) -> IncidentDTO:
        if problem_sys_id not in self._problems:
            raise LookupError(f"problem {problem_sys_id} not found")
        dto = self.update_incident(incident_sys_id, {"problem_id": problem_sys_id})
        self._problems[problem_sys_id]["work_notes"].append(
            f"Linked incident {dto.number}")
        return dto
