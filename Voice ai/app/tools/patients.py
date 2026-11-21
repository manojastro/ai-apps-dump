from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select

from app import clock
from app.data.models import Appointment, Patient
from app.tools.base import ToolContext, ToolError, register


class PatientIn(BaseModel):
    patient_id: str


class ApptBrief(BaseModel):
    id: str
    start: str
    reason: str


class PatientSummary(BaseModel):
    patient_id: str
    name: str
    last_appointment: ApptBrief | None = None
    upcoming_appointments: list[ApptBrief] = []


def _brief(x: Appointment) -> ApptBrief:
    return ApptBrief(id=x.id, start=x.start.isoformat(), reason=x.reason)


@register("get_patient_summary", "Minimal patient summary: name and appointments only.", PatientIn)
def get_patient_summary(ctx: ToolContext, a: PatientIn) -> PatientSummary:
    ctx.check_patient(a.patient_id)
    p = ctx.session.get(Patient, a.patient_id)
    if p is None:
        raise ToolError("unknown patient")
    appts = ctx.session.scalars(select(Appointment).where(
        Appointment.patient_id == p.id, Appointment.status != "cancelled").order_by(Appointment.start)).all()
    now = clock.now()
    past = [x for x in appts if x.start <= now]
    return PatientSummary(patient_id=p.id, name=f"{p.given} {p.family}",
                          last_appointment=_brief(past[-1]) if past else None,
                          upcoming_appointments=[_brief(x) for x in appts if x.start > now][:5])
