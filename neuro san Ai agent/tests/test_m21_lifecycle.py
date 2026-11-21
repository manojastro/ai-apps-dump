"""M21 tests: workflow registry lifecycle (runs, recheck, versions, demotion)."""

from __future__ import annotations

from control_plane import learning
from control_plane import registry as reg


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "wf.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def test_run_metrics_and_recheck(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        row = learning.propose_candidate(conn, "teams_memory", "SCR-018")
        wf = row["workflow_id"]
        learning.record_workflow_run(conn, wf, "C1", "ALLOW", "auto", True)
        learning.record_workflow_run(conn, wf, "C2", "ALLOW", "auto", True)
        learning.record_workflow_run(conn, wf, "C3", "ALLOW", "auto", False)
        fresh = learning.get_workflow(conn, wf)
        assert (fresh["execution_count"], fresh["success_count"], fresh["failure_count"]) == (3, 2, 1)
        assert fresh["success_rate"] == 66.7
        assert learning.recheck_workflow(conn, wf, "USER_001", device_id="DEVICE_001").decision == "ALLOW"
        denied = learning.recheck_workflow(conn, wf, "USER_001", device_id="DEVICE_001",
                                           device_compliant=False)
        assert denied.decision == "DENY"
    finally:
        conn.close()


def test_version_snapshot_and_promote_integration(tmp_path) -> None:
    from control_plane import approvals

    conn = _conn(tmp_path)
    try:
        candidate = learning.propose_candidate(conn, "teams_memory", "SCR-018")
        wf = candidate["workflow_id"]
        assert learning.snapshot_version(conn, wf) == f"{wf}-v1"
        try:
            learning.promote_candidate(conn, wf)
        except ValueError:
            pass
        gate = approvals.latest_for(conn, "", wf)
        approvals.approve(conn, gate["approval_id"], "change-advisory-board")
        assert learning.promote_candidate(conn, wf)["approval_state"] == "approved"
        versions = conn.execute("SELECT * FROM workflow_versions WHERE workflow_id=?",
                                (wf,)).fetchall()
        assert len(versions) >= 2  # manual snapshot + promotion snapshot
        assert versions[-1]["definition"]
    finally:
        conn.close()


def test_workflow_demotion_on_failures(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        conn.execute("INSERT INTO workflows(workflow_id, failure_signature, action_id, "
                     "autonomy_level, approval_state) VALUES ('WF-OLD', 'sig', 'SCR-018', 'L3', 'approved')")
        conn.commit()
        for i in range(3):
            learning.record_workflow_run(conn, "WF-OLD", f"C{i}", "ALLOW", "auto", False)
        outcome = learning.sync_autonomy(conn, "WF-OLD")
        assert outcome["recommended"] == "L2"
        assert learning.get_workflow(conn, "WF-OLD")["autonomy_level"] == "L2"
    finally:
        conn.close()
