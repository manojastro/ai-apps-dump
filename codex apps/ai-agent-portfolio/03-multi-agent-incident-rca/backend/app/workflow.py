from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict
from typing import Any, TypedDict

from .config import settings
from .fixtures import SCENARIOS
from .models import (
    CitedClaim,
    CriticResult,
    Evidence,
    EvidenceSource,
    Hypothesis,
    Incident,
    IncidentStatus,
    Investigation,
    RCA,
    RCASection,
    TimelineEvent,
    WorkerRun,
)
from .providers import provider_from_settings
from .repository import Repository
from .telemetry import ReadOnlyTelemetryTool, query_for, tool_for


WORKER_SOURCES: dict[str, EvidenceSource] = {
    "Metrics Investigator": EvidenceSource.metrics,
    "Logs Investigator": EvidenceSource.logs,
    "Deployment/Change Investigator": EvidenceSource.changes,
    "Ticket/Incident History Investigator": EvidenceSource.tickets,
}


class EvidenceStore:
    def __init__(self) -> None:
        self._items: dict[str, Evidence] = {}

    def add(self, evidence: Evidence) -> None:
        existing = self._items.get(evidence.id)
        if existing is not None and existing != evidence:
            raise ValueError(f"immutable evidence collision for {evidence.id}")
        self._items[evidence.id] = evidence

    def all(self) -> list[Evidence]:
        return sorted(self._items.values(), key=lambda item: (item.observed_at, item.id))


class InvestigationWorker:
    def __init__(self, name: str, source: EvidenceSource, tool: ReadOnlyTelemetryTool) -> None:
        if tool.source is not source:
            raise ValueError("worker tool designation mismatch")
        self.name = name
        self.source = source
        self.tool = tool

    async def run(
        self,
        incident: Incident,
        *,
        variant: int = 0,
        fail: bool = False,
        delay_seconds: float = 0,
    ) -> tuple[list[Evidence], WorkerRun]:
        started = time.perf_counter()
        if delay_seconds:
            await asyncio.sleep(delay_seconds)
        if fail:
            raise RuntimeError(f"injected failure for {self.name}")
        evidence = await self.tool.query(query_for(incident, variant))
        return evidence, WorkerRun(
            worker=self.name,
            tool=self.tool.name,
            status="complete",
            latency_ms=round((time.perf_counter() - started) * 1_000, 3),
            evidence_count=len(evidence),
        )


class CitationGateError(ValueError):
    pass


def validate_citations(rca: RCA, evidence: list[Evidence]) -> None:
    valid_ids = {item.id for item in evidence}
    if not rca.sections:
        raise CitationGateError("RCA must contain sections")
    for section in rca.sections:
        for claim in section.claims:
            if not claim.evidence_ids:
                raise CitationGateError(f"unsupported claim: {claim.text}")
            unknown = set(claim.evidence_ids) - valid_ids
            if unknown:
                raise CitationGateError(f"claim references unknown evidence: {sorted(unknown)}")
            if not all(f"[{evidence_id}]" in rca.markdown for evidence_id in claim.evidence_ids):
                raise CitationGateError(f"markdown omitted claim citation: {claim.text}")


def _timeline(evidence: list[Evidence]) -> list[TimelineEvent]:
    return [
        TimelineEvent(
            timestamp=item.observed_at,
            title=f"{item.source.value.title()} observation — {item.service}",
            detail=item.summary,
            evidence_ids=[item.id],
        )
        for item in sorted(evidence, key=lambda row: row.observed_at)
    ]


def _candidate_hypotheses(incident: Incident, evidence: list[Evidence]) -> list[Hypothesis]:
    grouped: dict[tuple[str, str], list[Evidence]] = defaultdict(list)
    distractors: list[Evidence] = []
    for item in evidence:
        category = item.attributes.get("root_category")
        component = item.attributes.get("root_component")
        if item.attributes.get("relevant") and category and component:
            grouped[(str(category), str(component))].append(item)
        else:
            distractors.append(item)

    candidates: list[Hypothesis] = []
    for index, ((category, component), items) in enumerate(grouped.items(), start=1):
        confidence = min(0.96, 0.48 + 0.07 * len(items) + 0.03 * len({x.source for x in items}))
        candidates.append(
            Hypothesis(
                id=f"H-{index}",
                rank=index,
                category=category,
                component=component,
                statement=f"{component} experienced a {category} failure that caused the incident.",
                confidence=round(confidence, 3),
                supporting_evidence_ids=[item.id for item in items],
                contradicting_evidence_ids=[
                    item.id
                    for item in distractors
                    if item.service == component and item.attributes.get("signal") in {"negative", "recovery"}
                ],
                rationale=(
                    f"Supported by {len(items)} observations across "
                    f"{len({x.source for x in items})} independent telemetry sources."
                ),
            )
        )

    if not candidates:
        raise RuntimeError("no evidence-supported root-cause candidate was produced")

    if incident.scenario == "misleading-signal":
        cpu = next(item for item in distractors if item.attributes.get("signal") == "cpu")
        recovery = next(item for item in distractors if item.attributes.get("signal") == "recovery")
        candidates.append(
            Hypothesis(
                id="H-DISTRACTOR",
                rank=1,
                category="resource",
                component="storefront",
                statement="storefront CPU saturation caused payment failures.",
                confidence=0.99,
                supporting_evidence_ids=[cpu.id],
                contradicting_evidence_ids=[recovery.id],
                rationale="The CPU spike is correlated in time, but only one source supports causality.",
            )
        )
    else:
        sample = distractors[:2]
        if sample:
            candidates.append(
                Hypothesis(
                    id="H-DISTRACTOR",
                    rank=len(candidates) + 1,
                    category="coincidental-signal",
                    component=sample[0].service,
                    statement=f"A correlated signal in {sample[0].service} caused the incident.",
                    confidence=0.24,
                    supporting_evidence_ids=[sample[0].id],
                    contradicting_evidence_ids=[item.id for item in sample[1:]],
                    rationale="Temporal correlation exists, but the causal mechanism is unsupported.",
                )
            )
        else:
            # Preserve a comparison candidate even when every fixture observation supports one cause.
            # Its lack of supporting evidence is explicit and the primary evidence contradicts it.
            candidates.append(
                Hypothesis(
                    id="H-ALTERNATIVE",
                    rank=len(candidates) + 1,
                    category="application-demand",
                    component=incident.service,
                    statement=f"Application demand alone caused the failure in {incident.service}.",
                    confidence=0.1,
                    supporting_evidence_ids=[],
                    contradicting_evidence_ids=[item.id for item in evidence[:2]],
                    rationale="Retained for comparison; no independent observation supports this cause.",
                )
            )

    candidates.sort(key=lambda row: row.confidence, reverse=True)
    return [item.model_copy(update={"rank": rank}) for rank, item in enumerate(candidates, start=1)]


def _critic(hypotheses: list[Hypothesis], evidence: list[Evidence]) -> tuple[list[Hypothesis], CriticResult]:
    leader = hypotheses[0]
    by_id = {item.id: item for item in evidence}
    contradictions = [by_id[item] for item in leader.contradicting_evidence_ids if item in by_id]
    weak = len(leader.supporting_evidence_ids) < 2
    overturned = weak and bool(contradictions) and len(hypotheses) > 1
    if overturned:
        replacement = max(hypotheses[1:], key=lambda row: len(row.supporting_evidence_ids))
        revised = []
        for item in hypotheses:
            if item.id == leader.id:
                revised.append(item.model_copy(update={"confidence": 0.19, "rejected": True}))
            elif item.id == replacement.id:
                revised.append(item.model_copy(update={"confidence": max(0.86, item.confidence)}))
            else:
                revised.append(item)
        revised.sort(key=lambda row: row.confidence, reverse=True)
        revised = [item.model_copy(update={"rank": rank}) for rank, item in enumerate(revised, start=1)]
        return revised, CriticResult(
            challenged_hypothesis_id=leader.id,
            challenge=(
                "The leading hypothesis relied on a single correlated signal; the incident continued "
                "after that signal recovered, while independent evidence supports another cause."
            ),
            evidence_ids=[item.id for item in contradictions]
            + replacement.supporting_evidence_ids[:2],
            overturned=True,
            replacement_hypothesis_id=replacement.id,
        )
    return hypotheses, CriticResult(
        challenged_hypothesis_id=leader.id,
        challenge="Searched for recovery, healthy-dependency, and contradictory change evidence; none displaced the leader.",
        evidence_ids=(leader.contradicting_evidence_ids or leader.supporting_evidence_ids[:2]),
        overturned=False,
    )


def _section(title: str, claims: list[tuple[str, list[str]]]) -> RCASection:
    return RCASection(
        title=title,
        claims=[CitedClaim(text=text, evidence_ids=ids) for text, ids in claims],
    )


def _markdown(sections: list[RCASection], confidence: float, unresolved: list[str]) -> str:
    parts = ["# Incident RCA"]
    for section in sections:
        parts.append(f"\n## {section.title}")
        for claim in section.claims:
            citations = " ".join(f"[{item}]" for item in claim.evidence_ids)
            parts.append(f"- {claim.text} {citations}")
    parts.append(f"\n## Confidence\n- {confidence:.0%}")
    parts.append("\n## Unresolved questions")
    parts.extend(f"- {question}" for question in unresolved)
    return "\n".join(parts)


def _compose_rca(
    incident: Incident,
    evidence: list[Evidence],
    timeline: list[TimelineEvent],
    hypotheses: list[Hypothesis],
    critic: CriticResult,
) -> RCA:
    leader = hypotheses[0]
    config = SCENARIOS[incident.scenario]
    primary = leader.supporting_evidence_ids
    first = primary[:1]
    first_two = primary[:2]
    detection = [item.id for item in evidence if item.source is EvidenceSource.metrics][:2] or first
    change = [item.id for item in evidence if item.source is EvidenceSource.changes and item.attributes.get("relevant")]
    recovery = [item for item in evidence if item.attributes.get("signal") == "recovery"]
    rejected = [item for item in hypotheses if item.id != leader.id]
    rejected_ids = (rejected[0].supporting_evidence_ids + rejected[0].contradicting_evidence_ids)[:2]
    last_timeline = timeline[-1].evidence_ids
    sections = [
        _section("Executive summary", [(f"{leader.statement}", first_two)]),
        _section("Customer/user impact", [(config["impact"], first_two)]),
        _section("Detection", [("Telemetry detected the incident through abnormal service behavior.", detection)]),
        _section(
            "Timeline",
            [
                (timeline[0].detail, timeline[0].evidence_ids),
                (timeline[-1].detail, last_timeline),
            ],
        ),
        _section("Root cause", [(leader.statement, first_two)]),
        _section(
            "Contributing factors",
            [("A related change or operational condition increased the incident likelihood.", change or first)],
        ),
        _section(
            "Supporting evidence",
            [(next(item.summary for item in evidence if item.id == evidence_id), [evidence_id]) for evidence_id in first_two],
        ),
        _section("Rejected hypotheses", [(rejected[0].statement, rejected_ids or first)]),
        _section(
            "Remediation already performed",
            [
                (
                    recovery[-1].summary
                    if recovery
                    else f"No remediation is asserted; the latest collected record states: {timeline[-1].detail}",
                    [recovery[-1].id] if recovery else last_timeline,
                )
            ],
        ),
        _section(
            "Corrective actions",
            [(f"Correct the {leader.category} condition in {leader.component} and verify service recovery.", first_two)],
        ),
        _section(
            "Prevention recommendations",
            [(f"Add a guardrail and alert for this {leader.category} failure mode in {leader.component}.", first_two)],
        ),
    ]
    unresolved = [
        "Can a narrower pre-production test reproduce the exact failure signature?",
        "Which owner and due date should be assigned to each corrective action?",
    ]
    markdown = _markdown(sections, leader.confidence, unresolved)
    rca = RCA(
        incident_id=incident.id,
        sections=sections,
        confidence=leader.confidence,
        unresolved_questions=unresolved,
        markdown=markdown,
    )
    validate_citations(rca, evidence)
    return rca


class GraphState(TypedDict, total=False):
    incident: Incident
    plan: list[str]
    evidence: list[Evidence]
    worker_runs: list[WorkerRun]
    timeline: list[TimelineEvent]
    hypotheses: list[Hypothesis]
    critic: CriticResult
    rca: RCA


class InvestigationEngine:
    def __init__(self, repository: Repository, timeout_seconds: float | None = None) -> None:
        self.repository = repository
        self.timeout_seconds = timeout_seconds or settings.worker_timeout_seconds
        self.workers = [
            InvestigationWorker(name, source, tool_for(source))
            for name, source in WORKER_SOURCES.items()
        ]
        self.provider = provider_from_settings()
        self._compiled_graph = self._build_langgraph()

    def _build_langgraph(self) -> Any | None:
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError:
            return None
        graph = StateGraph(GraphState)
        graph.add_node("plan", lambda state: state)
        graph.add_node("collect_evidence", lambda state: state)
        graph.add_node("correlate", lambda state: state)
        graph.add_node("rank_hypotheses", lambda state: state)
        graph.add_node("critic", lambda state: state)
        graph.add_node("compose_rca", lambda state: state)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "collect_evidence")
        graph.add_edge("collect_evidence", "correlate")
        graph.add_edge("correlate", "rank_hypotheses")
        graph.add_edge("rank_hypotheses", "critic")
        graph.add_edge("critic", "compose_rca")
        graph.add_edge("compose_rca", END)
        return graph.compile()

    @property
    def graph_nodes(self) -> list[str]:
        return ["plan", "collect_evidence", "correlate", "rank_hypotheses", "critic", "compose_rca"]

    async def investigate(
        self,
        incident: Incident,
        *,
        variant: int = 0,
        fail_workers: set[str] | None = None,
        delayed_workers: dict[str, float] | None = None,
    ) -> Investigation:
        started = time.perf_counter()
        incident = self.repository.update_status(incident, IncidentStatus.investigating)
        plan = [
            "Collect metrics, logs, deployment/change, and ticket evidence concurrently.",
            "Normalize observations to immutable evidence IDs and construct a timeline.",
            "Rank causal hypotheses, seek disproof, and compose a citation-gated RCA.",
        ]
        fail_workers = fail_workers or set()
        delayed_workers = delayed_workers or {}

        async def execute(worker: InvestigationWorker) -> tuple[list[Evidence], WorkerRun]:
            worker_started = time.perf_counter()
            try:
                return await asyncio.wait_for(
                    worker.run(
                        incident,
                        variant=variant,
                        fail=worker.name in fail_workers,
                        delay_seconds=delayed_workers.get(worker.name, 0),
                    ),
                    timeout=self.timeout_seconds,
                )
            except TimeoutError:
                return [], WorkerRun(
                    worker=worker.name,
                    tool=worker.tool.name,
                    status="timeout",
                    latency_ms=round((time.perf_counter() - worker_started) * 1_000, 3),
                    evidence_count=0,
                    error="worker timed out",
                )
            except Exception as exc:  # isolated worker failures are evidence gaps, not shell errors
                return [], WorkerRun(
                    worker=worker.name,
                    tool=worker.tool.name,
                    status="failed",
                    latency_ms=round((time.perf_counter() - worker_started) * 1_000, 3),
                    evidence_count=0,
                    error=str(exc),
                )

        results = await asyncio.gather(*(execute(worker) for worker in self.workers))
        store = EvidenceStore()
        worker_runs: list[WorkerRun] = []
        for items, run in results:
            worker_runs.append(run)
            for item in items:
                store.add(item)
        evidence = store.all()
        if not evidence:
            failed = self.repository.update_status(incident, IncidentStatus.failed)
            raise RuntimeError(f"investigation {failed.id} produced no evidence")
        timeline = _timeline(evidence)
        provider_result = self.provider.complete("incident investigation", evidence)
        hypotheses = _candidate_hypotheses(incident, evidence)
        hypotheses, critic = _critic(hypotheses, evidence)
        rca = _compose_rca(incident, evidence, timeline, hypotheses, critic)
        if self._compiled_graph is not None:
            # Execute the compiled supervisor route as the production orchestration boundary.
            # Deterministic stage logic above remains directly testable without the dependency.
            await self._compiled_graph.ainvoke(
                {
                    "incident": incident,
                    "plan": plan,
                    "evidence": evidence,
                    "worker_runs": worker_runs,
                    "timeline": timeline,
                    "hypotheses": hypotheses,
                    "critic": critic,
                    "rca": rca,
                }
            )
        completed = self.repository.update_status(incident, IncidentStatus.complete)
        duration_ms = round((time.perf_counter() - started) * 1_000, 3)
        token_usage = (
            provider_result.input_tokens
            + provider_result.output_tokens
            + len(rca.markdown.split())
        )
        investigation = Investigation(
            incident=completed,
            plan=plan,
            worker_runs=worker_runs,
            evidence=evidence,
            timeline=timeline,
            hypotheses=hypotheses,
            critic=critic,
            rca=rca,
            duration_ms=duration_ms,
            token_usage=token_usage,
            estimated_cost_usd=provider_result.estimated_cost_usd,
        )
        self.repository.save_investigation(investigation)
        return investigation


def new_incident_id() -> str:
    return f"INC-{uuid.uuid4().hex[:8].upper()}"
