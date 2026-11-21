"""Learning + ServiceNow coded tools (M7).

Learning: SQLite-backed pattern store on the M2 workflow tables. Candidates
are FORCED to approval_state='candidate' — self-promotion is impossible here
(full promotion pipeline lands in M21).

ServiceNow: simulated ITSM by default (use_mock=True); the live PDI path
wires in M18. Same signatures either way.
"""

from __future__ import annotations

import time
from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.digital_workplace._ctx import get_bundle


def _db():
    from common.config import load_settings
    from database.bootstrap import get_connection, init_db
    db_path = load_settings(env_file=".env").db_path
    init_db(db_path)
    return get_connection(db_path)


# ------------------------------------------------------------- learning

class RecordResolutionPattern(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from control_plane.learning import record_resolution

        run_id = f"RUN-{int(time.time() * 1000) % 100000:05d}"
        case_id = str(args.get("case_id", sly_data.get("case_id", "")))
        signature = str(args.get("failure_signature", "unknown"))
        success = bool(args.get("success", True))
        conn = _db()
        try:
            conn.execute(
                "INSERT INTO workflow_runs(run_id, workflow_id, case_id, success) "
                "VALUES (?,?,?,?)", (run_id, signature, case_id, int(success)))
            conn.commit()
            pattern_id = record_resolution(
                conn, case_id, signature,
                [str(e) for e in args.get("evidence_pattern", [])],
                str(args.get("root_cause", "")), str(args.get("action_id", "")),
                policy_result=str(args.get("policy_result", "")),
                approval_state=str(args.get("approval_state", "")),
                verification_passed=bool(args.get("verification_passed", success)),
                success=success, reopen=bool(args.get("reopen", False)))
            return {"recorded": True, "run_id": run_id, "pattern_id": pattern_id}
        finally:
            conn.close()


class DetectWorkflowPattern(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from control_plane.learning import detect_candidates

        try:
            min_occurrences = int(args.get("min_occurrences", 3))
        except (TypeError, ValueError):
            min_occurrences = 3
        conn = _db()
        try:
            return {"candidates": detect_candidates(conn, min_occurrences)}
        finally:
            conn.close()


class CreateWorkflowCandidate(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from control_plane.learning import propose_candidate

        conn = _db()
        try:
            row = propose_candidate(conn, str(args.get("failure_signature", "")),
                                    str(args.get("action_id", "")),
                                    root_cause=str(args.get("root_cause", "")),
                                    name=str(args.get("name", "")),
                                    workflow_id=str(args.get("workflow_id", "")))
            return {"workflow_id": row["workflow_id"], "approval_state": "candidate",
                    "note": "requires human approval before use (M21)"}
        finally:
            conn.close()


class SearchWorkflowRegistry(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        signature = str(args.get("failure_signature", ""))
        conn = _db()
        try:
            rows = conn.execute(
                "SELECT workflow_id, name, version, action_id, autonomy_level, "
                "approval_state FROM workflows WHERE failure_signature LIKE ?",
                (f"%{signature}%",)).fetchall()
            return {"workflows": [dict(r) for r in rows]}
        finally:
            conn.close()


class GetWorkflowStatistics(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        workflow_id = str(args.get("workflow_id", ""))
        conn = _db()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS runs, SUM(success) AS wins FROM workflow_runs "
                "WHERE workflow_id=?", (workflow_id,)).fetchone()
            runs, wins = (row["runs"] or 0), (row["wins"] or 0)
            return {"workflow_id": workflow_id, "runs": runs,
                    "success_rate": round(wins / runs, 3) if runs else 0.0}
        finally:
            conn.close()


# ------------------------------------------------------------- servicenow

def _itsm(seed_args: dict[str, Any]):
    try:
        seed = int(seed_args.get("seed", 42))
    except (TypeError, ValueError):
        seed = 42
    return get_bundle(seed).itsm


class CreateIncident(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from integrations.ports import IncidentDTO
        dto: IncidentDTO = _itsm(args).create_incident(  # type: ignore[union-attr]
            str(args.get("short_description", "")),
            description=str(args.get("description", "")))
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state}


class GetIncident(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        dto = _itsm(args).get_incident(str(args.get("sys_id", "")))  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state,
                "short_description": dto.short_description}


class SearchIncidents(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        try:
            limit = int(args.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        results = _itsm(args).search_incidents(str(args.get("query", "")), limit)  # type: ignore[union-attr]
        return {"incidents": [{"sys_id": r.sys_id, "number": r.number,
                               "state": r.state} for r in results]}


class AddWorkNote(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        dto = _itsm(args).add_work_note(str(args.get("sys_id", "")), str(args.get("note", "")))  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state}


class UpdateIncident(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        fields = {k: v for k, v in args.items() if k not in ("sys_id", "seed")}
        dto = _itsm(args).update_incident(str(args.get("sys_id", "")), fields)  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state}


class ResolveIncident(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        dto = _itsm(args).resolve_incident(str(args.get("sys_id", "")), str(args.get("close_notes", "")))  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state}


class EscalateIncident(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        dto = _itsm(args).escalate_incident(str(args.get("sys_id", "")), str(args.get("note", "")))  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state}


class CreateProblem(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        dto = _itsm(args).create_problem(str(args.get("short_description", "")), str(args.get("description", "")))  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number}


class LinkIncidentToProblem(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        dto = _itsm(args).link_incident_to_problem(str(args.get("incident_sys_id", "")), str(args.get("problem_sys_id", "")))  # type: ignore[union-attr]
        return {"sys_id": dto.sys_id, "number": dto.number, "state": dto.state}
