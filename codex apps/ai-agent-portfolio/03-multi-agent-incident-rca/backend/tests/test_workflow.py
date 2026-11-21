from __future__ import annotations

import pytest

from app.models import CitedClaim, RCASection
from app.workflow import CitationGateError, validate_citations
from conftest import make_incident


def test_graph_has_supervisor_stages(engine):
    assert engine.graph_nodes == [
        "plan",
        "collect_evidence",
        "correlate",
        "rank_hypotheses",
        "critic",
        "compose_rca",
    ]


@pytest.mark.asyncio
async def test_workers_run_and_correlation_orders_timeline(engine, incident):
    result = await engine.investigate(incident)
    assert len(result.worker_runs) == 4
    assert {run.status for run in result.worker_runs} == {"complete"}
    assert result.timeline == sorted(result.timeline, key=lambda event: event.timestamp)
    assert len({item.id for item in result.evidence}) == len(result.evidence)
    assert result.hypotheses[0].category == "deployment"
    validate_citations(result.rca, result.evidence)


@pytest.mark.asyncio
async def test_critic_overturns_obvious_but_wrong_signal(engine, repository):
    incident = make_incident("misleading-signal", "MISLEAD")
    repository.save_incident(incident)
    result = await engine.investigate(incident)
    assert result.critic.overturned is True
    assert result.critic.replacement_hypothesis_id
    assert result.hypotheses[0].category == "dependency"
    assert result.hypotheses[0].component == "payment-api"
    assert any(hypothesis.rejected for hypothesis in result.hypotheses)


@pytest.mark.asyncio
async def test_citation_gate_rejects_unknown_reference(engine, incident):
    result = await engine.investigate(incident)
    claim = CitedClaim(text="Unsupported fabricated claim", evidence_ids=["EV-FFFFFFFFFFFF"])
    bad_section = RCASection(title="Bad", claims=[claim])
    invalid = result.rca.model_copy(update={"sections": [bad_section], "markdown": "[EV-FFFFFFFFFFFF]"})
    with pytest.raises(CitationGateError, match="unknown evidence"):
        validate_citations(invalid, result.evidence)


@pytest.mark.asyncio
async def test_worker_failure_isolated_when_other_evidence_exists(engine, incident):
    result = await engine.investigate(incident, fail_workers={"Ticket/Incident History Investigator"})
    assert next(run for run in result.worker_runs if run.worker.startswith("Ticket")).status == "failed"
    assert result.incident.status.value == "complete"


@pytest.mark.asyncio
async def test_worker_timeout_is_recorded(engine, incident):
    result = await engine.investigate(
        incident,
        delayed_workers={"Ticket/Incident History Investigator": 0.2},
    )
    ticket = next(run for run in result.worker_runs if run.worker.startswith("Ticket"))
    assert ticket.status == "timeout"
    assert ticket.error == "worker timed out"

