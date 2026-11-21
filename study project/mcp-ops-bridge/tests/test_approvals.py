"""Approval token tests: reuse, wrong-target, wrong-tool, expired (M6)."""

from mock_itsm import approvals as appr
from mock_itsm.db import connect


def test_happy_path_and_reuse_blocked(db_path: str) -> None:
    conn = connect(db_path)
    try:
        token, _ = appr.create_approval(conn, "update_incident_state", "INC1000001")
        assert appr.verify_approval(conn, token, "update_incident_state", "INC1000001").ok is True
        # single-use: second verify must fail
        second = appr.verify_approval(conn, token, "update_incident_state", "INC1000001")
        assert second.ok is False
        assert "used" in second.reason
    finally:
        conn.close()


def test_wrong_target_blocked(db_path: str) -> None:
    conn = connect(db_path)
    try:
        token, _ = appr.create_approval(conn, "update_incident_state", "INC1000001")
        out = appr.verify_approval(conn, token, "update_incident_state", "INC1000002")
        assert out.ok is False
        assert "target" in out.reason
    finally:
        conn.close()


def test_wrong_tool_blocked(db_path: str) -> None:
    conn = connect(db_path)
    try:
        token, _ = appr.create_approval(conn, "add_work_note", "INC1000001")
        out = appr.verify_approval(conn, token, "update_incident_state", "INC1000001")
        assert out.ok is False
        assert "tool" in out.reason
    finally:
        conn.close()


def test_expired_blocked(db_path: str) -> None:
    conn = connect(db_path)
    try:
        token, _ = appr.create_approval(conn, "add_work_note", "INC1000001", expires_minutes=-1)
        out = appr.verify_approval(conn, token, "add_work_note", "INC1000001")
        assert out.ok is False
        assert "expired" in out.reason
    finally:
        conn.close()


def test_unknown_token_blocked(db_path: str) -> None:
    conn = connect(db_path)
    try:
        out = appr.verify_approval(conn, "nope", "add_work_note", "INC1000001")
        assert out.ok is False
    finally:
        conn.close()


def test_tokens_stored_hashed(db_path: str) -> None:
    conn = connect(db_path)
    try:
        token, _ = appr.create_approval(conn, "add_work_note", "INC1000001")
        cur = conn.execute(
            "SELECT token_hash FROM approvals WHERE target='INC1000001' ORDER BY created_at DESC LIMIT 1"
        )
        stored = str(cur.fetchone()["token_hash"])
        assert token not in stored  # plaintext never stored
        assert stored == appr.hash_token(token)
    finally:
        conn.close()
