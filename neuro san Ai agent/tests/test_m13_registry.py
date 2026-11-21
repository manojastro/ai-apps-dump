"""M13 tests: governed registry seed, hash integrity, metrics, selection."""

from __future__ import annotations

from control_plane import registry as reg


def _conn(tmp_path):
    from database.bootstrap import get_connection, init_db
    db = tmp_path / "reg.db"
    init_db(db)
    conn = get_connection(db)
    reg.seed_registry(conn)
    return conn


def test_seed_governed_and_idempotent(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        first = reg.seed_registry(conn)
        assert len(first) == 8
        assert reg.seed_registry(conn) == first  # rerun converges
        scr = reg.lookup_script(conn, "SCR-018")
        assert scr["name"] == "Clear Teams Cache" and scr["version"] == "3.2"
        assert scr["approved"] == 1 and scr["risk"] == "LOW"
        assert scr["autonomy_level"] == "L3" and scr["rollback_available"] == 1
        assert scr["owner"] and scr["approval_timestamp"] and scr["approved_by"]
        assert scr["success_rate"] == 98.9
        assert reg.verify_stored_hash(scr)
    finally:
        conn.close()


def test_tamper_detected(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        conn.execute("UPDATE scripts SET risk='LOW' WHERE script_id='SCR-FIREWALL'")
        conn.execute("UPDATE scripts SET hash='forged' WHERE script_id='SCR-018'")
        conn.commit()
        assert not reg.verify_stored_hash(reg.lookup_script(conn, "SCR-018"))
        assert reg.get_approved_action(conn, "SCR-018") is None  # untrusted
        assert reg.get_approved_action(conn, "SCR-NOPE") is None
        assert reg.get_approved_action(conn, "SCR-DISABLE-PROTECTION") is None
    finally:
        conn.close()


def test_find_approved_action_mapping(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        assert reg.find_approved_action(conn, "Teams excessive memory after update")["script_id"] == "SCR-018"
        assert reg.find_approved_action(conn, "Stale secure-access token")["script_id"] == "SCR-VPN-RECONNECT"
        assert reg.find_approved_action(conn, "Disk exhaustion")["script_id"] == "SCR-DISK-CLEANUP"
        assert reg.find_approved_action(conn, "Printer on fire") is None
    finally:
        conn.close()


def test_execution_accounting(tmp_path) -> None:
    conn = _conn(tmp_path)
    try:
        fresh = reg.record_execution(conn, "SCR-018", True)
        assert (fresh["execution_count"], fresh["success_count"]) == (96, 95)
        assert fresh["success_rate"] == 99.0
        failed = reg.record_execution(conn, "SCR-018", False, rollback=True, reopen=True)
        assert failed["failure_count"] == 2 and failed["rollback_count"] == 2
        assert failed["reopen_count"] == 2
    finally:
        conn.close()


def test_policy_allows_seeded_demo_action(tmp_path) -> None:
    from control_plane.policy import PolicyInput, evaluate

    conn = _conn(tmp_path)
    try:
        result = evaluate(conn, PolicyInput(user_id="USER_001", device_id="DEVICE_038",
                                            action_id="SCR-018"))
        assert result.decision == "ALLOW"
        assert evaluate(conn, PolicyInput(user_id="USER_001", device_id="DEVICE_038",
                                          action_id="SCR-VPN-RECONNECT")).decision == "REQUIRE_APPROVAL"
    finally:
        conn.close()
