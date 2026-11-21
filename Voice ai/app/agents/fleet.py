"""The four agents. Each has its own role (policy.yaml allow-list), prompt and result shape."""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, field_validator

from app.agents.base import AgentRunResult, BaseAgent, build_task_message, extract_json  # noqa: F401
from app.agents.prompts import get_prompt
from app.safety import clinical_terms
from app.tools import call_tool
from app.tools.checkins import threshold_reasons


# ---------------------------------------------------------------- Scheduler
class SchedulerResult(BaseModel):
    outcome: Literal["booked", "rescheduled", "approval_requested", "no_slots", "failed"]
    appointment_id: str | None = None
    approval_id: str | None = None
    slot_id: str | None = None
    note: str | None = None


class SchedulerAgent(BaseAgent):
    name, role, result_model = "scheduler", "scheduler", SchedulerResult


# ---------------------------------------------------------------- Follow-up
class FollowUpResult(BaseModel):
    communication_id: str
    approval_id: str


class FollowUpAgent(BaseAgent):
    name, role, result_model = "followup", "followup", FollowUpResult


# ---------------------------------------------------------------- Supply
class SupplyResult(BaseModel):
    outcome: Literal["order_drafted", "no_restock_needed"]
    order_id: str | None = None
    approval_id: str | None = None


class SupplyAgent(BaseAgent):
    name, role, result_model = "supply", "supply", SupplyResult


# ---------------------------------------------------------------- Recovery monitor
class SummaryOut(BaseModel):
    summary: str

    @field_validator("summary")
    @classmethod
    def neutral(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary is empty")
        if terms := clinical_terms(v):
            raise ValueError(f"summary contains clinical/urgency language: {terms}")
        if len(v) > 500:
            raise ValueError("summary too long")
        return v.strip()


class RecoveryResult(BaseModel):
    checkin_id: str
    flagged: bool
    reasons: list[str] = []
    approval_id: str | None = None
    summary: str | None = None
    summary_source: Literal["llm", "template", "none"] = "none"


class RecoveryMonitorAgent(BaseAgent):
    """Thresholds are applied in CODE first. The LLM only writes a neutral staff summary (no tools)."""

    name, role, result_model = "recovery", "recovery", SummaryOut

    def tool_schemas(self) -> list[dict]:  # the summariser model gets no tools at all
        return []

    def parse_final(self, text: str) -> BaseModel:
        return SummaryOut.model_validate(extract_json(text))

    def evaluate(self, checkin_id: str, *, workflow_id: str | None = None, task_key: str | None = None,
                 patient_scope: str | None = None) -> tuple[RecoveryResult, AgentRunResult | None]:
        task_key = task_key or f"{workflow_id}:recovery"
        got = call_tool(self.role, "get_checkins", {"checkin_id": checkin_id}, workflow_id=workflow_id,
                        patient_scope=patient_scope)
        if got.status != "ok" or not got.data or not got.data["items"]:
            return RecoveryResult(checkin_id=checkin_id, flagged=False), AgentRunResult(
                status="FAILED", error=got.error or "check-in not found")
        c = got.data["items"][0]
        reasons = threshold_reasons(c["pain_score"], c["temperature"])  # <- the decision, in code
        if not reasons:
            return RecoveryResult(checkin_id=checkin_id, flagged=False), None

        template = (f"Check-in {checkin_id}: recorded pain score {c['pain_score']}/10, temperature "
                    f"{c['temperature']} C. Fixed threshold(s) exceeded: {'; '.join(reasons)}. Staff review requested.")
        run = self.run({"action": "summarise_flagged_checkin", "checkin_id": checkin_id,
                        "pain_score": c["pain_score"], "temperature": c["temperature"], "reasons": reasons},
                       untrusted={"free_text": c["free_text"]}, workflow_id=workflow_id, task_key=task_key,
                       patient_scope=patient_scope)
        if run.status == "DONE" and run.result:
            summary, source = run.result["summary"], "llm"
        else:  # invalid/failed model output is recorded (run.status) and replaced by a safe template
            summary, source = template, "template"
        flag = call_tool(self.role, "flag_checkin_for_review", {"checkin_id": checkin_id, "summary": summary,
                                                                "idempotency_key": f"{task_key}:flag"},
                         workflow_id=workflow_id, patient_scope=patient_scope)
        if flag.status != "ok":
            return RecoveryResult(checkin_id=checkin_id, flagged=True, reasons=reasons, summary=summary,
                                  summary_source=source), run
        return RecoveryResult(checkin_id=checkin_id, flagged=True, reasons=flag.data["reasons"],
                              approval_id=flag.data["approval_id"], summary=summary, summary_source=source), run


AGENTS = {"scheduler": SchedulerAgent, "followup": FollowUpAgent, "recovery": RecoveryMonitorAgent,
          "supply": SupplyAgent}
_ = (json, get_prompt)
