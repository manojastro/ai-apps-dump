"""M22 tests: known-workflow replay (policy re-checked on every reuse)."""

from __future__ import annotations

from orchestration.replay import match_signature, try_known_workflow


def _conn(tmp_path):
    from control_plane import registry as reg
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "replay.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    conn.execute("INSERT INTO workflows(workflow_id, name, failure_signature, "
                 "root_cause_signature, action_id, autonomy_level, approval_state) "
                 "VALUES ('WF-023', 'Teams memory', 'teams_memory', 'Teams memory', "
                 "'SCR-018', 'L3', 'approved')")
    conn.execute("INSERT INTO workflows(workflow_id, name, failure_signature, "
                 "action_id, autonomy_level, approval_state) "
                 "VALUES ('WF-VPN', 'VPN stale', 'vpn_stale', 'SCR-VPN-RECONNECT', 'L2', 'approved')")
    conn.commit()
    return conn


def test_signature_match_threshold() -> None:
    assert match_signature("My laptop is slow and Teams keeps freezing", "teams_memory") >= 0.5
    assert match_signature("How do I claim internet reimbursement?", "teams_memory") == 0.0
    assert match_signature("anything", "") == 0.0


def test_l3_replay_auto_heals(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    result = try_known_workflow(conn, estate, "CASE-R1",
                                "My laptop is extremely slow and Teams keeps freezing.",
                                "DEVICE_005", "USER_005")
    assert result.status == "hit" and result.workflow_id == "WF-023"
    assert result.autonomy == "L3" and result.policy_decision == "ALLOW"
    assert result.human_intervention == "NONE"
    assert result.verification["outcome"] == "verified"
    teams = next(p.mem_mb for p in estate.get("DEVICE_005").processes if p.name == "Teams")
    assert teams == 640.0
    row = conn.execute("SELECT * FROM workflows WHERE workflow_id='WF-023'").fetchone()
    assert (row["execution_count"], row["success_count"], row["success_rate"]) == (1, 1, 100.0)


def test_miss_falls_back_to_investigation(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    result = try_known_workflow(conn, estate, "CASE-X",
                                "How do I claim internet reimbursement?",
                                "DEVICE_001", "USER_001")
    assert result.status == "miss"


def test_policy_recheck_blocks_changed_posture(tmp_path) -> None:
    from simulator.estate import generate_estate

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    estate.get("DEVICE_005").compliance_state = "non-compliant"
    before = dict(estate.get("DEVICE_005").__dict__)
    result = try_known_workflow(conn, estate, "CASE-R2",
                                "My laptop is extremely slow and Teams keeps freezing.",
                                "DEVICE_005", "USER_005")
    assert result.status == "hit" and result.policy_decision == "DENY"
    assert result.human_intervention == "REQUIRED"
    assert result.execution is None  # never executed
    assert estate.get("DEVICE_005").cpu_pct == before["cpu_pct"]


def test_l2_pauses_then_executes_after_approval(tmp_path) -> None:
    from control_plane import approvals
    from simulator.estate import generate_estate

    conn, estate = _conn(tmp_path), generate_estate(seed=42)
    first = try_known_workflow(conn, estate, "CASE-VPN",
                               "I changed my password and now my VPN will not connect.",
                               "DEVICE_002", "USER_002")
    assert first.status == "hit" and first.human_intervention == "REQUIRED"
    assert first.execution.status == "awaiting_approval"
    assert estate.get("DEVICE_002").vpn_connected is False
    approvals.approve(conn, first.execution.approval_id, "manager")
    second = try_known_workflow(conn, estate, "CASE-VPN",
                                "I changed my password and now my VPN will not connect.",
                                "DEVICE_002", "USER_002")
    assert second.human_intervention == "APPROVED"
    assert second.verification["outcome"] == "verified"
    assert estate.get("DEVICE_002").vpn_connected is True
    row = conn.execute("SELECT * FROM workflows WHERE workflow_id='WF-VPN'").fetchone()
    assert (row["execution_count"], row["success_count"]) == (1, 1)
