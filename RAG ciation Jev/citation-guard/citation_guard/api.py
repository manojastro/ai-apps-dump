"""Local API. No auth: bind to localhost only (see docs/DESIGN.md for what auth would need)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import load_config
from .ingest import load_document
from .judges import JUDGE_NAMES, BudgetExceeded
from .pipeline import ClaimIn, JudgeUnavailable, VerifyResult, verify_answer

app = FastAPI(title="Citation Guard", version="0.1.0")


class VerifyRequest(BaseModel):
    doc_id: str
    answer: str = ""
    claims: list[ClaimIn] = Field(default_factory=list)
    judge: str | None = None  # defaults to config api.judge


@app.get("/health")
def health() -> dict:
    cfg = load_config()
    return {"status": "ok", "judge": cfg.api.judge, "jev_model": cfg.jev.model}


@app.post("/v1/verify", response_model=VerifyResult)
async def verify(req: VerifyRequest) -> VerifyResult:
    cfg = load_config()
    judge = req.judge or cfg.api.judge
    if judge not in JUDGE_NAMES:
        raise HTTPException(422, f"judge must be one of {JUDGE_NAMES}")
    try:
        doc = load_document(req.doc_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    try:
        return await verify_answer(doc, req.claims, judge, cfg)
    except BudgetExceeded as e:
        raise HTTPException(413, str(e))
    except JudgeUnavailable as e:
        raise HTTPException(503, str(e))
    except Exception as e:  # e.g. TypeSafeError: missing key
        if type(e).__name__ == "TypeSafeError":
            raise HTTPException(503, f"Jev unavailable: {e}")
        raise
