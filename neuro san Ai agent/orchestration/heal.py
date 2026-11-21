"""Proactive fleet healing (M24): matches → healed devices + Problem record.

Consumes M23 scans. Auto bucket executes+verifies per device (each gated
again at execution time — classify-then-act is never assumed). Approval
bucket files human gates without touching devices. Blocked bucket is
reported, never forced. Prevented-ticket math is honest: verified-healed
devices minus the already-reported originating device.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from control_plane import approvals
from control_plane.execution import EXECUTED, request_execution
from control_plane.rollback import VERIFIED, verify_and_recover
from integrations.ports import ITSMProvider
from orchestration.fleet import AUTO, BLOCKED, NEEDS_APPROVAL, FleetScan, scan_fleet


@dataclass
class HealReport:
    signature: str
    scanned: int = 0
    matching: int = 0
    healed: list[str] = field(default_factory=list)
    failed: list[dict[str, str]] = field(default_factory=list)
    approval: list[dict[str, str]] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    problem_number: str = ""
    problem_sys_id: str = ""
    prevented: int = 0
    originating_device: str = ""


def heal_fleet(conn: sqlite3.Connection, estate: Any, itsm: ITSMProvider,
               case_id: str, root_cause: str, action_id: str,
               evidence: list[dict[str, Any]] | None = None,
               originating_device: str = "",
               originating_incident_sys_id: str = "",
               requested_by: str = "fleet-healer") -> HealReport:
    """Execute the M23 scan to verified healing + Problem record."""
    scan: FleetScan = scan_fleet(conn, estate, case_id, root_cause, action_id, evidence)
    from evidence.store import ensure_case
    ensure_case(conn, case_id)
    report = HealReport(signature=scan.signature, scanned=scan.scanned,
                        matching=scan.matching, originating_device=originating_device)

    for device_id in scan.auto:
        subcase = f"{case_id}:{device_id}"
        executed = request_execution(conn, estate, subcase, action_id, device_id,
                                     estate.get(device_id).user_id)
        if executed.status != EXECUTED:
            report.failed.append({"device_id": device_id, "reason": "; ".join(executed.reasons)})
            continue
        recovered = verify_and_recover(conn, estate, executed.run_id, subcase)
        if recovered["outcome"] == VERIFIED:
            report.healed.append(device_id)
            conn.execute("UPDATE fleet_matches SET remediation_run_id=?, verified=1 "
                         "WHERE match_id=?", (executed.run_id, f"FM-{case_id}-{device_id}"))
        else:
            report.failed.append({"device_id": device_id,
                                  "reason": f"verify: {recovered['outcome']}"})
    conn.commit()

    for device_id in scan.approval:
        gate = approvals.request_approval(conn, f"{case_id}:{device_id}", action_id,
                                          requested_by)
        report.approval.append({"device_id": device_id, "approval_id": gate["approval_id"]})
    report.blocked = list(scan.blocked)

    healed_others = [d for d in report.healed if d != originating_device]
    report.prevented = len(healed_others)

    from metrics.compute import record_case_metrics
    record_case_metrics(conn, case_id, "healed", float(len(report.healed)))
    record_case_metrics(conn, case_id, "prevented", float(report.prevented))
    record_case_metrics(conn, case_id, "matching", float(scan.matching))

    description = (f"Root cause: {root_cause} | remediation: {action_id} | "
                   f"scanned={scan.scanned} matching={scan.matching} "
                   f"healed={len(report.healed)} approval={len(report.approval)} "
                   f"blocked={len(report.blocked)} prevented={report.prevented}")
    problem = itsm.create_problem(f"Fleet pattern: {root_cause}", description)
    report.problem_number, report.problem_sys_id = problem.number, problem.sys_id
    if originating_incident_sys_id:
        try:
            itsm.link_incident_to_problem(originating_incident_sys_id, problem.sys_id)
        except (LookupError, ValueError):
            pass
    return report
