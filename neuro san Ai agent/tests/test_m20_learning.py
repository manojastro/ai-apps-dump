"""M20 tests: resolution snapshots → candidates → governed promotion."""

from __future__ import annotations

import pytest

from control_plane import approvals
from control_plane import learning
from control_plane import registry as reg


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "learn.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def _record(conn, case: str, approved: bool = True, reopen: bool = False,
            success: bool = True) -> None:
    learning.record_resolution(
        conn, case, "teams_memory", ["ram", "process_memory"],
        "Teams excessive memory after update", "SCR-018",
        policy_result="ALLOW", approval_state="APPROVED" if approved else "auto",
        verification_passed=success, success=success, reopen=reopen)


def test_record_detect_propose(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        assert conn.execute("SELECT COUNT(*) AS n FROM resolution_patterns").fetchone()["n"] == 0
        _record(conn, "CASE-1")
        row = conn.execute("SELECT * FROM resolution_patterns").fetchone()
        assert row["failure_signature"] == "teams_memory" and row["success"] == 1
        assert learning.detect_candidates(conn) == []
        _record(conn, "CASE-2")
        _record(conn, "CASE-3")
        found = learning.detect_candidates(conn)
        assert len(found) == 1 and found[0]["occurrences"] == 3
        assert found[0]["success_rate"] == 1.0 and found[0]["action_id"] == "SCR-018"
        candidate = learning.propose_candidate(conn, "teams_memory", "SCR-018")
        assert candidate["approval_state"] == "candidate"
        assert candidate["autonomy_level"] == "L1"  # earned later, never granted
    finally:
        conn.close()


def test_reopened_and_unapproved_excluded(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        _record(conn, "CASE-1")
        _record(conn, "CASE-2")
        _record(conn, "CASE-3", reopen=True)  # relapse: excluded from occurrences
        _record(conn, "CASE-4", approved=False)  # auto success counts, but is not human touch
        assert learning.detect_candidates(conn) == []
        _record(conn, "CASE-5")
        # 4 clean of 5 total (reopen excluded); rate reflects every row.
        found = learning.detect_candidates(conn, min_success_rate=0.5)
        assert len(found) == 1 and found[0]["occurrences"] == 4
        assert found[0]["success_rate"] == 0.8
        assert learning.detect_candidates(conn) == []  # default 0.9 still blocks
        # All-auto pattern (zero APPROVED rows) never proposes, however often.
        for i in range(6, 10):
            learning.record_resolution(
                conn, f"AUTO-{i}", "auto_sig", ["x"], "r", "SCR-018",
                approval_state="auto", verification_passed=True, success=True)
        auto = [c for c in learning.detect_candidates(conn, min_success_rate=0.5)
                if c["failure_signature"] == "auto_sig"]
        assert auto == []
    finally:
        conn.close()


def test_promote_gauntlet_and_no_self_promotion(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        for i in range(3):
            _record(conn, f"CASE-{i}")
        candidate = learning.propose_candidate(conn, "teams_memory", "SCR-018")
        with pytest.raises(ValueError, match="awaiting human approval"):
            learning.promote_candidate(conn, candidate["workflow_id"])
        gate = approvals.latest_for(conn, "", candidate["workflow_id"])
        approvals.approve(conn, gate["approval_id"], "change-advisory-board")
        done = learning.promote_candidate(conn, candidate["workflow_id"])
        assert done["approval_state"] == "approved" and done["autonomy_level"] == "L1"
        assert learning.promote_candidate(conn, candidate["workflow_id"])["approval_state"] == "approved"
    finally:
        conn.close()


def test_promote_refuses_unapproved_action(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        candidate = learning.propose_candidate(conn, "x", "SCR-DISABLE-PROTECTION")
        gate = approvals.latest_for(conn, "", candidate["workflow_id"])
        if gate is None:
            try:
                learning.promote_candidate(conn, candidate["workflow_id"])
            except ValueError:
                pass
            gate = approvals.latest_for(conn, "", candidate["workflow_id"])
        approvals.approve(conn, gate["approval_id"], "change-advisory-board")
        with pytest.raises(ValueError, match="not approved"):
            learning.promote_candidate(conn, candidate["workflow_id"])
    finally:
        conn.close()


def test_ops_tools_delegate(tmp_path, monkeypatch) -> None:
    import asyncio
    import tests.conftest  # noqa: F401
    from coded_tools.digital_workplace import ops

    async def go():
        return await ops.RecordResolutionPattern().async_invoke(
            {"case_id": "CASE-T", "failure_signature": "teams_memory",
             "action_id": "SCR-018", "approval_state": "APPROVED",
             "verification_passed": True, "success": True}, {})
    monkeypatch.setenv("DB_PATH", str(tmp_path / "ops.db"))
    out = asyncio.run(go())
    assert out["recorded"] and out["pattern_id"].startswith("PAT-CASE-T-")
