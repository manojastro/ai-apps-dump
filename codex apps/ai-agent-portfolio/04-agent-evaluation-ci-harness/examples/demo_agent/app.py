from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel

from evalharness.models import TestCase
from evalharness.targets import DemoAgentTarget

app = FastAPI(title="Deterministic Demo Agent")


class Request(BaseModel):
    case: dict


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": os.getenv("DEMO_AGENT_MODE", "good")}


@app.post("/evaluate")
def evaluate(request: Request) -> dict:
    target = DemoAgentTarget(os.getenv("DEMO_AGENT_MODE", "good"))
    return target.invoke(TestCase.from_dict(request.case)).to_dict()

