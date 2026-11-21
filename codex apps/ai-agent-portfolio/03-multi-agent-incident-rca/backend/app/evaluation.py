from __future__ import annotations

import argparse
import asyncio
import json
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .fixtures import SCENARIOS
from .models import EvaluationSummary, Incident
from .repository import Repository
from .workflow import InvestigationEngine, validate_citations


def dataset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evaluation" / "cases.jsonl"


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    source = path or dataset_path()
    cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    if len(cases) < 60:
        raise ValueError(f"evaluation dataset must contain at least 60 cases; found {len(cases)}")
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("evaluation case IDs must be unique")
    return cases


async def evaluate_cases(cases: list[dict[str, Any]]) -> tuple[EvaluationSummary, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    category_totals: dict[str, list[bool]] = defaultdict(list)
    durations: list[float] = []
    for case in cases:
        repository = Repository("sqlite:///:memory:")
        engine = InvestigationEngine(repository)
        config = SCENARIOS[case["scenario"]]
        incident = Incident(
            id=f"EVAL-{case['id']}",
            title=config["title"],
            service=config["service"],
            scenario=case["scenario"],
            severity=case.get("severity", "SEV-2"),
            alert_summary=config["impact"],
        )
        repository.save_incident(incident)
        investigation = await engine.investigate(incident, variant=int(case["variant"]))
        leader = investigation.hypotheses[0]
        category_ok = leader.category == case["ground_truth_category"]
        exact_ok = category_ok and leader.component == case["ground_truth_component"]
        valid_ids = {item.id for item in investigation.evidence}
        claims = [claim for section in investigation.rca.sections for claim in section.claims]
        cited_claims = sum(bool(claim.evidence_ids) for claim in claims)
        unsupported = sum(bool(set(claim.evidence_ids) - valid_ids) for claim in claims)
        try:
            validate_citations(investigation.rca, investigation.evidence)
            gate_passed = True
        except ValueError:
            gate_passed = False
        category_totals[case["ground_truth_category"]].append(category_ok)
        durations.append(investigation.duration_ms)
        rows.append(
            {
                "case_id": case["id"],
                "scenario": case["scenario"],
                "expected_category": case["ground_truth_category"],
                "predicted_category": leader.category,
                "expected_component": case["ground_truth_component"],
                "predicted_component": leader.component,
                "category_correct": category_ok,
                "exact_correct": exact_ok,
                "citation_coverage": cited_claims / len(claims) if claims else 0.0,
                "unsupported_claims": unsupported,
                "claim_count": len(claims),
                "citation_gate_passed": gate_passed,
                "critic_overturned": investigation.critic.overturned,
                "duration_ms": investigation.duration_ms,
                "worker_latency_ms": {
                    run.worker: run.latency_ms for run in investigation.worker_runs
                },
                "token_usage": investigation.token_usage,
                "estimated_cost_usd": investigation.estimated_cost_usd,
            }
        )

    total = len(rows)
    summary = EvaluationSummary(
        total_cases=total,
        exact_root_cause_accuracy=sum(row["exact_correct"] for row in rows) / total,
        category_accuracy=sum(row["category_correct"] for row in rows) / total,
        evidence_citation_coverage=sum(row["citation_coverage"] for row in rows) / total,
        unsupported_claim_rate=sum(row["unsupported_claims"] for row in rows)
        / sum(row["claim_count"] for row in rows),
        critic_overturn_rate=sum(row["critic_overturned"] for row in rows) / total,
        average_duration_ms=statistics.fmean(durations),
        accuracy_by_category={
            category: sum(values) / len(values) for category, values in category_totals.items()
        },
        passed=(
            all(row["exact_correct"] for row in rows)
            and all(row["citation_gate_passed"] for row in rows)
            and all(row["unsupported_claims"] == 0 for row in rows)
            and all(row["citation_coverage"] == 1 for row in rows)
        ),
    )
    return summary, rows


def write_reports(
    summary: EvaluationSummary,
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    json_path = output_dir / "evaluation-report.json"
    markdown_path = output_dir / "evaluation-report.md"
    json_path.write_text(
        json.dumps(
            {"generated_at": generated_at, "summary": summary.model_dump(), "cases": rows},
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    categories = "\n".join(
        f"| {category} | {accuracy:.1%} |"
        for category, accuracy in sorted(summary.accuracy_by_category.items())
    )
    markdown_path.write_text(
        "\n".join(
            [
                "# Multi-Agent Incident RCA Evaluation",
                "",
                f"Generated: {generated_at}",
                f"Status: **{'PASS' if summary.passed else 'FAIL'}**",
                "",
                "| Metric | Result |",
                "|---|---:|",
                f"| Cases | {summary.total_cases} |",
                f"| Exact root-cause accuracy | {summary.exact_root_cause_accuracy:.1%} |",
                f"| Category accuracy | {summary.category_accuracy:.1%} |",
                f"| Citation coverage | {summary.evidence_citation_coverage:.1%} |",
                f"| Unsupported-claim rate | {summary.unsupported_claim_rate:.1%} |",
                f"| Critic overturn rate | {summary.critic_overturn_rate:.1%} |",
                f"| Average duration | {summary.average_duration_ms:.2f} ms |",
                "",
                "## Accuracy by category",
                "",
                "| Category | Accuracy |",
                "|---|---:|",
                categories,
            ]
        ),
        encoding="utf-8",
    )
    return json_path, markdown_path


async def run(output_dir: Path | None = None) -> EvaluationSummary:
    summary, rows = await evaluate_cases(load_cases())
    write_reports(summary, rows, output_dir or Path("evaluation/reports"))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic incident replay evaluation")
    parser.add_argument("--output", type=Path, default=Path("evaluation/reports"))
    args = parser.parse_args()
    summary = asyncio.run(run(args.output))
    print(summary.model_dump_json(indent=2))
    return 0 if summary.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
