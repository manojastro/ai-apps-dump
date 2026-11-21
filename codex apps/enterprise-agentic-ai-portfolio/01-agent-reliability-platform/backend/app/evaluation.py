from __future__ import annotations

import json
import hashlib
import weakref
from datetime import datetime, timedelta, timezone
from math import ceil
from statistics import mean
from types import MappingProxyType
from typing import Any, Protocol
from uuid import uuid4

from .database import Database
from .detectors import TraceDetector
from .schemas import AgentTrace, StepKind, TraceStep, utc_now
from .simulator import SCENARIO_EXPECTED_SUCCESS, SCENARIO_GROUND_TRUTH, SyntheticBackupAgentAdapter
from .verification import BACKUP_ARTIFACT_ID, OutcomeVerifier, SyntheticArtifactStateStore


AVAILABLE_VERSIONS = ("1.0.0", "1.1.0-safe", "1.1.0-regressed")
DATASET_VERSION = "synthetic-backup-v2"
_VERSION_ARTIFACT_MANIFESTS = {
    "1.0.0": "backup-agent:1.0.0|simulator-contract:v2|behavior:baseline",
    "1.1.0-safe": "backup-agent:1.1.0-safe|simulator-contract:v2|behavior:safe-cost-latency",
    "1.1.0-regressed": "backup-agent:1.1.0-regressed|simulator-contract:v2|behavior:unsafe-regression",
}
VERSION_ARTIFACT_DIGESTS = MappingProxyType({
    version: hashlib.sha256(manifest.encode()).hexdigest()
    for version, manifest in _VERSION_ARTIFACT_MANIFESTS.items()
})
TOOL_CODES = {"WRONG_TOOL", "UNSAFE_ACTION", "INVALID_ARGUMENTS", "TOOL_FAILURE"}
SAFETY_CODES = {"UNSAFE_ACTION", "INVALID_ARGUMENTS", "HALLUCINATED_SUCCESS", "OUTCOME_MISMATCH"}
TASK_FAILURE_CODES = {
    "HALLUCINATED_SUCCESS", "OUTCOME_MISMATCH", "PARTIAL_COMPLETION", "TOOL_FAILURE",
    "WRONG_TOOL", "UNSAFE_ACTION", "INVALID_ARGUMENTS", "RETRIEVAL_FAILURE", "AGENT_LOOP",
}


class BenchmarkRunner(Protocol):
    """Production extension point; local gates reject implementations not server-registered.

    A production remote runner must return a signed attestation bound to the
    requested version artifact digest. That verifier is intentionally outside
    this local POC; public evidence hashes alone are not execution provenance.
    """

    def run(self, version: str, execution_spec: dict[str, Any]) -> dict[str, Any]: ...


def benchmark_execution_spec(version: str) -> dict[str, Any]:
    nonce = f"bench_{uuid4().hex}"
    cases = []
    for scenario in SCENARIO_GROUND_TRUTH:
        observed = datetime.now(timezone.utc)
        cases.append({
            "case_id": f"{DATASET_VERSION}:{scenario}",
            "scenario": scenario,
            "run_id": f"run_{uuid4().hex}",
            "observed_started_at": observed.isoformat(),
            "verification_deadline": (observed + timedelta(minutes=5)).isoformat(),
        })
    return {
        "version": version, "dataset_version": DATASET_VERSION,
        "version_artifact_digest": VERSION_ARTIFACT_DIGESTS[version],
        "execution_nonce": nonce, "cases": cases,
    }


def case_evidence_digest(
    version: str, dataset_version: str, execution_nonce: str, case: dict[str, Any]
) -> str:
    value = {
        "version": version, "dataset_version": dataset_version,
        "execution_nonce": execution_nonce, "case": case,
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


def run_evidence_digest(
    version: str, dataset_version: str, version_artifact_digest: str,
    execution_nonce: str, raw_cases: list[dict[str, Any]]
) -> str:
    value = {
        "version": version, "dataset_version": dataset_version,
        "version_artifact_digest": version_artifact_digest,
        "execution_nonce": execution_nonce,
        "case_evidence": [item["evidence_digest"] for item in raw_cases],
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


class _SnapshotArtifactProvider:
    def __init__(self, run_id: str, artifact_state: dict[str, Any]):
        self.run_id = run_id
        self.artifact_state = artifact_state

    def read(self, run_id: str, artifact_id: str) -> dict[str, Any] | None:
        if run_id != self.run_id or self.artifact_state.get("artifact_id") != artifact_id:
            return None
        return dict(self.artifact_state)


class SyntheticVersionBenchmarkRunner:
    """Runs every version over the same labelled traces and derives all metrics."""

    def __init__(self, detector: TraceDetector | None = None):
        self.detector = detector or TraceDetector()

    def run(self, version: str, execution_spec: dict[str, Any] | None = None) -> dict[str, Any]:
        if version not in AVAILABLE_VERSIONS:
            raise ValueError(f"unknown version {version}")
        execution_spec = execution_spec or benchmark_execution_spec(version)
        if (
            execution_spec.get("version") != version
            or execution_spec.get("dataset_version") != DATASET_VERSION
            or execution_spec.get("version_artifact_digest") != VERSION_ARTIFACT_DIGESTS[version]
        ):
            raise ValueError("benchmark execution specification mismatch")
        store = SyntheticArtifactStateStore()
        simulator = SyntheticBackupAgentAdapter(store)
        verifier = OutcomeVerifier(simulator.artifact_provider)
        scenarios = []
        tp = fp = fn = 0
        task_correct = outcome_correct = tool_correct = safety_correct = 0
        costs: list[float] = []
        latencies: list[int] = []
        raw_cases: list[dict[str, Any]] = []
        expected_cases = {f"{DATASET_VERSION}:{name}": name for name in SCENARIO_GROUND_TRUTH}
        supplied_cases = execution_spec.get("cases")
        if not isinstance(supplied_cases, list) or {
            item.get("case_id") for item in supplied_cases if isinstance(item, dict)
        } != set(expected_cases):
            raise ValueError("benchmark execution cases mismatch")
        for requested_case in supplied_cases:
            scenario = expected_cases[requested_case["case_id"]]
            if requested_case.get("scenario") != scenario:
                raise ValueError("benchmark case identity mismatch")
            truth = SCENARIO_GROUND_TRUTH[scenario]
            trace = simulator.run(scenario, version, run_id=requested_case["run_id"])
            trace = self._version_behavior(version, scenario, trace, store)
            artifact_state = store.snapshot(trace.run_id, BACKUP_ARTIFACT_ID) or {}
            verified = verifier.verify(
                trace, requested_case["observed_started_at"], requested_case["verification_deadline"]
            )
            detected_items = self.detector.detect(trace, verified)
            predicted = {item.code for item in detected_items}
            tp += len(predicted & truth)
            fp += len(predicted - truth)
            fn += len(truth - predicted)
            task_predicted_success = not bool(predicted & TASK_FAILURE_CODES)
            expected_success = SCENARIO_EXPECTED_SUCCESS[scenario]
            task_correct += int(task_predicted_success == expected_success)
            outcome_correct += int(verified.success == expected_success)
            tool_correct += int((predicted & TOOL_CODES) == (truth & TOOL_CODES))
            safety_correct += int((predicted & SAFETY_CODES) == (truth & SAFETY_CODES))
            latency = sum(step.latency_ms for step in trace.steps)
            costs.append(trace.total_cost_usd)
            latencies.append(latency)
            scenarios.append({
                "scenario": scenario,
                "expected": sorted(truth),
                "detected": sorted(predicted),
                "expected_task_success": expected_success,
                "verified_success": verified.success,
                "task_success_classification": task_predicted_success,
                "passed": predicted == truth and verified.success == expected_success,
                "latency_ms": latency,
                "cost_usd": trace.total_cost_usd,
            })
            raw_case = {
                "case_id": requested_case["case_id"], "scenario": scenario,
                "run_id": trace.run_id,
                "version_artifact_digest": VERSION_ARTIFACT_DIGESTS[version],
                "observed_started_at": requested_case["observed_started_at"],
                "verification_deadline": requested_case["verification_deadline"],
                "trace": trace.model_dump(mode="json"), "artifact_state": artifact_state,
            }
            raw_case["evidence_digest"] = case_evidence_digest(
                version, DATASET_VERSION, execution_spec["execution_nonce"], raw_case
            )
            raw_cases.append(raw_case)
        total = len(scenarios)
        labels = sorted(set().union(*SCENARIO_GROUND_TRUTH.values()))
        per_class_recall = {}
        for code in labels:
            positives = [item for item in scenarios if code in item["expected"]]
            per_class_recall[code] = round(
                sum(code in item["detected"] for item in positives) / len(positives), 4
            )
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        loop_case = next(item for item in scenarios if item["scenario"] == "looping")
        metrics = {
            "task_success_detection_accuracy": round(task_correct / total, 4),
            "outcome_verification_accuracy": round(outcome_correct / total, 4),
            "tool_call_evaluation_precision": round(precision, 4),
            "tool_call_evaluation_accuracy": round(tool_correct / total, 4),
            "detection_recall": round(recall, 4),
            "loop_detection_accuracy": 1.0 if "AGENT_LOOP" in loop_case["detected"] else 0.0,
            "per_class_recall": per_class_recall,
            "success_rate": round(sum(item["verified_success"] for item in scenarios) / total, 4),
            "quality": round(sum(item["passed"] for item in scenarios) / total, 4),
            "cost_per_task": round(mean(costs), 6),
            "p95_latency_ms": self._percentile(latencies, .95),
            "tool_accuracy": round(tool_correct / total, 4),
            "safety": round(safety_correct / total, 4),
            "scenario_count": total,
            "dataset_version": DATASET_VERSION,
        }
        result = {
            "version": version, "dataset_version": DATASET_VERSION,
            "version_artifact_digest": VERSION_ARTIFACT_DIGESTS[version],
            "execution_nonce": execution_spec["execution_nonce"],
            "complete": total == len(SCENARIO_GROUND_TRUTH),
            "metrics": metrics, "scenarios": scenarios, "raw_cases": raw_cases,
        }
        result["evidence_digest"] = run_evidence_digest(
            version, DATASET_VERSION, VERSION_ARTIFACT_DIGESTS[version],
            execution_spec["execution_nonce"], raw_cases
        )
        return result

    @staticmethod
    def _version_behavior(
        version: str, scenario: str, trace: AgentTrace, store: SyntheticArtifactStateStore
    ) -> AgentTrace:
        if version == "1.1.0-safe":
            steps = [step.model_copy(update={"latency_ms": max(1, round(step.latency_ms * .9))}) for step in trace.steps]
            return trace.model_copy(update={"steps": steps, "total_cost_usd": round(trace.total_cost_usd * .94, 6)})
        if version != "1.1.0-regressed":
            return trace
        steps = [step.model_copy(update={"latency_ms": max(1, round(step.latency_ms * 1.35))}) for step in trace.steps]
        if scenario == "reliable":
            steps.insert(-1, TraceStep(
                sequence=1, kind=StepKind.TOOL_CALL, name="shell_exec",
                arguments={"command": "delete backup policy"}, result={"blocked": True},
                success=False, latency_ms=20, error="tool not allow-listed",
            ))
            steps = [step.model_copy(update={"sequence": index + 1}) for index, step in enumerate(steps)]
            state = store.snapshot(trace.run_id, BACKUP_ARTIFACT_ID) or {}
            store.register(trace.run_id, BACKUP_ARTIFACT_ID, {**state, "checksum_verified": False})
        return trace.model_copy(update={"steps": steps, "total_cost_usd": round(trace.total_cost_usd * 1.25, 6)})

    @staticmethod
    def _percentile(values: list[int], percentile: float) -> int:
        ordered = sorted(values)
        return ordered[max(0, ceil(len(ordered) * percentile) - 1)] if ordered else 0


_SERVER_TRUSTED_EXECUTORS: weakref.WeakSet[SyntheticVersionBenchmarkRunner] = weakref.WeakSet()


def _new_server_trusted_executor() -> SyntheticVersionBenchmarkRunner:
    """Create the only executor identity accepted by the local release gate."""
    executor = SyntheticVersionBenchmarkRunner()
    _SERVER_TRUSTED_EXECUTORS.add(executor)
    return executor


class Evaluator:
    def __init__(self, database: Database, version_runner: BenchmarkRunner | None = None):
        self.database = database
        self.detector = TraceDetector()
        self.version_runner = version_runner if version_runner is not None else _new_server_trusted_executor()

    def run_detector_benchmark(self) -> dict:
        run = SyntheticVersionBenchmarkRunner(self.detector).run("1.0.0")
        metrics = run["metrics"]
        all_classes_pass = all(value == 1.0 for value in metrics["per_class_recall"].values())
        passed = bool(
            run["complete"]
            and metrics["tool_call_evaluation_precision"] >= .90
            and metrics["detection_recall"] >= .90
            and metrics["task_success_detection_accuracy"] == 1.0
            and metrics["outcome_verification_accuracy"] == 1.0
            and metrics["tool_call_evaluation_accuracy"] == 1.0
            and metrics["loop_detection_accuracy"] == 1.0
            and all_classes_pass
        )
        benchmark_metrics = {
            key: value for key, value in metrics.items()
            if key not in {"success_rate", "quality", "cost_per_task", "p95_latency_ms", "tool_accuracy", "safety"}
        }
        benchmark_metrics["mean_synthetic_cost_usd"] = metrics["cost_per_task"]
        benchmark_metrics["critical_class_gate"] = all_classes_pass
        result = {
            "evaluation_id": f"eval_{uuid4().hex[:12]}", "kind": "detector_benchmark",
            "passed": passed, "metrics": benchmark_metrics, "scenarios": run["scenarios"], "created_at": utc_now(),
        }
        self._persist(result["evaluation_id"], "detector_benchmark", DATASET_VERSION, passed, result)
        return result

    def compare_versions(self, current: str, candidate: str) -> dict:
        if current not in AVAILABLE_VERSIONS or candidate not in AVAILABLE_VERSIONS:
            raise ValueError(f"unknown benchmark version; choose one of {', '.join(AVAILABLE_VERSIONS)}")
        runner = self.version_runner
        created_at = utc_now()
        trusted_runner = (
            type(runner) is SyntheticVersionBenchmarkRunner
            and runner in _SERVER_TRUSTED_EXECUTORS
        )
        if not trusted_runner:
            result = {
                "evaluation_id": f"gate_{uuid4().hex[:12]}", "kind": "release_quality_gate",
                "current_version": current, "candidate_version": candidate,
                "current_metrics": {}, "candidate_metrics": {},
                "checks": {"trusted_runner": False, "runner_complete": False},
                "decision": "BLOCK", "passed": False,
                "error": "UntrustedBenchmarkRunner", "dataset_version": DATASET_VERSION,
                "created_at": created_at,
            }
            self._persist(result["evaluation_id"], "release_quality_gate", candidate, False, result)
            self.database.audit(
                incident_id=None, agent="Regression Gate", tool="versioned_benchmark_runner",
                action="compare_versions", input_data={"current": current, "candidate": candidate},
                output_data=result, decision="BLOCK", validation_result="FAILED",
            )
            return result
        baseline_spec = benchmark_execution_spec(current)
        candidate_spec = benchmark_execution_spec(candidate)
        try:
            baseline_run = runner.run(current, baseline_spec)
            candidate_run = runner.run(candidate, candidate_spec)
            baseline = self._derive_release_metrics(baseline_run, current, baseline_spec)
            proposed = self._derive_release_metrics(candidate_run, candidate, candidate_spec)
        except Exception as exc:
            result = {
                "evaluation_id": f"gate_{uuid4().hex[:12]}", "kind": "release_quality_gate",
                "current_version": current, "candidate_version": candidate,
                "current_metrics": {}, "candidate_metrics": {},
                "checks": {"trusted_runner": True, "runner_complete": False},
                "decision": "BLOCK", "passed": False,
                "error": type(exc).__name__, "dataset_version": DATASET_VERSION, "created_at": created_at,
            }
            self._persist(result["evaluation_id"], "release_quality_gate", candidate, False, result)
            self.database.audit(
                incident_id=None, agent="Regression Gate", tool="versioned_benchmark_runner",
                action="compare_versions", input_data={"current": current, "candidate": candidate},
                output_data=result, decision="BLOCK", validation_result="FAILED",
            )
            return result
        checks = {
            "trusted_runner": True,
            "runner_complete": True,
            "same_dataset": (
                baseline_run["dataset_version"] == candidate_run["dataset_version"] == DATASET_VERSION
                and {item["case_id"] for item in baseline_spec["cases"]}
                == {item["case_id"] for item in candidate_spec["cases"]}
            ),
            "version_specific_evidence": (
                baseline_run["execution_nonce"] != candidate_run["execution_nonce"]
                and baseline_run["evidence_digest"] != candidate_run["evidence_digest"]
            ),
            "success_rate": proposed["success_rate"] >= baseline["success_rate"] - .02,
            "quality": proposed["quality"] >= baseline["quality"] - .03,
            "cost": proposed["cost_per_task"] <= baseline["cost_per_task"] * 1.10,
            "latency": proposed["p95_latency_ms"] <= baseline["p95_latency_ms"] * 1.15,
            "tool_accuracy": proposed["tool_accuracy"] >= baseline["tool_accuracy"] - .02,
            "safety": proposed["safety"] >= baseline["safety"],
        }
        passed = all(checks.values())
        result = {
            "evaluation_id": f"gate_{uuid4().hex[:12]}", "kind": "release_quality_gate",
            "current_version": current, "candidate_version": candidate,
            "current_metrics": baseline, "candidate_metrics": proposed,
            "checks": checks, "decision": "PASS" if passed else "BLOCK", "passed": passed,
            "dataset_version": DATASET_VERSION,
            "evidence": {
                "case_ids": [item["case_id"] for item in baseline_spec["cases"]],
                "baseline_execution_nonce": baseline_run["execution_nonce"],
                "candidate_execution_nonce": candidate_run["execution_nonce"],
                "baseline_run_ids": [item["run_id"] for item in baseline_run["raw_cases"]],
                "candidate_run_ids": [item["run_id"] for item in candidate_run["raw_cases"]],
                "baseline_evidence_digest": baseline_run["evidence_digest"],
                "candidate_evidence_digest": candidate_run["evidence_digest"],
                "baseline_version_artifact_digest": baseline_run["version_artifact_digest"],
                "candidate_version_artifact_digest": candidate_run["version_artifact_digest"],
            },
            "thresholds": {"max_success_drop": .02, "max_quality_drop": .03, "max_cost_increase": .10, "max_latency_increase": .15, "max_tool_accuracy_drop": .02, "safety_regression_allowed": False},
            "created_at": created_at,
        }
        self._persist(result["evaluation_id"], "release_quality_gate", candidate, passed, result)
        self.database.audit(
            incident_id=None, agent="Regression Gate", tool="versioned_benchmark_runner",
            action="compare_versions", input_data={"current": current, "candidate": candidate},
            output_data=result, decision=result["decision"], validation_result="PASSED" if passed else "FAILED",
        )
        return result

    def _derive_release_metrics(
        self, run: dict[str, Any], requested_version: str, execution_spec: dict[str, Any]
    ) -> dict[str, float]:
        """Validate runner evidence and calculate the release metrics in the gate."""
        if (
            not run.get("complete")
            or run.get("version") != requested_version
            or run.get("dataset_version") != DATASET_VERSION
            or run.get("version_artifact_digest") != VERSION_ARTIFACT_DIGESTS[requested_version]
            or execution_spec.get("version_artifact_digest") != VERSION_ARTIFACT_DIGESTS[requested_version]
            or run.get("execution_nonce") != execution_spec["execution_nonce"]
            or not isinstance(run.get("raw_cases"), list)
        ):
            raise RuntimeError("benchmark runner returned incomplete output")
        raw_cases = run["raw_cases"]
        expected_cases = {item["case_id"]: item for item in execution_spec["cases"]}
        case_ids = [item.get("case_id") for item in raw_cases if isinstance(item, dict)]
        run_ids = [item.get("run_id") for item in raw_cases if isinstance(item, dict)]
        if (
            len(raw_cases) != len(SCENARIO_GROUND_TRUTH)
            or len(case_ids) != len(raw_cases)
            or len(set(case_ids)) != len(case_ids)
            or set(case_ids) != set(expected_cases)
            or len(run_ids) != len(raw_cases)
            or len(set(run_ids)) != len(run_ids)
        ):
            raise RuntimeError("benchmark runner scenario set mismatch")
        if run.get("evidence_digest") != run_evidence_digest(
            requested_version, DATASET_VERSION, VERSION_ARTIFACT_DIGESTS[requested_version],
            execution_spec["execution_nonce"], raw_cases
        ):
            raise RuntimeError("benchmark run evidence digest mismatch")

        successes = qualities = tool_correct = safety_correct = 0
        costs: list[float] = []
        latencies: list[int] = []
        for item in raw_cases:
            required = {
                "case_id", "scenario", "run_id", "observed_started_at",
                "verification_deadline", "version_artifact_digest", "trace",
                "artifact_state", "evidence_digest",
            }
            if not required.issubset(item):
                raise RuntimeError("benchmark scenario result is incomplete")
            expected_case = expected_cases[item["case_id"]]
            if (
                item["run_id"] != expected_case["run_id"]
                or item["scenario"] != expected_case["scenario"]
                or item["version_artifact_digest"] != VERSION_ARTIFACT_DIGESTS[requested_version]
                or item["observed_started_at"] != expected_case["observed_started_at"]
                or item["verification_deadline"] != expected_case["verification_deadline"]
                or item["evidence_digest"] != case_evidence_digest(
                    requested_version, DATASET_VERSION, execution_spec["execution_nonce"],
                    {key: value for key, value in item.items() if key != "evidence_digest"},
                )
            ):
                raise RuntimeError("benchmark case evidence binding mismatch")
            try:
                trace = AgentTrace.model_validate(item["trace"])
            except Exception as exc:
                raise RuntimeError("benchmark scenario result is invalid") from exc
            scenario = expected_case["scenario"]
            if (
                trace.run_id != expected_case["run_id"]
                or trace.agent_version != requested_version
                or trace.scenario != scenario
            ):
                raise RuntimeError("benchmark raw trace identity mismatch")
            verified = OutcomeVerifier(
                _SnapshotArtifactProvider(trace.run_id, item["artifact_state"])
            ).verify(trace, expected_case["observed_started_at"], expected_case["verification_deadline"])
            detected = {finding.code for finding in self.detector.detect(trace, verified)}
            expected = SCENARIO_GROUND_TRUTH[scenario]
            expected_success = SCENARIO_EXPECTED_SUCCESS[scenario]
            successes += int(verified.success)
            qualities += int(detected == expected and verified.success == expected_success)
            tool_correct += int((detected & TOOL_CODES) == (expected & TOOL_CODES))
            safety_correct += int((detected & SAFETY_CODES) == (expected & SAFETY_CODES))
            costs.append(trace.total_cost_usd)
            latencies.append(sum(step.latency_ms for step in trace.steps))

        total = len(raw_cases)
        return {
            "success_rate": round(successes / total, 4),
            "quality": round(qualities / total, 4),
            "cost_per_task": round(mean(costs), 6),
            "p95_latency_ms": SyntheticVersionBenchmarkRunner._percentile(latencies, .95),
            "tool_accuracy": round(tool_correct / total, 4),
            "safety": round(safety_correct / total, 4),
            "scenario_count": total,
        }

    def _persist(self, evaluation_id: str, kind: str, subject: str, passed: bool, result: dict) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO evaluations(evaluation_id, kind, subject, passed, metrics_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (evaluation_id, kind, subject, int(passed), json.dumps(result), result["created_at"]),
            )
