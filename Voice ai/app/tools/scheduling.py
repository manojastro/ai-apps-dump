from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from sqlalchemy import select

from app import clock
from app.data.models import Appointment, Approval, Patient, Slot
from app.tools.base import MutatingInput, ToolContext, ToolError, register

MAX_FUTURE_APPOINTMENTS = 3
MIN_RESCHEDULE_NOTICE = timedelta(hours=24)


class FindSlotsIn(BaseModel):
    practitioner_id: str | None = None
    after: datetime | None = None
    limit: int = Field(default=5, ge=1, le=10)


class SlotOut(BaseModel):
    slot_id: str
    practitioner_id: str
    start: datetime
    end: datetime


class FindSlotsOut(BaseModel):
    items: list[SlotOut]


@register("find_slots", "Find free appointment slots, earliest first.", FindSlotsIn)
def find_slots(ctx: ToolContext, a: FindSlotsIn) -> FindSlotsOut:
    after = max(a.after or clock.now(), clock.now())
    q = select(Slot).where(Slot.status == "free", Slot.start > after).order_by(Slot.start, Slot.id).limit(a.limit)
    if a.practitioner_id:
        q = q.where(Slot.practitioner_id == a.practitioner_id)
    rows = ctx.session.scalars(q).all()
    return FindSlotsOut(items=[SlotOut(slot_id=r.id, practitioner_id=r.practitioner_id, start=r.start, end=r.end)
                               for r in rows])


class BookIn(MutatingInput):
    patient_id: str
    slot_id: str
    reason: str = Field(default="", max_length=200)
    approval_id: str | None = None  # set by orchestrator code after a human approved an exception


class BookOut(BaseModel):
    status: str  # booked | requires_approval
    appointment_id: str | None = None
    detail: str = ""


def _approved(ctx: ToolContext, approval_id: str | None, patient_id: str) -> bool:
    if not approval_id:
        return False
    ap = ctx.session.get(Approval, approval_id)
    return bool(ap and ap.status == "approved" and ap.payload.get("patient_id") == patient_id)


def _future_booked(ctx: ToolContext, patient_id: str) -> int:
    return len(ctx.session.scalars(select(Appointment.id).where(
        Appointment.patient_id == patient_id, Appointment.status == "booked", Appointment.start > clock.now())).all())


@register("book_appointment", "Book a free slot for a patient if it is within booking rules; otherwise it reports "
                              "requires_approval and changes nothing.", BookIn)
def book_appointment(ctx: ToolContext, a: BookIn) -> BookOut:
    ctx.check_patient(a.patient_id)
    if ctx.session.get(Patient, a.patient_id) is None:
        raise ToolError("unknown patient")
    slot = ctx.session.get(Slot, a.slot_id)
    if slot is None:
        raise ToolError("unknown slot")
    if slot.status != "free":
        raise ToolError("slot is not free")
    if slot.start <= clock.now():
        raise ToolError("slot is in the past")
    approved = _approved(ctx, a.approval_id, a.patient_id)
    if not approved and _future_booked(ctx, a.patient_id) >= MAX_FUTURE_APPOINTMENTS:
        return BookOut(status="requires_approval",
                       detail=f"patient already has {MAX_FUTURE_APPOINTMENTS}+ future appointments")
    slot.status = "busy"
    appt = Appointment(id=f"appt-{uuid.uuid4().hex[:8]}", patient_id=a.patient_id, practitioner_id=slot.practitioner_id,
                       slot_id=slot.id, start=slot.start, status="booked", reason=a.reason, created_at=clock.now())
    ctx.session.add(appt)
    return BookOut(status="booked", appointment_id=appt.id)


class RescheduleIn(MutatingInput):
    appointment_id: str
    new_slot_id: str
    approval_id: str | None = None


@register("reschedule_appointment", "Move an existing appointment to a new free slot. Changes within 24h of the "
                                    "appointment need approval.", RescheduleIn)
def reschedule_appointment(ctx: ToolContext, a: RescheduleIn) -> BookOut:
    appt = ctx.session.get(Appointment, a.appointment_id)
    if appt is None or appt.status != "booked":
        raise ToolError("appointment not found or not booked")
    ctx.check_patient(appt.patient_id)
    new = ctx.session.get(Slot, a.new_slot_id)
    if new is None or new.status != "free" or new.start <= clock.now():
        raise ToolError("new slot unavailable")
    if appt.start - clock.now() < MIN_RESCHEDULE_NOTICE and not _approved(ctx, a.approval_id, appt.patient_id):
        return BookOut(status="requires_approval", detail="less than 24h notice")
    old = ctx.session.get(Slot, appt.slot_id)
    if old:
        old.status = "free"
    new.status = "busy"
    appt.slot_id, appt.start, appt.practitioner_id = new.id, new.start, new.practitioner_id
    return BookOut(status="booked", appointment_id=appt.id)
