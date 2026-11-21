import pytest
import yaml
from sqlalchemy import func, select

from app.audit import log as audit
from app.data import db
from app.data.models import Appointment, AuditEntry, Communication, Observation
from app.rbac import policy
from app.tools import REGISTRY, call_tool

ROLES = list(policy.roles()) + ["nobody"]


def test_policy_only_references_real_tools():
    for role, tools in policy.load_policy()["roles"].items():
        assert set(tools) <= set(REGISTRY), role


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("tool", sorted(REGISTRY))
def test_permission_matrix(seeded, role, tool):
    """Every tool from every role: allowed iff policy.yaml says so. Empty args => allowed roles hit
    validation (error), never 'denied'; disallowed roles are denied before anything else happens."""
    res = call_tool(role, tool, {})
    expected_allowed = tool in (yaml.safe_load(policy.POLICY_PATH.read_text())["roles"].get(role) or [])
    if expected_allowed:
        assert res.status != "denied", res
    else:
        assert res.status == "denied"
        assert "not allowed" in res.error
    last = audit.search(limit=1)[0]  # every call, denied or not, is audited
    assert last.tool == tool and last.actor == role


def test_denied_calls_are_audited_with_reason(seeded):
    res = call_tool("supply", "get_patient_summary", {"patient_id": "pat-0001"}, workflow_id="wf-x")
    assert res.status == "denied"
    e = audit.search(tool="get_patient_summary")[0]
    assert (e.actor, e.status, e.workflow_id, e.patient_id) == ("supply", "denied", "wf-x", "pat-0001")
    assert len(e.args_hash) == 16


def test_unknown_tool_denied(seeded):
    assert call_tool("scheduler", "cancel_all_appointments", {}).status == "denied"


def test_field_limits_hide_data(seeded):
    sched = call_tool("scheduler", "get_patient_summary", {"patient_id": "pat-0001"}).data
    follow = call_tool("followup", "get_patient_summary", {"patient_id": "pat-0001"}).data
    assert "last_appointment" not in sched and "last_appointment" in follow
    for d in (sched, follow):
        assert "phone" not in d and "birth_date" not in d and "observations" not in d
    chk = call_tool("recovery", "get_checkins", {"patient_id": _patient_with_checkin()}).data
    assert chk["items"] and "free_text" in chk["items"][0]


def _patient_with_checkin():
    with db.session() as s:
        return s.scalars(select(Observation.patient_id)).first()


def test_supply_gets_no_patient_data_even_via_forecast(seeded):
    r = call_tool("supply", "get_usage_forecast", {"days": 14})
    assert r.status == "ok"
    assert set(r.data) == {"days", "upcoming_appointments", "items"}


def test_mutating_tools_need_idempotency_key(seeded):
    r = call_tool("followup", "draft_communication", {"patient_id": "pat-0001", "body": "Hello"})
    assert r.status == "error" and "idempotency_key" in r.error


def test_idempotent_replay_does_not_duplicate(seeded):
    args = {"patient_id": "pat-0001", "body": "Reminder about your appointment.", "idempotency_key": "k1"}
    a, b = call_tool("followup", "draft_communication", args), call_tool("followup", "draft_communication", args)
    assert a.status == b.status == "ok" and not a.replayed and b.replayed
    assert a.data == b.data
    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(Communication)) == 1
    assert audit.search(tool="draft_communication", limit=1)[0].status == "replayed"


def test_patient_scope_blocks_cross_patient_access(seeded):
    r = call_tool("followup", "get_patient_summary", {"patient_id": "pat-0002"}, patient_scope="pat-0001")
    assert r.status == "denied" and "scoped" in r.error
    r = call_tool("followup", "draft_communication",
                  {"patient_id": "pat-0002", "body": "hi", "idempotency_key": "x"}, patient_scope="pat-0001")
    assert r.status == "denied"


def test_message_guards(seeded):
    bad = call_tool("followup", "draft_communication",
                    {"patient_id": "pat-0001", "body": "Also pat-0002 has an appointment", "idempotency_key": "a"})
    assert bad.status == "error" and "another patient" in bad.error
    bad = call_tool("followup", "draft_communication",
                    {"patient_id": "pat-0001", "body": "You should stop taking your medication", "idempotency_key": "b"})
    assert bad.status == "error" and "clinical" in bad.error


def test_flag_tool_recomputes_thresholds_itself(seeded):
    with db.session() as s:
        low = s.scalars(select(Observation).where(Observation.pain_score < 7, Observation.temperature < 38.0)).first()
        high = s.scalars(select(Observation).where(Observation.pain_score >= 7)).first()
        low_id, high_id = low.id, high.id
    r = call_tool("recovery", "flag_checkin_for_review", {"checkin_id": low_id, "summary": "x", "idempotency_key": "l"})
    assert r.status == "error" and "thresholds not met" in r.error
    r = call_tool("recovery", "flag_checkin_for_review", {"checkin_id": high_id, "summary": "Neutral note.",
                                                          "idempotency_key": "h"})
    assert r.status == "ok" and r.data["flagged"] and r.data["approval_id"]


def test_booking_rules_and_approval_exception(seeded):
    slots = call_tool("scheduler", "find_slots", {"limit": 10}).data["items"]
    ids = [x["slot_id"] for x in slots]
    for i in range(3):  # fill the patient's allowance
        with db.session() as s:
            n = s.scalar(select(func.count()).select_from(Appointment).where(
                Appointment.patient_id == "pat-0001", Appointment.status == "booked"))
        if n >= 3:
            break
        assert call_tool("scheduler", "book_appointment", {"patient_id": "pat-0001", "slot_id": ids[i],
                                                           "idempotency_key": f"b{i}"}).data["status"] == "booked"
    over = call_tool("scheduler", "book_appointment", {"patient_id": "pat-0001", "slot_id": ids[5],
                                                       "idempotency_key": "over"})
    assert over.data["status"] == "requires_approval"
    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(AuditEntry)) > 0
