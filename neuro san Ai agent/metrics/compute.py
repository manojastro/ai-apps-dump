"""KPI dashboard metrics (M27): every number computed from recorded rows.

Estimates (engineer minutes, cost) multiply computed counts by documented
constants — the counts are real, the rates are labeled estimates.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

ENGINEER_MIN_PER_HEALED = 20
ENGINEER_MIN_PER_AUTO_INCIDENT = 30
COST_PER_MINUTE_USD = 1.5


def _count(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return conn.execute(sql, params).fetchone()[0]


def compute_metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    """Full KPI set from live tables. No constants except labeled estimates."""
    cases = _count(conn, "SELECT COUNT(*) FROM cases")
    technical = _count(conn, "SELECT COUNT(DISTINCT case_id) FROM evidence")
    knowledge = _count(conn,
        "SELECT COUNT(DISTINCT case_id) FROM audit_events WHERE agent='knowledge_agent' "
        "AND case_id NOT IN (SELECT DISTINCT case_id FROM evidence)")
    resolved = _count(conn, "SELECT COUNT(*) FROM incidents WHERE resolved_at != ''")
    escalated = _count(conn, "SELECT COUNT(*) FROM incidents WHERE priority='1'")
    approved_gate = _count(conn, "SELECT COUNT(*) FROM approvals WHERE state='APPROVED'")
    resolved_no_gate = _count(conn,
        "SELECT COUNT(*) FROM incidents WHERE resolved_at != '' AND case_id NOT IN "
        "(SELECT DISTINCT case_id FROM approvals WHERE state='APPROVED')")
    runs = _count(conn, "SELECT COUNT(*) FROM remediation_runs WHERE run_id NOT LIKE '%-RB'")
    run_wins = _count(conn, "SELECT COUNT(*) FROM remediation_runs WHERE success=1 AND run_id NOT LIKE '%-RB'")
    verified = _count(conn, "SELECT COUNT(*) FROM remediation_runs WHERE verification_result LIKE '%\"passed\": true%'")
    verify_attempts = _count(conn, "SELECT COUNT(*) FROM remediation_runs WHERE verification_result != ''")
    rollbacks = _count(conn, "SELECT COUNT(*) FROM remediation_runs WHERE rollback_run_id != ''")
    reopens = _count(conn, "SELECT COALESCE(SUM(reopen),0) FROM resolution_patterns")
    denies = _count(conn, "SELECT COUNT(*) FROM policy_decisions WHERE decision='DENY'")
    supported = _count(conn, "SELECT COUNT(*) FROM hypotheses WHERE status='SUPPORTED'")
    hyps = _count(conn, "SELECT COUNT(*) FROM hypotheses")
    wf_runs = _count(conn, "SELECT COUNT(*) FROM workflow_runs")
    wf_wins = _count(conn, "SELECT COUNT(*) FROM workflow_runs WHERE success=1")
    approved_wf = _count(conn, "SELECT COUNT(*) FROM workflows WHERE approval_state='approved'")
    candidates = _count(conn, "SELECT COUNT(*) FROM workflows WHERE approval_state='candidate'")
    healed = _count(conn, "SELECT COUNT(DISTINCT device_id) FROM fleet_matches WHERE verified=1")
    prevented_rows = conn.execute("SELECT value FROM metrics WHERE name='prevented'").fetchall()
    prevented = int(sum(r[0] for r in prevented_rows))
    durations = []
    for row in conn.execute("SELECT created_at, resolved_at FROM incidents WHERE resolved_at != ''"):
        try:
            start = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            end = datetime.fromisoformat(row[1].replace("Z", "+00:00"))
            durations.append((end - start).total_seconds())
        except (TypeError, ValueError):
            continue
    minutes = healed * ENGINEER_MIN_PER_HEALED + resolved_no_gate * ENGINEER_MIN_PER_AUTO_INCIDENT
    return {
        "requests_handled": cases,
        "technical_cases": technical,
        "knowledge_cases": knowledge,
        "evidence_cases": technical,
        "auto_resolved": resolved_no_gate,
        "human_approved": approved_gate,
        "escalated": escalated,
        "incidents_resolved": resolved,
        "automation_rate": round(resolved_no_gate / resolved, 3) if resolved else 0.0,
        "rca_supported_share": round(supported / hyps, 3) if hyps else 0.0,
        "remediation_runs": runs,
        "remediation_success_rate": round(run_wins / runs, 3) if runs else 0.0,
        "verification_rate": round(verified / verify_attempts, 3) if verify_attempts else 0.0,
        "rollbacks": rollbacks,
        "reopened": reopens,
        "policy_denies": denies,
        "workflow_runs": wf_runs,
        "workflow_success_rate": round(wf_wins / wf_runs, 3) if wf_runs else 0.0,
        "approved_workflows": approved_wf,
        "workflow_candidates": candidates,
        "healed_devices": healed,
        "tickets_prevented": prevented,
        "avg_resolution_seconds": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "engineer_minutes_saved_estimate": minutes,
        "cost_saved_usd_estimate": round(minutes * COST_PER_MINUTE_USD, 2),
    }


def render_markdown(metrics: dict[str, Any]) -> str:
    lines = ["# KPI dashboard (computed, never staged)", ""]
    for key, value in metrics.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def record_case_metrics(conn: sqlite3.Connection, case_id: str, name: str, value: float) -> None:
    conn.execute("INSERT INTO metrics(metric_id, name, value, case_id) VALUES (?,?,?,?)",
                 (f"{name}-{case_id}", name, value, case_id))
    conn.commit()
