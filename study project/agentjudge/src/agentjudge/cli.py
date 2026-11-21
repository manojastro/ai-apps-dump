"""Typer CLI: run / compare / gate / calibrate."""

import json
from datetime import date
from pathlib import Path
from typing import Annotated, cast

import typer

from agentjudge.calibration import calibrate as do_calibrate
from agentjudge.compare import compare_runs, detect_regressions
from agentjudge.config import EvalFileConfig, load_eval_config
from agentjudge.runner import run_from_config

app = typer.Typer(help="AgentJudge: eval harness + CI quality gate (mock-first, offline).")


@app.command()
def run(
    target: Annotated[str, typer.Option(help="stub | opscopilot")] = "stub",
    set: Annotated[str, typer.Option(help="golden set path")] = "golden_set.jsonl",
    config: Annotated[str, typer.Option(help="eval config yaml")] = "eval_config.yaml",
    subset: Annotated[str, typer.Option(help="all | smoke | category:<name>")] = "all",
    repeat: Annotated[int, typer.Option(help="repeats for variance (M8)")] = 0,
    out: Annotated[str, typer.Option(help="reports dir")] = "reports",
) -> None:
    """Run the golden set against a target and write JSON + Markdown reports."""
    cfg = load_eval_config(config)
    cfg.target = target  # CLI flag wins over yaml
    if repeat > 0:
        cfg.repeat = repeat
    tag = subset.replace(":", "-")
    stem = f"run_{target}_{tag}_{date.today().isoformat()}"
    json_path, md_path = run_from_config(set, subset, cfg, out, stem)
    summary = json.loads(json_path.read_text(encoding="utf-8"))["summary"]
    typer.echo(f"wrote {json_path} + {md_path}")
    typer.echo(
        f"hit_rate@5={summary['hit_rate_at_5']:.3f} "
        f"faithfulness={summary['faithfulness']:.3f} "
        f"refusal_accuracy={summary['refusal_accuracy']:.3f} "
        f"cost=${summary['cost_usd']:.2f}"
    )


@app.command()
def compare(
    a: Annotated[str, typer.Argument(help="current run JSON")],
    b: Annotated[str, typer.Argument(help="baseline run JSON")] = "",
    baseline: Annotated[str, typer.Option(help="alias for b")] = "",
) -> None:
    """Show metric deltas between two runs (arrows: up good, down bad)."""
    base_path = b or baseline
    if not base_path:
        raise typer.BadParameter("provide second run: compare A B")
    cur = json.loads(Path(a).read_text(encoding="utf-8"))
    base = json.loads(Path(base_path).read_text(encoding="utf-8"))
    for metric, vals in compare_runs(cur, base).items():
        arrow = "up" if vals["delta"] >= 0 else "DOWN"
        typer.echo(
            f"{metric}: {vals['baseline']:.3f} -> {vals['current']:.3f} "
            f"({vals['delta']:+.3f} {arrow})"
        )


@app.command()
def gate(
    report: Annotated[str, typer.Argument(help="run JSON to check")],
    baseline: Annotated[str, typer.Option(help="baseline run JSON")] = "reports/baseline.json",
    config: Annotated[str, typer.Option(help="eval config yaml")] = "eval_config.yaml",
    tolerance: Annotated[float, typer.Option(help="allowed drop vs baseline")] = 0.02,
) -> None:
    """CI quality gate: exit 1 on threshold breach or regression."""
    cfg: EvalFileConfig = load_eval_config(config)
    cur = json.loads(Path(report).read_text(encoding="utf-8"))
    summary = cur["summary"]
    failures: list[str] = []
    t = cfg.thresholds
    checks = [
        ("faithfulness", summary["faithfulness"], t.faithfulness, ">="),
        ("hit_rate_at_5", summary["hit_rate_at_5"], t.hit_rate_at_5, ">="),
        ("refusal_accuracy", summary["refusal_accuracy"], t.refusal_accuracy, ">="),
        ("p95_latency_ms", summary["p95_latency_ms"], t.p95_latency_ms, "<="),
    ]
    for name, got, want, op in checks:
        ok = got >= want if op == ">=" else got <= want
        typer.echo(f"{name}: {got:.3f} {op} {want:.3f} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{name} {got:.3f} breaches {op} {want:.3f}")
    if Path(baseline).exists():
        base = json.loads(Path(baseline).read_text(encoding="utf-8"))
        for reg in detect_regressions(cur, base, tolerance):
            msg = f"{reg.metric} regressed {reg.baseline:.3f}->{reg.current:.3f}"
            typer.echo(f"regression: {msg}")
            failures.append(msg)
    else:
        typer.echo(f"no baseline at {baseline}; threshold checks only")
    if failures:
        typer.echo("GATE FAILED")
        raise typer.Exit(code=1)
    typer.echo("GATE PASSED")


@app.command(name="calibrate")
def calibrate_cmd(
    human: Annotated[str, typer.Option(help="human labels jsonl")] = "labels/human_20.jsonl",
    judge: Annotated[str, typer.Option(help="run JSON with judge scores")] = "",
) -> None:
    """Print Cohen's kappa between human labels and the mock judge."""
    if not judge:
        raise typer.BadParameter("--judge reports/run_X.json is required")
    result = do_calibrate(human, judge)
    typer.echo(f"n={result['n']} kappa={cast(float, result['kappa']):.3f}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
