from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TestCase:
    id: str
    user_input: str
    expected_answer: str = ""
    expected_properties: list[str] = field(default_factory=list)
    expected_sources: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    difficulty: str = "common"
    category: str = "general"
    answerable: bool = True
    allowed_tools: list[str] = field(default_factory=list)
    forbidden_tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TestCase":
        return cls(**{name: value.get(name, default) for name, default in {
            "id": "", "user_input": "", "expected_answer": "",
            "expected_properties": [], "expected_sources": [], "tags": [],
            "difficulty": "common", "category": "general", "answerable": True,
            "allowed_tools": [], "forbidden_tools": [], "metadata": {},
        }.items()})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TargetResponse:
    answer: str
    contexts: list[dict[str, str]] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    task_success: bool | None = None
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TargetResponse":
        fields = cls.__dataclass_fields__
        return cls(**{key: value[key] for key in fields if key in value})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SampleResult:
    case: TestCase
    response: TargetResponse
    metrics: dict[str, float]
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(), "response": self.response.to_dict(),
            "metrics": self.metrics, "violations": self.violations,
        }


@dataclass(slots=True)
class RunReport:
    id: str
    project_id: str
    dataset_id: str
    target: str
    judge_config: dict[str, Any]
    aggregate: dict[str, float]
    category_metrics: dict[str, dict[str, float]]
    confidence_intervals: dict[str, tuple[float, float]]
    samples: list[SampleResult]
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RunReport":
        samples = [
            SampleResult(
                TestCase.from_dict(item["case"]),
                TargetResponse.from_dict(item["response"]),
                item["metrics"], item.get("violations", []),
            )
            for item in value.get("samples", [])
        ]
        return cls(
            id=value["id"], project_id=value["project_id"], dataset_id=value["dataset_id"],
            target=value["target"], judge_config=value["judge_config"],
            aggregate=value["aggregate"], category_metrics=value.get("category_metrics", {}),
            confidence_intervals=value.get("confidence_intervals", {}), samples=samples,
            created_at=value["created_at"], metadata=value.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "project_id": self.project_id,
            "dataset_id": self.dataset_id, "target": self.target,
            "judge_config": self.judge_config, "aggregate": self.aggregate,
            "category_metrics": self.category_metrics,
            "confidence_intervals": self.confidence_intervals,
            "samples": [sample.to_dict() for sample in self.samples],
            "created_at": self.created_at, "metadata": self.metadata,
        }


@dataclass(slots=True)
class GateConfig:
    absolute_thresholds: dict[str, float] = field(default_factory=dict)
    max_relative_regression: float = 0.03
    max_p95_latency_ms: float = 2000
    max_cost_per_request_usd: float = 0.01
    forbid_unsafe_tools: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "GateConfig":
        return cls(
            absolute_thresholds=value.get("absolute_thresholds", {}),
            max_relative_regression=float(value.get("max_relative_regression", 0.03)),
            max_p95_latency_ms=float(value.get("max_p95_latency_ms", 2000)),
            max_cost_per_request_usd=float(value.get("max_cost_per_request_usd", 0.01)),
            forbid_unsafe_tools=bool(value.get("forbid_unsafe_tools", True)),
        )
