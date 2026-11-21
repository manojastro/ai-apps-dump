from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pydantic import BaseModel
from sqlalchemy.orm import Session


class ToolError(Exception):
    """Validation / business-rule failure (reported to the caller as status=error)."""


class ScopeViolation(Exception):
    """Caller touched data outside the patient scope of its task (reported as status=denied)."""


@dataclass
class ToolContext:
    session: Session
    role: str
    workflow_id: str | None = None
    patient_scope: str | None = None

    def check_patient(self, patient_id: str | None) -> None:
        if self.patient_scope and patient_id and patient_id != self.patient_scope:
            raise ScopeViolation(f"task is scoped to {self.patient_scope}; access to {patient_id} denied")


class MutatingInput(BaseModel):
    """Inputs of state-changing tools. The agent loop injects the key; models never invent it."""

    idempotency_key: str | None = None


@dataclass
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    fn: Callable[[ToolContext, BaseModel], BaseModel]
    mutating: bool = False
    extra: dict = field(default_factory=dict)

    def llm_schema(self) -> dict:
        schema = self.input_model.model_json_schema()
        schema.get("properties", {}).pop("idempotency_key", None)
        return {"name": self.name, "description": self.description, "input_schema": schema}


REGISTRY: dict[str, ToolSpec] = {}


def register(name: str, description: str, input_model: type[BaseModel]):
    def deco(fn):
        REGISTRY[name] = ToolSpec(name, description, input_model, fn, mutating=issubclass(input_model, MutatingInput))
        return fn

    return deco
