"""Runner: execute the golden set against a target, score, write reports."""

import json
from datetime import date
from pathlib import Path
from statistics import mean as _mean
from typing import cast

from agentjudge import metrics as m
from agentjudge.config import EvalFileConfig
from agentjudge.gen_metrics import faithfulness
from agentjudge.judge import mock_judge_score
from agentjudge.schemas import GoldenRecord, ScoredRecord
from agentjudge.targets import OpsCopilotTarget, StubTarget, Target


def load_golden_set(path: str | Path) -> list[GoldenRecord]:
    """Read + validate golden_set.jsonl (one GoldenRecord per line)."""
    records: list[GoldenRecord] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(GoldenRecord.model_validate_json(line))
    return records


def select_subset(records: list[GoldenRecord], subset: str = "all") -> list[GoldenRecord]:
    """subset: 'all' | 'smoke' | 'category:<name>'."""
    if subset == "all":
        return records
    if subset == "smoke":
        return [r for r in records if r.smoke]
    if subset.startswith("category:"):
        cat = subset.split(":", 1)[1]
        return [r for r in records if r.category == cat]
    raise ValueError(f"unknown subset: {subset}")


def build_target(name: str, base_url: str, records: list[GoldenRecord]) -> Target:
    """Factory so later targets (incident_commander, ...) plug in here."""
    if name == "stub":
        return StubTarget(records)
    if name == "opscopilot":
        return OpsCopilotTarget(base_url)
    raise ValueError(f"unknown target: {name}")


def _refused(text: str) -> bool:
    t = text.lower()
    return "must refuse" in t or "can't answer" in t or "cannot answer" in t


def _pctl(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1))))
    return ordered[idx]


def score_record(rec: GoldenRecord, target: Target, top_k: int = 5) -> ScoredRecord:
    """Run one golden record through the target and score it."""
    retrieved = target.search(rec.question, top_k)
    ans = target.ask(rec.question, top_k)
    # Retrieval answers use search() IDs; generation uses the ask() answer.
    used_ids = ans.doc_ids or retrieved
    faith = faithfulness(ans.answer, [rec.reference_answer] if rec.reference_answer else [])
    judge = mock_judge_score(rec.question, ans, rec.reference_answer, rec.must_refuse)
    refused = _refused(ans.answer)
    return ScoredRecord(
        id=rec.id,
        category=rec.category,
        hit_at_5=m.hit_rate_at_k(used_ids, rec.expected_doc_ids, top_k),
        recall_at_5=m.recall_at_k(used_ids, rec.expected_doc_ids, top_k),
        reciprocal_rank=m.reciprocal_rank(used_ids, rec.expected_doc_ids),
        context_precision=m.context_precision(used_ids, rec.expected_doc_ids),
        context_recall=m.context_recall(used_ids, rec.expected_doc_ids),
        faithfulness=float(faith["score"]),
        judge_correctness=judge["correctness"],
        judge_completeness=judge["completeness"],
        judge_safety=judge["safety"],
        refused=refused,
        refusal_correct=(refused == rec.must_refuse),
        citation_validity=m.citation_validity(ans.citations, used_ids),
        latency_ms=ans.latency_ms,
        cost_usd=ans.cost_usd,
    )


def summarize(scored: list[ScoredRecord]) -> dict[str, float]:
    """Aggregate per-record scores into run-level numbers."""
    return {
        "n": float(len(scored)),
        "hit_rate_at_5": m.mean([s.hit_at_5 for s in scored]),
        "recall_at_5": m.mean([s.recall_at_5 for s in scored]),
        "mrr": m.mean([s.reciprocal_rank for s in scored]),
        "context_precision": m.mean([s.context_precision for s in scored]),
        "context_recall": m.mean([s.context_recall for s in scored]),
        "faithfulness": m.mean([s.faithfulness for s in scored]),
        "judge_correctness_mean": m.mean([float(s.judge_correctness) for s in scored]),
        "refusal_accuracy": m.mean([1.0 if s.refusal_correct else 0.0 for s in scored]),
        "citation_validity": m.mean([s.citation_validity for s in scored]),
        "p50_latency_ms": _pctl([s.latency_ms for s in scored], 50),
        "p95_latency_ms": _pctl([s.latency_ms for s in scored], 95),
        "cost_usd": sum(s.cost_usd for s in scored),
    }


def run_eval(
    records: list[GoldenRecord],
    target: Target,
    top_k: int = 5,
    repeat: int = 1,
) -> dict[str, object]:
    """Run all records (repeat times) -> report dict with spread when repeat>1."""
    repeats: list[dict[str, float]] = []
    scored: list[ScoredRecord] = []
    for _ in range(max(1, repeat)):
        batch = [score_record(r, target, top_k) for r in records]
        repeats.append(summarize(batch))
        scored = batch  # keep last full batch for per-record details
    summary = summarizespread(repeats) if len(repeats) > 1 else dict(repeats[0])
    worst = sorted(scored, key=lambda s: (s.judge_correctness, s.faithfulness))[:5]
    report: dict[str, object] = {
        "target": target.name,
        "date": str(date.today()),
        "n": len(scored),
        "repeat": len(repeats),
        "summary": summary,
        "records": [s.model_dump() for s in scored],
        "worst_5": [s.model_dump() for s in worst],
        "cost_usd": summary.get("cost_usd", 0.0),
    }
    if len(repeats) > 1:
        report["spread"] = {
            k: {
                "min": min(r[k] for r in repeats),
                "max": max(r[k] for r in repeats),
            }
            for k in repeats[0]
        }
    return report


def summarizespread(repeats: list[dict[str, float]]) -> dict[str, float]:
    """Mean of each metric across repeats (spread itself goes in report['spread'])."""
    keys = repeats[0].keys()
    return {k: _mean([r[k] for r in repeats]) for k in keys}


def write_reports(report: dict[str, object], out_dir: str | Path, stem: str) -> tuple[Path, Path]:
    """Write <stem>.json (machine) + <stem>.md (human) reports."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / f"{stem}.json"
    md_path = out / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def render_markdown(report: dict[str, object]) -> str:
    """README-ready Markdown summary of a run report."""
    s = report.get("summary", {})
    assert isinstance(s, dict)
    lines = [
        f"# AgentJudge run — {report.get('target')} ({report.get('date')})",
        "",
        f"n={report.get('n')} repeat={report.get('repeat')} "
        f"cost=${cast(float, report.get('cost_usd', 0.0)):.2f}",
        "",
        "| metric | value |",
        "|---|---|",
    ]
    for k, v in s.items():
        val = f"{float(v):.3f}" if isinstance(v, (int, float)) else str(v)
        lines.append(f"| {k} | {val} |")
    spread = report.get("spread")
    if isinstance(spread, dict) and "faithfulness" in spread:
        f = spread["faithfulness"]
        assert isinstance(f, dict)
        lines += [
            "",
            f"Spread over {report.get('repeat')} repeats "
            f"(faithfulness min–max: {f['min']:.3f}–{f['max']:.3f}). "
            "Small deltas (<0.02) are noise, not regressions.",
        ]
    lines += ["", "## Worst 5 questions", ""]
    worst = report.get("worst_5", [])
    assert isinstance(worst, list)
    for w in worst:
        assert isinstance(w, dict)
        lines.append(
            f"- {w['id']} ({w['category']}): judge={w['judge_correctness']}/5 "
            f"faithfulness={float(w['faithfulness']):.2f}"
        )
    lines.append("")
    return "\n".join(lines)


def run_from_config(
    set_path: str | Path,
    subset: str,
    cfg: EvalFileConfig,
    out_dir: str | Path = "reports",
    stem: str | None = None,
) -> tuple[Path, Path]:
    """Load set, build target from config, run, write reports. Returns paths."""
    records = select_subset(load_golden_set(set_path), subset)
    target = build_target(cfg.target, cfg.target_url, records)
    report = run_eval(records, target, top_k=cfg.top_k, repeat=cfg.repeat)
    name = stem or f"run_{target.name}_{date.today().isoformat()}"
    return write_reports(report, out_dir, name)
