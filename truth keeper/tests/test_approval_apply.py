import sqlite3

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from app.applier.applier import Applier
from app.applier.sandbox import SandboxViolation, assert_writable
from app.approval.store import InvalidTransition
from app.audit import log as audit_module
from app.core import pipeline
from app.core.detection import detect_dir
from app.core.regressions import load_cases
from app.llm.client import LLMClient


def run(settings, store):
    return pipeline.run(store, LLMClient(settings), settings.sandbox_dir, "v1")


def proposal_for(store, ctype):
    rows = [r for r in store.list_queue(type=ctype) if r["proposal"] and r["proposal"]["status"] == "PENDING_REVIEW"]
    return rows[0]


def sandbox_sub_status(settings, sub_id):
    con = sqlite3.connect(settings.sandbox_dir / "billing.db")
    try:
        return con.execute("SELECT status FROM subscriptions WHERE subscription_id=?", (sub_id,)).fetchone()[0]
    finally:
        con.close()


def test_pipeline_queues_every_conflict(env):
    settings, store = env
    s = run(settings, store)
    assert s.detected == 120 and s.proposed == 120 and s.failed == 0
    queue = store.list_queue()
    assert [r["impact_usd"] for r in queue] == sorted((r["impact_usd"] for r in queue), reverse=True)
    again = run(settings, store)  # idempotent: existing proposals are not duplicated
    assert again.proposed == 0 and again.skipped_existing == 120


def test_approve_then_apply_fixes_sandbox_and_conflict_is_gone(env):
    settings, store = env
    run(settings, store)
    row = proposal_for(store, "CANCELLED_BUT_BILLING_ACTIVE")
    pid, sub = row["proposal"]["id"], row["proposal"]["params"]["subscription_id"]
    applier = Applier(store, settings.sandbox_dir, settings.generated_dir)

    assert applier.apply(pid, "alice").outcome == "refused"  # no approval yet -> nothing changes
    assert sandbox_sub_status(settings, sub) == "active"

    store.approve(pid, "alice", "looks right")
    res = applier.apply(pid, "alice")
    assert res.outcome == "applied" and res.conflict_still_detected is False
    assert res.before["status"] == "active" and res.after["status"] == "cancelled"
    assert sandbox_sub_status(settings, sub) == "cancelled"
    # originals untouched
    con = sqlite3.connect(settings.generated_dir / "billing.db")
    assert con.execute("SELECT status FROM subscriptions WHERE subscription_id=?", (sub,)).fetchone()[0] == "active"
    con.close()
    # re-running the detector shows the conflict is gone
    assert row["id"] not in {c.id for c in detect_dir(settings.sandbox_dir).conflicts}
    assert store.get_conflict(row["id"])["status"] == "RESOLVED"
    events = [e["event"] for e in store.audit_entries(entity_id=str(pid))]
    assert "proposal_approved" in events and "fix_applied" in events
    applied = [e for e in store.audit_entries(entity_id=str(pid)) if e["event"] == "fix_applied"][0]
    assert applied["before"] and applied["after"] and applied["actor"] == "alice"


def test_double_apply_changes_nothing(env):
    settings, store = env
    run(settings, store)
    pid = proposal_for(store, "PLAN_MISMATCH")["proposal"]["id"]
    store.approve(pid, "bob")
    applier = Applier(store, settings.sandbox_dir, settings.generated_dir)
    assert applier.apply(pid, "bob").outcome == "applied"
    snapshot = (settings.sandbox_dir / "crm.db").read_bytes()
    second = applier.apply(pid, "bob")
    assert second.outcome == "already_applied"
    assert (settings.sandbox_dir / "crm.db").read_bytes() == snapshot


def test_reject_blocks_apply_and_creates_regression_case(env):
    settings, store = env
    run(settings, store)
    pid = proposal_for(store, "EMAIL_MISMATCH")["proposal"]["id"]
    with pytest.raises(InvalidTransition):
        store.reject(pid, "carol", "")  # a reason is mandatory
    store.reject(pid, "carol", "billing contact is correct, CRM is outdated")
    assert Applier(store, settings.sandbox_dir, settings.generated_dir).apply(pid, "carol").outcome == "refused"
    with pytest.raises(InvalidTransition):
        store.approve(pid, "carol")  # cannot approve after rejecting
    cases = load_cases(settings.regressions_dir)
    assert len(cases) == 1 and cases[0]["source"] == "rejected" and "carol" in cases[0]["note"]


def test_stale_precondition_marks_stale_and_applies_nothing(env):
    """Debugging exercise 3: edit sandbox after approval, before apply."""
    settings, store = env
    run(settings, store)
    row = proposal_for(store, "CANCELLED_BUT_BILLING_ACTIVE")
    pid, sub = row["proposal"]["id"], row["proposal"]["params"]["subscription_id"]
    store.approve(pid, "dave")
    con = sqlite3.connect(settings.sandbox_dir / "billing.db")
    con.execute("UPDATE subscriptions SET monthly_amount = monthly_amount + 1 WHERE subscription_id=?", (sub,))
    con.commit()
    con.close()
    res = Applier(store, settings.sandbox_dir, settings.generated_dir).apply(pid, "dave")
    assert res.outcome == "stale"
    assert store.get_proposal(pid)["status"] == "STALE"
    assert sandbox_sub_status(settings, sub) == "active"
    assert any(e["event"] == "apply_stale" for e in store.audit_entries(entity_id=str(pid)))


def test_flag_for_review_hands_conflict_off(env):
    settings, store = env
    run(settings, store)
    row = proposal_for(store, "PAST_DUE_BUT_CRM_ACTIVE")
    pid = row["proposal"]["id"]
    store.approve(pid, "erin")
    res = Applier(store, settings.sandbox_dir, settings.generated_dir).apply(pid, "erin")
    assert res.outcome == "applied" and res.after["status"] == "open"
    assert row["id"] not in {c.id for c in detect_dir(settings.sandbox_dir).conflicts}


def test_merge_duplicates(env):
    settings, store = env
    run(settings, store)
    row = proposal_for(store, "DUPLICATE_CUSTOMER")
    store.approve(row["proposal"]["id"], "fay")
    res = Applier(store, settings.sandbox_dir, settings.generated_dir).apply(row["proposal"]["id"], "fay")
    assert res.outcome == "applied" and res.after["merged_into"] == row["proposal"]["params"]["keep_customer_id"]
    assert res.conflict_still_detected is False


def test_audit_log_is_append_only(env):
    settings, store = env
    run(settings, store)
    public = [n for n in dir(audit_module) if not n.startswith("_")]
    assert not any(w in n.lower() for n in public for w in ("update", "delete", "remove", "edit"))
    with store.engine.begin() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM audit_log")).scalar()
    assert n > 0
    for sql in ("UPDATE audit_log SET actor='mallory'", "DELETE FROM audit_log"):
        with pytest.raises(DatabaseError, match="append-only"), store.engine.begin() as conn:
            conn.execute(text(sql))
    with store.engine.begin() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM audit_log")).scalar() == n


def test_applier_refuses_paths_outside_sandbox(env, tmp_path):
    settings, _ = env
    with pytest.raises(SandboxViolation):
        assert_writable(settings.generated_dir / "crm.db", settings.sandbox_dir, settings.generated_dir)
    with pytest.raises(SandboxViolation):
        assert_writable(tmp_path / "elsewhere.db", settings.sandbox_dir, settings.generated_dir)


def test_decisions_require_reviewer(env):
    settings, store = env
    run(settings, store)
    pid = proposal_for(store, "PLAN_MISMATCH")["proposal"]["id"]
    with pytest.raises(InvalidTransition):
        store.approve(pid, "  ")
