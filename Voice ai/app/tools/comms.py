from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app import clock
from app.data.models import Communication, Patient
from app.safety import clinical_terms, foreign_patient_ids
from app.tools.base import MutatingInput, ToolContext, ToolError, register


class DraftIn(MutatingInput):
    patient_id: str
    body: str = Field(min_length=1, max_length=1000)


class DraftOut(BaseModel):
    communication_id: str
    status: str


@register("draft_communication", "Create a DRAFT message to a patient (operational content only). "
                                 "It is not sent; it must go through request_approval.", DraftIn)
def draft_communication(ctx: ToolContext, a: DraftIn) -> DraftOut:
    ctx.check_patient(a.patient_id)
    if ctx.session.get(Patient, a.patient_id) is None:
        raise ToolError("unknown patient")
    if foreign_patient_ids(a.body, a.patient_id):
        raise ToolError("message references another patient")
    if terms := clinical_terms(a.body):
        raise ToolError(f"message contains clinical language ({', '.join(terms)}); operations messages only")
    c = Communication(id=f"comm-{uuid.uuid4().hex[:8]}", patient_id=a.patient_id, workflow_id=ctx.workflow_id,
                      status="draft", body=a.body, created_by=ctx.role, created_at=clock.now())
    ctx.session.add(c)
    return DraftOut(communication_id=c.id, status="draft")
