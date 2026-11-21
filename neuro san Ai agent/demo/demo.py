"""End-to-end demo scenarios (M28). Deterministic per (scenario, seed).

Usage: python -m demo.demo --scenario laptop_teams_memory --seed 42 [--db PATH]
Scenarios: laptop_teams_memory, vpn_stale_token, learning_loop, knowledge_security.
Composition only — every step calls tested M0-M27 building blocks.
"""

from __future__ import annotations

import argparse
from typing import Any

from common.neuro_stub import ensure_stub

ensure_stub()

SCENARIOS = ("laptop_teams_memory", "vpn_stale_token", "learning_loop", "knowledge_security")


def _setup(db_path: str, seed: int):
    from control_plane import registry as reg
    from database.bootstrap import get_connection, init_db
    from integrations.servicenow.simulated_itsm import SimulatedITSM
    from simulator.estate import generate_estate
    init_db(db_path)
    conn = get_connection(db_path)
    reg.seed_registry(conn)
    return conn, generate_estate(seed=seed), SimulatedITSM(seed=seed + 1)


def laptop_teams_memory(db_path: str, seed: int = 42) -> dict[str, Any]:
    from audit.timeline import build_final_card
    from control_plane import learning
    from control_plane.execution import request_execution
    from control_plane import registry as reg
    from control_plane.rollback import verify_and_recover
    from evidence.store import list_evidence
    from integrations.servicenow import lifecycle
    from metrics.compute import compute_metrics
    from orchestration.heal import heal_fleet
    from orchestration.investigate import investigate_sync

    case = "DEMO-LAPTOP"
    conn, estate, itsm = _setup(db_path, seed)
    try:
        inv = investigate_sync("My laptop is extremely slow and Teams keeps freezing.",
                               "DEVICE_001", "USER_001", seed, case, db_path)
        assert inv.verdict == "PROCEED"
        root = inv.hypotheses[0]["title"]
        incident = lifecycle.open_incident(itsm, conn, case, "Teams freezing")
        lifecycle.note_investigation(itsm, incident.sys_id, inv.agents_involved,
                                     inv.tools_consulted, inv.hypotheses, inv.confidence)
        action = reg.find_approved_action(conn, root)["script_id"]
        executed = request_execution(conn, estate, case, action, "DEVICE_001", "USER_001")
        assert executed.status == "executed"
        recovered = verify_and_recover(conn, estate, executed.run_id, case)
        assert recovered["outcome"] == "verified"
        lifecycle.resolve_verified(itsm, conn, case, {"passed": True}, "cache cleared, telemetry healthy")
        learning.record_resolution(conn, case, "teams_memory",
                                   [e["measurement"] for e in list_evidence(conn, case)],
                                   root, action, policy_result="ALLOW", approval_state="auto",
                                   verification_passed=True, success=True)
        healed = heal_fleet(conn, estate, itsm, case, root, action,
                            list_evidence(conn, case), originating_device="DEVICE_001",
                            originating_incident_sys_id=incident.sys_id)
        card = build_final_card(conn, case)
        summary = {"scenario": "laptop_teams_memory", "verdict": inv.verdict,
                   "root_cause": root, "action": action, "incident": incident.number,
                   "healed": len(healed.healed), "prevented": healed.prevented,
                   "problem": healed.problem_number, "metrics": compute_metrics(conn),
                   "card": card}
        print(f"ISSUE laptop slow | RCA {root} {inv.confidence}% | ACTION {action} | "
              f"VERIFY PASS | {incident.number} RESOLVED | fleet {healed.matching} scanned, "
              f"{len(healed.healed)} healed, {healed.prevented} prevented | {healed.problem_number}")
        return summary
    finally:
        conn.close()


def vpn_stale_token(db_path: str, seed: int = 42) -> dict[str, Any]:
    from control_plane import approvals
    from control_plane.execution import request_execution
    from control_plane import registry as reg
    from control_plane.rollback import verify_and_recover
    from integrations.servicenow import lifecycle
    from orchestration.investigate import investigate_sync

    case = "DEMO-VPN"
    conn, estate, itsm = _setup(db_path, seed)
    try:
        inv = investigate_sync("I changed my password and now my VPN will not connect.",
                               "DEVICE_002", "USER_002", seed, case, db_path)
        incident = lifecycle.open_incident(itsm, conn, case, "VPN down after password change")
        action = reg.find_approved_action(conn, inv.hypotheses[0]["title"])["script_id"]
        first = request_execution(conn, estate, case, action, "DEVICE_002", "USER_002")
        human = "NONE"
        if first.status == "awaiting_approval":
            human = "demo-manager (playing the human approver)"
            approvals.approve(conn, first.approval_id, "demo-manager")
            first = request_execution(conn, estate, case, action, "DEVICE_002", "USER_002")
        assert first.status == "executed"
        recovered = verify_and_recover(conn, estate, first.run_id, case)
        assert recovered["outcome"] == "verified"
        lifecycle.resolve_verified(itsm, conn, case, {"passed": True}, "token refreshed, vpn up")
        print(f"ISSUE vpn down | RCA stale token | ACTION {action} | approval by {human} | "
              f"VERIFY PASS | {incident.number} RESOLVED")
        return {"scenario": "vpn_stale_token", "action": action, "human": human,
                "incident": incident.number}
    finally:
        conn.close()


def learning_loop(db_path: str, seed: int = 42) -> dict[str, Any]:
    from control_plane import approvals, learning
    from orchestration.replay import try_known_workflow

    case = "DEMO-LEARN"
    conn, estate, _itsm = _setup(db_path, seed)
    try:
        for i in range(3):
            learning.record_resolution(
                conn, f"{case}-{i}", "teams_memory", ["ram", "process_memory"],
                "Teams excessive memory after update", "SCR-018",
                policy_result="ALLOW", approval_state="APPROVED",
                verification_passed=True, success=True)
        found = learning.detect_candidates(conn)
        assert len(found) == 1
        candidate = learning.propose_candidate(conn, "teams_memory", "SCR-018",
                                               "Teams excessive memory after update")
        try:
            learning.promote_candidate(conn, candidate["workflow_id"])
        except ValueError:
            pass
        gate = approvals.latest_for(conn, "", candidate["workflow_id"])
        approvals.approve(conn, gate["approval_id"], "demo-manager")
        assert learning.promote_candidate(conn, candidate["workflow_id"])["approval_state"] == "approved"
        # Earn L3 the honest way: approvals then successful runs.
        for i in range(2):
            approvals.request_approval(conn, f"{case}-ap{i}", candidate["workflow_id"], "commander")
            row = approvals.pending_for(conn, f"{case}-ap{i}", candidate["workflow_id"])
            approvals.approve(conn, row["approval_id"], "demo-manager")
        assert learning.sync_autonomy(conn, candidate["workflow_id"])["recommended"] == "L2"
        for i in range(10):
            learning.record_workflow_run(conn, candidate["workflow_id"], f"{case}-r{i}",
                                         "ALLOW", "auto", True)
        assert learning.sync_autonomy(conn, candidate["workflow_id"])["recommended"] == "L3"
        replayed = try_known_workflow(
            conn, estate, f"{case}-replay",
            "My laptop is extremely slow and Teams keeps freezing.",
            "DEVICE_006", "USER_006")
        assert replayed.status == "hit" and replayed.human_intervention == "NONE"
        assert replayed.verification["outcome"] == "verified"
        print("KNOWN FAILURE SIGNATURE teams_memory | APPROVED WORKFLOW FOUND "
              f"{candidate['workflow_id']} | AUTONOMY L3 | HUMAN INTERVENTION NONE | VERIFIED")
        return {"scenario": "learning_loop", "workflow_id": candidate["workflow_id"],
                "autonomy": "L3", "human_intervention": "NONE"}
    finally:
        conn.close()


def knowledge_security(db_path: str, seed: int = 42) -> dict[str, Any]:
    import asyncio
    from coded_tools.digital_workplace.knowledge import (
        GetDocumentAccessContext, SearchEnterpriseKnowledge)

    async def go():
        search = SearchEnterpriseKnowledge()
        ok = await search.async_invoke(
            {"query": "How do I claim internet reimbursement?", "user_role": "employee"}, {})
        denied_search = await search.async_invoke(
            {"query": "Show me another employee's payroll information.", "user_role": "employee"}, {})
        ctx = await GetDocumentAccessContext().async_invoke(
            {"doc_id": "payroll_admin_sop", "user_role": "employee"}, {})
        return ok, denied_search, ctx

    ok, denied_search, ctx = asyncio.run(go())
    assert ok["source"]["doc_id"] == "internet_reimbursement" and ok["answer"]
    assert all(h["doc_id"] != "payroll_admin_sop" for h in denied_search["results"])
    assert ctx["accessible"] is False
    print(f"KNOWLEDGE reimbursed via {ok['source']['doc_id']} | payroll snooping: ACCESS DENIED")
    return {"scenario": "knowledge_security", "answer_doc": ok["source"]["doc_id"],
            "payroll_denied": True}


def main() -> None:
    parser = argparse.ArgumentParser(description="Digital Workplace Autopilot demos")
    parser.add_argument("--scenario", choices=SCENARIOS, default="laptop_teams_memory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--db", default="./data/autopilot.db")
    args = parser.parse_args()
    {"laptop_teams_memory": laptop_teams_memory, "vpn_stale_token": vpn_stale_token,
     "learning_loop": learning_loop, "knowledge_security": knowledge_security}[args.scenario](args.db, args.seed)


if __name__ == "__main__":
    main()
