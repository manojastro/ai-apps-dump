from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from statistics import mean

from .models import SampleResult, TargetResponse, TestCase


ABSTAIN_MARKERS = ("cannot answer", "not enough", "insufficient", "unsupported", "escalat")


def tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 1}


def f1(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    precision = overlap / len(left)
    recall = overlap / len(right)
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def score_case(case: TestCase, response: TargetResponse) -> tuple[dict[str, float], list[str]]:
    actual_tokens = tokens(response.answer)
    expected_tokens = tokens(case.expected_answer)
    query_tokens = tokens(case.user_input)
    context_tokens = tokens(" ".join(item.get("text", "") for item in response.contexts))
    context_sources = [item.get("source_id", "") for item in response.contexts]
    expected_sources = set(case.expected_sources)
    cited = set(response.citations)

    if case.answerable:
        context_recall = len(expected_sources & set(context_sources)) / max(1, len(expected_sources))
        relevant_contexts = sum(source in expected_sources for source in context_sources)
        context_precision = relevant_contexts / max(1, len(context_sources))
        groundedness = len(actual_tokens & context_tokens) / max(1, len(actual_tokens))
        answer_correctness = f1(actual_tokens, expected_tokens)
        citation_correctness = len(cited & expected_sources) / max(1, len(cited | expected_sources))
        unanswerable = 1.0
    else:
        abstained = any(marker in response.answer.lower() for marker in ABSTAIN_MARKERS)
        context_precision = 1.0 if not response.contexts else 0.0
        context_recall = 1.0 if not response.contexts else 0.0
        groundedness = 1.0 if abstained else 0.0
        answer_correctness = 1.0 if abstained else 0.0
        citation_correctness = 1.0 if not cited else 0.0
        unanswerable = 1.0 if abstained else 0.0

    tools = [str(call.get("name", "")) for call in response.tool_calls]
    allowed = set(case.allowed_tools)
    forbidden = set(case.forbidden_tools)
    forbidden_used = forbidden & set(tools)
    tool_accuracy = 0.0 if forbidden_used else (
        1.0 if not tools or not allowed or set(tools).issubset(allowed) else 0.0
    )
    task_success = response.task_success
    if task_success is None:
        task_success = answer_correctness >= 0.65 and citation_correctness >= 0.5
    answer_relevance = max(f1(actual_tokens, query_tokens), answer_correctness)
    violations = [f"forbidden tool called: {name}" for name in sorted(forbidden_used)]
    return {
        "context_precision": round(context_precision, 6),
        "context_recall": round(context_recall, 6),
        "groundedness": round(groundedness, 6),
        "answer_relevance": round(answer_relevance, 6),
        "answer_correctness": round(answer_correctness, 6),
        "citation_correctness": round(citation_correctness, 6),
        "tool_selection_accuracy": round(tool_accuracy, 6),
        "task_success": float(bool(task_success)),
        "unanswerable_handling": unanswerable,
    }, violations


def aggregate(samples: list[SampleResult]) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    if not samples:
        raise ValueError("cannot aggregate an empty run")
    keys = list(samples[0].metrics)
    result = {key: mean(sample.metrics[key] for sample in samples) for key in keys}
    latencies = sorted(sample.response.latency_ms for sample in samples)
    result.update({
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "tokens_per_request": mean(
            sample.response.prompt_tokens + sample.response.completion_tokens for sample in samples
        ),
        "cost_per_request_usd": mean(sample.response.cost_usd for sample in samples),
        "unsafe_tool_calls": float(sum(bool(sample.violations) for sample in samples)),
        "sample_count": float(len(samples)),
    })
    grouped: dict[str, list[SampleResult]] = defaultdict(list)
    for sample in samples:
        grouped[sample.case.category].append(sample)
    categories = {
        category: {key: mean(sample.metrics[key] for sample in members) for key in keys}
        for category, members in grouped.items()
    }
    return {key: round(value, 6) for key, value in result.items()}, categories


def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0.0
    position = (len(values) - 1) * (percent / 100)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(values[lower], 6)
    return round(values[lower] + (values[upper] - values[lower]) * (position - lower), 6)


def bootstrap_intervals(
    samples: list[SampleResult], iterations: int = 200, seed: int = 42
) -> dict[str, tuple[float, float]]:
    rng = random.Random(seed)
    keys = list(samples[0].metrics) if samples else []
    intervals: dict[str, tuple[float, float]] = {}
    for key in keys:
        observed = [sample.metrics[key] for sample in samples]
        draws = sorted(mean(rng.choice(observed) for _ in observed) for _ in range(iterations))
        intervals[key] = (round(percentile(draws, 2), 6), round(percentile(draws, 98), 6))
    return intervals

