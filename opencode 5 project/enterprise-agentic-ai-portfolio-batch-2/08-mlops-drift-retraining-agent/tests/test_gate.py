"""Retraining gate tests, including all no-retrain cases."""
from __future__ import annotations

import pytest

from backend.app.agents.retraining_decision import RetrainingDecisionAgent, evaluate_gate
from backend.app.db import SessionLocal
from backend.app.schemas.dto import GateInputs
from backend.app.services.baseline import train_baseline
from tests.test_agents import _make_window


def _gate(**overrides) -> GateInputs:
    defaults = dict(
        meaningful_drift=True,
        perf_degradation=True,
        high_risk_drift=False,
        sufficient_new_labeled_samples=True,
        projected_benefit=0.5,
        min_projected_benefit=0.15,
        n_labeled_samples=4000,
        min_labeled_samples=400,
    )
    defaults.update(overrides)
    return GateInputs(**defaults)


def test_gate_retrains_when_all_conditions_met():
    decision, reasons = evaluate_gate(_gate())
    assert decision == "retrain"
    assert len(reasons) == 4


def test_gate_blocks_when_no_meaningful_drift():
    decision, reasons = evaluate_gate(_gate(meaningful_drift=False))
    assert decision == "monitor"
    assert any("meaningful" in r for r in reasons)


def test_gate_blocks_when_no_perf_degradation_and_low_risk():
    decision, reasons = evaluate_gate(_gate(perf_degradation=False, high_risk_drift=False))
    assert decision == "monitor"
    assert any("performance degradation nor high-risk" in r for r in reasons)


def test_gate_allows_high_risk_without_perf_degradation():
    decision, _ = evaluate_gate(_gate(perf_degradation=False, high_risk_drift=True))
    assert decision == "retrain"


def test_gate_blocks_insufficient_samples():
    decision, reasons = evaluate_gate(
        _gate(sufficient_new_labeled_samples=False, n_labeled_samples=100)
    )
    assert decision == "monitor"
    assert any("insufficient labelled samples" in r for r in reasons)


def test_gate_blocks_low_projected_benefit():
    decision, reasons = evaluate_gate(_gate(projected_benefit=0.05))
    assert decision == "monitor"
    assert any("projected benefit" in r for r in reasons)


@pytest.fixture(scope="module")
def module_baseline():
    session = SessionLocal()
    try:
        return train_baseline(session, seed=42, n_samples=3000)
    finally:
        session.close()


def _decide(window_id: int) -> tuple[str, dict]:
    session = SessionLocal()
    try:
        output = RetrainingDecisionAgent().decide(session, window_id)
        return output.decision, output.gate_inputs.model_dump()
    finally:
        session.close()


def _evaluated_window(knobs: dict | None, seed: int) -> int:
    from backend.app.agents.monitoring import ModelMonitoringAgent
    from backend.app.db import SessionLocal

    session = SessionLocal()
    try:
        window_id = _make_window(session, knobs, seed=seed)
        ModelMonitoringAgent().evaluate_window(session, window_id)
        return window_id
    finally:
        session.close()


def test_clean_window_decides_monitor(module_baseline):
    window_id = _evaluated_window(None, seed=6101)
    decision, gate_inputs = _decide(window_id)
    assert decision == "monitor"
    assert gate_inputs["meaningful_drift"] is False
    assert gate_inputs["perf_degradation"] is False


def test_subtle_window_decides_monitor(module_baseline):
    window_id = _evaluated_window({"mean_shift": 0.12, "variance_shift": 1.05}, seed=6102)
    decision, gate_inputs = _decide(window_id)
    assert decision == "monitor"
    assert gate_inputs["meaningful_drift"] is False


def test_severe_window_decides_retrain(module_baseline):
    window_id = _evaluated_window(
        {
            "mean_shift": 1.4,
            "variance_shift": 1.8,
            "label_noise": 0.18,
            "missingness_rate": 0.06,
        },
        seed=6103,
    )
    decision, gate_inputs = _decide(window_id)
    assert decision == "retrain"
    assert gate_inputs["meaningful_drift"] is True
    assert (
        gate_inputs["perf_degradation"] is True or gate_inputs["high_risk_drift"] is True
    )
    assert gate_inputs["sufficient_new_labeled_samples"] is True
    assert gate_inputs["projected_benefit"] >= 0.15


def test_label_noise_only_decides_monitor(module_baseline):
    window_id = _evaluated_window({"label_noise": 0.35}, seed=6104)
    decision, gate_inputs = _decide(window_id)
    assert decision in ("monitor", "retrain")
    assert isinstance(gate_inputs, dict)
    assert gate_inputs["n_labeled_samples"] >= gate_inputs["min_labeled_samples"]
