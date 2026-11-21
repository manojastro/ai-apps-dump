"""End-to-end run on the sandbox: detect -> persist -> propose (LLM) -> queue for human review."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.approval.store import Store
from app.audit import log as audit
from app.core.detection import detect_dir
from app.core.models import ProposalStatus
from app.core.proposer import propose
from app.llm.client import LLMClient
from app.tracing import get_tracer

# A new proposal is only created when the conflict has none, or the last one went stale/failed.
REPROPOSE_FROM = {None, ProposalStatus.STALE.value, ProposalStatus.FAILED.value}


@dataclass
class RunSummary:
    detected: int
    sync: dict
    proposed: int = 0
    failed: int = 0
    skipped_existing: int = 0
    by_type: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def run(store: Store, llm: LLMClient, data_dir: Path, prompt_version: str, limit: int | None = None,
        do_propose: bool = True, actor: str = "pipeline") -> RunSummary:
    tracer = get_tracer()
    with tracer.start_as_current_span("pipeline.run") as span:
        span.set_attribute("tk.prompt_version", prompt_version)
        det = detect_dir(Path(data_dir))
        sync = store.sync_conflicts(det.conflicts, actor=actor)
        summary = RunSummary(detected=len(det.conflicts), sync=sync)
        for c in det.conflicts:
            summary.by_type[c.type.value] = summary.by_type.get(c.type.value, 0) + 1
        if do_propose:
            todo = sorted(det.conflicts, key=lambda c: -(c.impact.amount_usd if c.impact else 0))
            for c in todo:
                if limit is not None and summary.proposed >= limit:
                    break
                if store.latest_proposal_status(c.id) not in REPROPOSE_FROM:
                    summary.skipped_existing += 1
                    continue
                r = propose(c, llm, prompt_version)
                store.save_proposal(r, actor=actor)
                summary.proposed += 1
                summary.failed += int(r.status == ProposalStatus.FAILED)
        with store.Session.begin() as s:
            audit.append(s, actor=actor, event="pipeline_run", entity_type="run", entity_id="sandbox",
                         details={**summary.to_dict(), "prompt_version": prompt_version, "llm_mode": llm.mode})
        span.set_attribute("tk.detected", summary.detected)
        span.set_attribute("tk.proposed", summary.proposed)
        return summary
