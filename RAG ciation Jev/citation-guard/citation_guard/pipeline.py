"""verify(answer) end to end: Check A -> (passage window -> judge) -> gate -> decision log."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .config import Config
from .gate import AnswerResult, Thresholds, Verdict, answer_result, claim_verdict, stringmatch_verdict
from .ingest import Document
from .judges.base import CallBudget, Judge
from .quote_match import QuoteStatus, match_quote, offsets_for_log, passage_window


# Errors that mean the judge cannot work at all (bad key, no access, wrong model). A run
# that hits one stops: writing it out as per-claim HUMAN_REVIEW would look like a result.
FATAL_ERRORS = {
    "AuthenticationError", "PermissionDeniedError", "NotFoundError",
    "TypeSafeAuthenticationError", "TypeSafePermissionDeniedError", "TypeSafeNotFoundError",
}


class JudgeUnavailable(RuntimeError):
    pass


class ClaimIn(BaseModel):
    claim_id: str
    claim: str
    quote: str
    section_id: str | None = None


class ClaimDecision(BaseModel):
    run_id: str
    mode: str  # LIVE | MOCK | NO-MODEL
    judge: str
    model: str | None
    request_id: str | None = None
    doc_id: str
    claim_id: str
    cited_section_id: str | None
    quote_status: QuoteStatus
    found_section_id: str | None = None
    quote_occurrences: int = 0
    offsets: dict | None = None
    closest_fuzzy_score: float | None = None  # debug only
    judge_called: bool = False
    probabilities: dict[str, float] | None = None
    confidence: float | None = None
    top_label: str | None = None
    verdict: Verdict
    thresholds: Thresholds
    latency_ms: float  # whole claim: Check A + judge
    judge_latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    mock: bool = False
    error: str | None = None
    timestamp: str
    # Evaluation-only fields (None outside `eval`).
    label: str | None = None
    label_source: str | None = None
    split: str | None = None
    origin: str | None = None


class VerifyResult(BaseModel):
    run_id: str
    mode: str
    judge: str
    answer_result: AnswerResult
    claims: list[ClaimDecision]


def run_mode(judge_name: str) -> str:
    if judge_name == "mock":
        return "MOCK"
    if judge_name == "stringmatch":
        return "NO-MODEL"
    return "LIVE"


def new_run_id(judge_name: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{judge_name}-{uuid.uuid4().hex[:6]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


async def verify_claims(
    doc: Document,
    claims: list[ClaimIn],
    judge: Judge | None,
    cfg: Config,
    *,
    judge_name: str,
    run_id: str,
    thresholds: Thresholds | None = None,
    budget: CallBudget | None = None,
    extras: dict[str, dict[str, Any]] | None = None,
) -> list[ClaimDecision]:
    """Verify claims against one document. `judge=None` means the string-match baseline.

    The judge must already be entered (`async with judge:`)."""
    th = thresholds or Thresholds(**cfg.gate.model_dump())
    mode = run_mode(judge_name)
    extras = extras or {}
    budget = budget or CallBudget(cfg.run.max_api_calls_per_run)

    # Phase 1: Check A for every claim (no model).
    checked = []
    for c in claims:
        t0 = time.perf_counter()
        m = match_quote(doc, c.quote, c.section_id, cfg.quote.min_chars)
        checked.append((c, m, (time.perf_counter() - t0) * 1000))

    to_judge = [
        i for i, (_, m, _) in enumerate(checked)
        if judge is not None and m.status in (QuoteStatus.FOUND_IN_CITED_SECTION, QuoteStatus.FOUND_ELSEWHERE)
    ]
    # Cost cap: stop before any call if this run would exceed it.
    if judge is not None and judge.is_live:
        budget.check(len(to_judge))

    sem = asyncio.Semaphore(max(1, cfg.run.concurrency))
    results: dict[int, tuple[Any, str | None]] = {}

    async def run_one(i: int) -> None:
        c, m, _ = checked[i]
        passage = passage_window(doc, m.start, m.end, cfg.passage.window_chars)
        async with sem:
            if judge.is_live:
                budget.take(1)
            try:
                results[i] = (await judge.judge(c.claim, c.quote, passage.text), None)
            except Exception as e:
                if type(e).__name__ in FATAL_ERRORS:
                    raise JudgeUnavailable(f"{type(e).__name__}: {e}") from e
                # Any other judge failure -> HUMAN_REVIEW, never a silent PASS.
                results[i] = (None, f"{type(e).__name__}: {e}")

    await asyncio.gather(*(run_one(i) for i in to_judge))
    if to_judge and all(results[i][0] is None for i in to_judge):
        first = results[to_judge[0]][1]
        raise JudgeUnavailable(f"every judge call failed (first error: {first})")

    decisions: list[ClaimDecision] = []
    for i, (c, m, a_ms) in enumerate(checked):
        jr, err = results.get(i, (None, None))
        if judge is None:
            verdict = stringmatch_verdict(m.status)
        else:
            verdict = claim_verdict(m.status, jr.probabilities if jr else None, th)
        ex = extras.get(c.claim_id, {})
        decisions.append(
            ClaimDecision(
                run_id=run_id,
                mode=mode,
                judge=judge_name,
                model=(jr.model if jr else getattr(judge, "model", None)) if judge is not None else None,
                request_id=jr.request_id if jr else None,
                doc_id=doc.doc_id,
                claim_id=c.claim_id,
                cited_section_id=c.section_id,
                quote_status=m.status,
                found_section_id=m.found_section_id,
                quote_occurrences=m.occurrences,
                offsets=offsets_for_log(doc, m),
                closest_fuzzy_score=m.closest_fuzzy_score,
                judge_called=i in to_judge,
                probabilities=jr.probabilities if jr else None,
                confidence=jr.confidence if jr else None,
                top_label=jr.top_label if jr else None,
                verdict=verdict,
                thresholds=th,
                latency_ms=a_ms + (jr.latency_ms if jr else 0.0),
                judge_latency_ms=jr.latency_ms if jr else None,
                input_tokens=jr.input_tokens if jr else None,
                output_tokens=jr.output_tokens if jr else None,
                # No judge call -> no cost. A failed call has unknown cost (None).
                estimated_cost_usd=jr.estimated_cost_usd if jr else (None if i in to_judge else 0.0),
                mock=bool(jr.mock) if jr else judge_name == "mock",
                error=err,
                timestamp=_now(),
                label=ex.get("label"),
                label_source=ex.get("label_source"),
                split=ex.get("split"),
                origin=ex.get("origin"),
            )
        )
    return decisions


def write_decisions(run_dir: Path, decisions: list[ClaimDecision]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "decisions.jsonl"
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        for d in decisions:
            fh.write(d.model_dump_json() + "\n")
    return path


def read_decisions(run_dir: Path) -> list[ClaimDecision]:
    path = run_dir / "decisions.jsonl"
    with open(path, encoding="utf-8") as fh:
        return [ClaimDecision.model_validate(json.loads(line)) for line in fh if line.strip()]


async def verify_answer(
    doc: Document,
    claims: list[ClaimIn],
    judge_name: str,
    cfg: Config,
    *,
    judge: Judge | None = None,
    run_dir: Path | None = None,
) -> VerifyResult:
    """Convenience wrapper: builds/enters the judge, verifies, aggregates, optionally logs."""
    from .judges import make_judge

    run_id = run_dir.name if run_dir else new_run_id(judge_name)
    j = judge if judge is not None else make_judge(judge_name, cfg)
    if j is None:
        decisions = await verify_claims(doc, claims, None, cfg, judge_name=judge_name, run_id=run_id)
    else:
        async with j:
            decisions = await verify_claims(doc, claims, j, cfg, judge_name=judge_name, run_id=run_id)
    if run_dir:
        write_decisions(run_dir, decisions)
    return VerifyResult(
        run_id=run_id,
        mode=run_mode(judge_name),
        judge=judge_name,
        answer_result=answer_result([d.verdict for d in decisions]),
        claims=decisions,
    )
