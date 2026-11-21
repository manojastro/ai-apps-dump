from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app import clock
from app.approval.service import KIND_ROLE, default_expiry
from app.data.models import Approval, Communication, SupplyOrder
from app.tools.base import MutatingInput, ToolContext, ToolError, register

Kind = Literal["communication", "booking_exception", "followup_booking", "supply_order"]


class RequestApprovalIn(MutatingInput):
    kind: Kind
    ref_id: str
    summary: str = Field(max_length=600)
    payload: dict = Field(default_factory=dict)


class RequestApprovalOut(BaseModel):
    approval_id: str
    status: str
    required_role: str


@register("request_approval", "Ask a human to approve a drafted message, booking exception or supply order. "
                              "Agents can request approvals but can never grant them.", RequestApprovalIn)
def request_approval(ctx: ToolContext, a: RequestApprovalIn) -> RequestApprovalOut:
    payload = dict(a.payload)
    if a.kind == "communication":
        c = ctx.session.get(Communication, a.ref_id)
        if c is None or c.status != "draft":
            raise ToolError("communication must exist and be a draft")
        ctx.check_patient(c.patient_id)
        payload = {**payload, "patient_id": c.patient_id, "body": c.body}
    elif a.kind == "supply_order":
        o = ctx.session.get(SupplyOrder, a.ref_id)
        if o is None or o.status != "draft":
            raise ToolError("order must exist and be a draft")
        o.status = "pending_approval"
        payload = {**payload, "lines": o.lines}
    else:  # booking kinds carry patient_id + slot_id in payload
        pid = payload.get("patient_id")
        if not pid or not payload.get("slot_id"):
            raise ToolError("payload needs patient_id and slot_id")
        ctx.check_patient(pid)
    ap = Approval(id=f"apr-{uuid.uuid4().hex[:8]}", kind=a.kind, status="pending", required_role=KIND_ROLE[a.kind],
                  workflow_id=ctx.workflow_id, ref_id=a.ref_id, summary=a.summary, payload=payload,
                  requested_by=ctx.role, created_at=clock.now(), expires_at=default_expiry(a.kind))
    ctx.session.add(ap)
    return RequestApprovalOut(approval_id=ap.id, status="pending", required_role=ap.required_role)
