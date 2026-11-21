"""Pydantic v2 shapes for the mock ITSM API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Incident(BaseModel):
    sys_id: str
    number: str
    short_description: str
    description: str = ""
    state: str = "New"
    priority: str = "3"
    service: str = ""
    ci: str = ""
    caller: str = ""
    opened_at: str = ""
    updated_at: str = ""
    work_notes: str = "[]"
    resolution: str = ""


class IncidentPatch(BaseModel):
    state: str | None = None
    work_notes: str | None = Field(default=None, description="Note text to append")
    resolution: str | None = None


class ApprovalCreate(BaseModel):
    tool: str
    target: str
    action: str = "write"
    expires_minutes: int = 10


class ApprovalIssued(BaseModel):
    approval_token: str
    tool: str
    target: str
    expires_at: str


class ApprovalCheck(BaseModel):
    ok: bool
    reason: str = ""
