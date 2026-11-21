"""Drift scenario simulator producing staged monitoring windows over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

SEVERE_KNOBS: dict[str, Any] = {
    "mean_shift": 1.4,
    "variance_shift": 1.8,
    "label_noise": 0.18,
    "missingness_rate": 0.06,
    "new_segment_share": 0.45,
}
SUBTLE_KNOBS: dict[str, Any] = {"mean_shift": 0.12, "variance_shift": 1.05}


class ClientLike(Protocol):
    def post(self, path: str, json: Any = None) -> Any: ...

    def get(self, path: str) -> Any: ...


@dataclass
class StageResult:
    stage: str
    window_id: int
    alert: bool
    drift_count: int
    max_psi: float
    f1: float
    decision: str | None = None
    reasons: list[str] = field(default_factory=list)
    gate_inputs: dict = field(default_factory=dict)


@dataclass
class ScenarioReport:
    baseline_version: str
    baseline_metrics: dict
    stages: list[StageResult] = field(default_factory=list)
    candidate_version: str | None = None
    candidate_verdict: str | None = None
    bad_candidate_version: str | None = None
    bad_candidate_verdict: str | None = None
    promotion_state: str | None = None
    champion_after: str | None = None


class DriftSimulator:
    """Drives the full API workflow across clean, subtle and severe windows."""

    def __init__(self, client: ClientLike) -> None:
        self.client = client

    def train_baseline(self, seed: int = 42, n_samples: int = 6000) -> dict:
        response = self.client.post(
            "/api/v1/models/train-baseline",
            json={"seed": seed, "n_samples": n_samples},
        )
        return response.json()

    def submit_and_evaluate(
        self, name: str, step: int, knobs: dict, n_samples: int = 4000, seed: int | None = None
    ) -> tuple[dict, dict]:
        payload: dict[str, Any] = {"name": name, "step": step, "n_samples": n_samples, "knobs": knobs}
        if seed is not None:
            payload["seed"] = seed
        window = self.client.post("/api/v1/monitoring/windows", json=payload).json()
        evaluation = self.client.post(
            f"/api/v1/monitoring/windows/{window['id']}/evaluate", json={}
        ).json()
        return window, evaluation

    def decide(self, window_id: int) -> dict:
        return self.client.post("/api/v1/retraining/decide", json={"window_id": window_id}).json()

    def investigate(self, window_id: int) -> dict:
        return self.client.post(f"/api/v1/retraining/investigations/{window_id}", json={}).json()

    def run_scenario(self) -> ScenarioReport:
        report = ScenarioReport(baseline_version="", baseline_metrics={})
        baseline = self.train_baseline()
        report.baseline_version = baseline["version"]
        report.baseline_metrics = baseline["metrics"]

        stages = [
            ("clean", {}, False),
            ("subtle", SUBTLE_KNOBS, False),
            ("severe", SEVERE_KNOBS, True),
        ]
        for index, (name, knobs, _expected_alert) in enumerate(stages, start=1):
            window, evaluation = self.submit_and_evaluate(
                name, index, knobs, seed=1000 + index
            )
            decision: dict = {}
            if evaluation["alert"] or name == "severe":
                if name != "clean":
                    decision = self.decide(window["id"]) or {}
            stage = StageResult(
                stage=name,
                window_id=window["id"],
                alert=bool(evaluation["alert"]),
                drift_count=int(evaluation["drift_count"]),
                max_psi=float(evaluation["max_psi"]),
                f1=float(evaluation["f1"]),
                decision=decision.get("decision"),
                reasons=decision.get("reasons", []),
                gate_inputs=decision.get("gate_inputs", {}).get("model_extra", {})
                or {
                    k: v
                    for k, v in (decision.get("gate_inputs") or {}).items()
                },
            )
            report.stages.append(stage)

        severe_stage = report.stages[-1]
        if severe_stage.decision == "retrain":
            trained = self.client.post(
                "/api/v1/candidates/train",
                json={"source_window_id": severe_stage.window_id, "seed": 7},
            ).json()
            report.candidate_version = trained["version"]
            evaluated = self.client.post(
                "/api/v1/candidates/evaluate", json={"version": trained["version"]}
            ).json()
            report.candidate_verdict = evaluated["verdict"]
        else:
            trained = {"version": None}
            evaluated = {}

        if report.candidate_verdict == "pass":
            self.client.post("/api/v1/shadow/run", json={"version": report.candidate_version})
            self.client.post("/api/v1/shadow/canary", json={"version": report.candidate_version})
            promotion = self.client.post(
                "/api/v1/promotions",
                json={"candidate_version": report.candidate_version},
            ).json()
            approved = self.client.post(
                f"/api/v1/promotions/{promotion['promotion_id']}/approve",
                json={"approver": "demo-operator", "comment": "demo approval"},
            ).json()
            report.promotion_state = approved["state"]

        registry = self.client.get("/api/v1/registry").json()
        champions = [m for m in registry["models"] if m["status"] == "champion"]
        report.champion_after = champions[0]["version"] if champions else None

        bad = self.client.post(
            "/api/v1/candidates/train",
            json={"inject_bad": True, "bad_n_samples": 140, "bad_label_noise": 0.35},
        ).json()
        report.bad_candidate_version = bad["version"]
        bad_eval = self.client.post(
            "/api/v1/candidates/evaluate", json={"version": bad["version"]}
        ).json()
        report.bad_candidate_verdict = bad_eval["verdict"]
        return report


def run_scenario(client: ClientLike) -> ScenarioReport:
    """Convenience wrapper."""
    return DriftSimulator(client).run_scenario()
