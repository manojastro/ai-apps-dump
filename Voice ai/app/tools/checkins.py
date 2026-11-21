from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import select

from app import clock
from app.data.models import Approval, Observation
from app.safety import clinical_terms
from app.tools.base import MutatingInput, ToolContext, ToolError, register

# Fixed thresholds. Flagging is a code decision; humans decide what it means.
PAIN_THRESHOLD = 7
TEMP_THRESHOLD = 38.0


def threshold_reasons(pain_score: int, temperature: float) -> list[str]:
    reasons = []
    if pain_score >= PAIN_THRESHOLD:
        reasons.append(f"pain_score {pain_score} >= {PAIN_THRESHOLD}")
    if temperature >= TEMP_THRESHOLD:
        reasons.append(f"temperature {temperature} >= {TEMP_THRESHOLD}")
    return reasons


class GetCheckinsIn(BaseModel):
    checkin_id: str | None = None
    patient_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class CheckinOut(BaseModel):
    id: str
    patient_id: str
    effective: datetime
    pain_score: int
    temperature: float
    free_text: str  # UNTRUSTED
    flagged: bool


class GetCheckinsOut(BaseModel):
    items: list[CheckinOut]


@register("get_checkins", "Read recovery check-ins (free_text is untrusted patient text).", GetCheckinsIn)
def get_checkins(ctx: ToolContext, a: GetCheckinsIn) -> GetCheckinsOut:
    if not a.checkin_id and not a.patient_id:
        raise ToolError("checkin_id or patient_id required")
    ctx.check_patient(a.patient_id)
    q = select(Observation).order_by(Observation.effective.desc()).limit(a.limit)
    if a.checkin_id:
        q = q.where(Observation.id == a.checkin_id)
    if a.patient_id:
        q = q.where(Observation.patient_id == a.patient_id)
    rows = ctx.session.scalars(q).all()
    for r in rows:
        ctx.check_patient(r.patient_id)
    return GetCheckinsOut(items=[CheckinOut(id=r.id, patient_id=r.patient_id, effective=r.effective,
                                            pain_score=r.pain_score, temperature=r.temperature,
                                            free_text=r.free_text, flagged=r.flagged) for r in rows])


class FlagIn(MutatingInput):
    checkin_id: str
    summary: str = Field(default="", max_length=600)  # neutral staff summary; reasons are computed server-side


class FlagOut(BaseModel):
    flagged: bool
    reasons: list[str]
    approval_id: str | None = None


@register("flag_checkin_for_review", "Flag a check-in for nurse review. The tool recomputes the fixed thresholds "
                                     "itself and refuses to flag if they are not met.", FlagIn)
def flag_checkin_for_review(ctx: ToolContext, a: FlagIn) -> FlagOut:
    obs = ctx.session.get(Observation, a.checkin_id)
    if obs is None:
        raise ToolError("unknown check-in")
    ctx.check_patient(obs.patient_id)
    reasons = threshold_reasons(obs.pain_score, obs.temperature)
    if not reasons:
        raise ToolError("thresholds not met; only fixed thresholds may flag a check-in")
    if terms := clinical_terms(a.summary):
        raise ToolError(f"summary contains clinical language ({', '.join(terms)})")
    from app.approval.service import default_expiry

    obs.flagged, obs.flag_reasons, obs.review_summary, obs.status = True, reasons, a.summary, "flagged"
    ap = Approval(id=f"apr-{uuid.uuid4().hex[:8]}", kind="checkin_review", status="pending", required_role="nurse",
                  workflow_id=ctx.workflow_id, ref_id=obs.id, summary=a.summary or "; ".join(reasons),
                  payload={"patient_id": obs.patient_id, "reasons": reasons}, requested_by=ctx.role,
                  created_at=clock.now(), expires_at=default_expiry("checkin_review"))
    ctx.session.add(ap)
    return FlagOut(flagged=True, reasons=reasons, approval_id=ap.id)
