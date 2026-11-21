"""Run the golden scenarios through SchemaGuard and report real metrics.

    uv run python eval/run_eval.py --llm fake            # deterministic, used in CI
    uv run python eval/run_eval.py --llm azure           # real LLM (needs keys; costs money)

Writes eval/results/<llm>-results.json and eval/results/summary.md.
Approvals during eval are given by a bot reviewer ("eval-bot") so the full flow, including the
local branch, is exercised. Nothing here pushes anywhere.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from schemaguard.config import Settings  # noqa: E402
from schemaguard.sandbox import run_sandbox  # noqa: E402
from schemaguard.schemas.mutate import apply_mutations  # noqa: E402
from schemaguard.service import SchemaGuardService  # noqa: E402

ASSET_TYPES = {"Column", "Visual", "Dashboard"}


def load_scenarios(d: Path) -> list[dict[str, Any]]:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.yaml"))]


def predicted_impacts(svc: SchemaGuardService, st: dict[str, Any]) -> set[str]:
    out = set()
    for n in st.get("impacted_nodes", []):
        if n["context"] or n["type"] not in ASSET_TYPES:
            continue
        if n["type"] == "Column" and svc.lineage.node(n["id"]).get("layer") == "raw":
            continue
        out.add(n["id"])
    return out


def predicted_verdicts(st: dict[str, Any]) -> dict[str, str]:
    v = {a["asset"]: a["verdict"] for a in st.get("assessments", [])}
    v.update({f"dashboard:{k}": x for k, x in (st.get("aggregate") or {}).get("dashboards", {}).items()})
    return v


def route_of(status: str) -> str:
    return {"awaiting_approval": "approval", "escalated": "escalate", "no_impact": "report"}.get(
        status, status
    )


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def percentile(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def run(args: argparse.Namespace) -> dict[str, Any]:
    scenarios = load_scenarios(args.scenarios)
    if args.only:
        scenarios = [s for s in scenarios if s["id"] in args.only.split(",")]
    home = Path(tempfile.mkdtemp(prefix="sg-eval-"))
    settings = Settings(
        home=home, pipeline_dir=ROOT / "demo_pipeline", llm_provider=args.llm, log_level="WARNING"
    )
    svc = SchemaGuardService(settings)
    current = {
        p.name.removesuffix(".avsc"): json.loads(p.read_text(encoding="utf-8"))
        for p in (ROOT / "demo_pipeline" / "avro").glob("*.avsc")
    }
    rows = []
    for sc in scenarios:
        exp = sc["expected"]
        new_schema = apply_mutations(current[sc["topic"]], sc["mutations"])
        t0 = time.perf_counter()
        run_id, _ = svc.submit_change(sc["topic"], new_schema, source="eval")
        t_decision = time.perf_counter() - t0
        first = svc.get_run(run_id)
        status_first = first["status"]
        if status_first == "awaiting_approval":
            svc.approve(run_id, reviewer="eval-bot", comment="automated eval approval")
        t_total = time.perf_counter() - t0
        final = svc.get_run(run_id)
        st = final["state"]
        pred_imp, exp_imp = predicted_impacts(svc, st), set(exp["impacted"])
        pv = predicted_verdicts(st)
        verdict_checks = {
            a: {"expected": v, "predicted": pv.get(a, "missing")} for a, v in exp["verdicts"].items()
        }
        attempts = st.get("attempts", [])
        ct = st.get("cost_tracking", {})
        row = {
            "id": sc["id"],
            "status_first": status_first,
            "status_final": final["status"],
            "route": {"expected": exp["route"], "predicted": route_of(status_first)},
            "change_class": {
                "expected": exp["change_class"],
                "predicted": (st.get("change_class") or {}).get("change_class"),
            },
            "impact": {
                "tp": sorted(pred_imp & exp_imp),
                "fp": sorted(pred_imp - exp_imp),
                "fn": sorted(exp_imp - pred_imp),
            },
            "verdicts": verdict_checks,
            "fix": {
                "expected_pass": exp.get("fix_should_pass"),
                "entered_loop": bool(attempts),
                "passed": bool(attempts) and bool(st.get("test_results", {}).get("ok")),
                "attempts": len(attempts),
                "retries": st.get("retry_count", 0),
                "strategies": [a["strategy"] for a in attempts],
            },
            "escalated": final["status"] == "escalated",
            "injection": {
                "expected": bool(exp.get("injection_flagged")),
                "predicted": bool(st.get("injection_findings")),
            },
            "failing_tables": {
                "expected": exp.get("failing_tables"),
                "predicted": (st.get("aggregate") or {}).get("build_impact", {}).get("failing_tables", []),
            },
            "latency_s": {"to_decision": round(t_decision, 3), "end_to_end": round(t_total, 3)},
            "tokens": ct.get("tokens_in", 0) + ct.get("tokens_out", 0),
            "llm_calls": ct.get("calls", 0),
            "cost_usd": ct.get("usd", 0.0),
            "error": final.get("error"),
        }
        # Independent oracle: run the UNCHANGED pipeline under the new schema in DuckDB.
        oracle = run_sandbox(
            ROOT / "demo_pipeline", home / "oracle" / sc["id"], "", sc["topic"], new_schema, 120
        )
        actual_failed = sorted(
            t
            for task in oracle.get("tasks", [])
            if task["status"] == "failed"
            for t, _ in [
                (w.split(":", 1)[1], None) for w, _d in svc.lineage.out(f"task:{task['task_id']}", "WRITES")
            ]
        )
        actual_tests = sorted(t["name"] for t in oracle.get("tests", []) if not t["passed"])
        pred_tests = sorted(
            {
                a["asset"].removeprefix("test:")
                for a in st.get("assessments", [])
                if a["type"] == "DataTest" and a["verdict"] == "breaking"
            }
            | set((st.get("aggregate") or {}).get("build_impact", {}).get("blocked_tests", []))
        )
        row["oracle"] = {
            "failed_builds": {"actual": actual_failed, "predicted": row["failing_tables"]["predicted"]},
            "failed_tests": {"actual": actual_tests, "predicted": pred_tests},
        }
        rows.append(row)
        print(f"{sc['id']:<32} {status_first:<18} -> {final['status']:<10} {t_total:6.2f}s", flush=True)
    svc.close()
    return {"rows": rows, "metrics": metrics(rows), "llm": args.llm, "home": str(home)}


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(len(r["impact"]["tp"]) for r in rows)
    fp = sum(len(r["impact"]["fp"]) for r in rows)
    fn = sum(len(r["impact"]["fn"]) for r in rows)
    vchecks = [c for r in rows for c in r["verdicts"].values()]
    vcorrect = sum(c["expected"] == c["predicted"] for c in vchecks)
    fix_expected = [r for r in rows if r["fix"]["expected_pass"] is True]
    fix_passed = [r for r in fix_expected if r["fix"]["passed"]]
    loop = [r for r in rows if r["fix"]["entered_loop"]]
    esc_correct = sum((r["route"]["expected"] == "escalate") == r["escalated"] for r in rows)
    esc_tp = sum(r["route"]["expected"] == "escalate" and r["escalated"] for r in rows)
    esc_pred = sum(r["escalated"] for r in rows)
    esc_exp = sum(r["route"]["expected"] == "escalate" for r in rows)
    lat_d = [r["latency_s"]["to_decision"] for r in rows]
    lat_e = [r["latency_s"]["end_to_end"] for r in rows]
    ft = [r for r in rows if r["failing_tables"]["expected"] is not None]
    ob = sum(
        r["oracle"]["failed_builds"]["actual"] == r["oracle"]["failed_builds"]["predicted"] for r in rows
    )
    otp = sum(
        len(set(r["oracle"]["failed_tests"]["actual"]) & set(r["oracle"]["failed_tests"]["predicted"]))
        for r in rows
    )
    opred = sum(len(r["oracle"]["failed_tests"]["predicted"]) for r in rows)
    oact = sum(len(r["oracle"]["failed_tests"]["actual"]) for r in rows)
    return {
        "scenarios": len(rows),
        "impact_precision": tp / (tp + fp) if tp + fp else 1.0,
        "impact_recall": tp / (tp + fn) if tp + fn else 1.0,
        "impact_counts": {"tp": tp, "fp": fp, "fn": fn},
        "verdict_accuracy": vcorrect / len(vchecks) if vchecks else 1.0,
        "verdict_checks": len(vchecks),
        "route_accuracy": sum(r["route"]["expected"] == r["route"]["predicted"] for r in rows) / len(rows),
        "change_class_accuracy": sum(
            r["change_class"]["expected"] == r["change_class"]["predicted"] for r in rows
        )
        / len(rows),
        "fix_test_pass_rate": len(fix_passed) / len(fix_expected) if fix_expected else 0.0,
        "fix_expected": len(fix_expected),
        "fix_passed": len(fix_passed),
        "avg_retries_in_fix_loop": statistics.mean(r["fix"]["retries"] for r in loop) if loop else 0.0,
        "runs_entering_fix_loop": len(loop),
        "escalation_accuracy": esc_correct / len(rows),
        "escalation_precision": esc_tp / esc_pred if esc_pred else 1.0,
        "escalation_recall": esc_tp / esc_exp if esc_exp else 1.0,
        "injection_detection_accuracy": sum(
            r["injection"]["expected"] == r["injection"]["predicted"] for r in rows
        )
        / len(rows),
        "failing_tables_accuracy": (
            sum(sorted(r["failing_tables"]["expected"]) == r["failing_tables"]["predicted"] for r in ft)
            / len(ft)
        )
        if ft
        else 1.0,
        "oracle_build_agreement": ob / len(rows),
        "oracle_test_precision": otp / opred if opred else 1.0,
        "oracle_test_recall": otp / oact if oact else 1.0,
        "oracle_test_counts": {"tp": otp, "predicted": opred, "actual": oact},
        "latency_to_decision_s": {"p50": percentile(lat_d, 0.5), "p95": percentile(lat_d, 0.95)},
        "latency_end_to_end_s": {"p50": percentile(lat_e, 0.5), "p95": percentile(lat_e, 0.95)},
        "tokens_per_run": {
            "mean": statistics.mean(r["tokens"] for r in rows),
            "max": max(r["tokens"] for r in rows),
        },
        "llm_calls_per_run": statistics.mean(r["llm_calls"] for r in rows),
        "cost_usd_per_run": {
            "mean": statistics.mean(r["cost_usd"] for r in rows),
            "total": sum(r["cost_usd"] for r in rows),
        },
        "errors": [r["id"] for r in rows if r["error"]],
    }


def summary_md(result: dict[str, Any], command: str) -> str:
    m = result["metrics"]
    sha = (
        subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        or "n/a"
    )
    L = [
        "# SchemaGuard evaluation summary",
        "",
        f"- **Date (UTC):** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
        f"- **Command:** `{command}`",
        f"- **Git commit:** `{sha}`  ·  **LLM provider:** `{result['llm']}`  ·  **Scenarios:** {m['scenarios']}",
        "",
    ]
    if result["llm"] == "fake":
        L += [
            "> The `fake` provider is a deterministic scripted fixer, not a model. These numbers measure SchemaGuard's",
            "> deterministic parts (lineage, verdict rules, sandbox, loop control, guardrails) and the fake's heuristics;",
            "> they say nothing about LLM quality. Token counts for `fake` are character-based estimates and cost is $0.",
            "",
        ]
    L += [
        "Labels in `eval/scenarios/` were written by the same author as the verdict rules, so the label-based",
        "metrics measure consistency with that specification. The **oracle** rows are independent: they compare",
        "predictions with what DuckDB actually does when the unchanged pipeline runs on the new schema.",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Impact precision (graph traversal) | {pct(m['impact_precision'])} ({m['impact_counts']['tp']} TP / {m['impact_counts']['fp']} FP) |",
        f"| Impact recall (graph traversal) | {pct(m['impact_recall'])} ({m['impact_counts']['fn']} FN) |",
        f"| Verdict accuracy | {pct(m['verdict_accuracy'])} over {m['verdict_checks']} labelled assets |",
        f"| Route accuracy (report / approval / escalate) | {pct(m['route_accuracy'])} |",
        f"| Change-class accuracy | {pct(m['change_class_accuracy'])} |",
        f"| Fix test-pass rate | {pct(m['fix_test_pass_rate'])} ({m['fix_passed']}/{m['fix_expected']} scenarios expected to be fixable) |",
        f"| Avg retries in fix loop | {m['avg_retries_in_fix_loop']:.2f} over {m['runs_entering_fix_loop']} runs |",
        f"| Escalation accuracy | {pct(m['escalation_accuracy'])} (precision {pct(m['escalation_precision'])}, recall {pct(m['escalation_recall'])}) |",
        f"| Injection detection accuracy | {pct(m['injection_detection_accuracy'])} |",
        f"| Failing-build prediction accuracy | {pct(m['failing_tables_accuracy'])} |",
        f"| **Oracle:** predicted failing builds = DuckDB reality | {pct(m['oracle_build_agreement'])} of scenarios |",
        f"| **Oracle:** breaking-test precision / recall vs DuckDB | {pct(m['oracle_test_precision'])} / {pct(m['oracle_test_recall'])} ({m['oracle_test_counts']['tp']} TP, {m['oracle_test_counts']['predicted']} predicted, {m['oracle_test_counts']['actual']} actual) |",
        f"| Latency to decision p50 / p95 | {m['latency_to_decision_s']['p50']:.2f}s / {m['latency_to_decision_s']['p95']:.2f}s |",
        f"| Latency end-to-end (incl. approval + branch) p50 / p95 | {m['latency_end_to_end_s']['p50']:.2f}s / {m['latency_end_to_end_s']['p95']:.2f}s |",
        f"| Tokens per run (mean / max) | {m['tokens_per_run']['mean']:.0f} / {m['tokens_per_run']['max']} |",
        f"| LLM calls per run (mean) | {m['llm_calls_per_run']:.1f} |",
        f"| Estimated cost per run (mean) / total | ${m['cost_usd_per_run']['mean']:.4f} / ${m['cost_usd_per_run']['total']:.4f} |",
        "",
        "## Per scenario",
        "",
        "| Scenario | Route exp → got | Final | Impact FP/FN | Verdicts ok | Fix | Retries | Time (s) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in result["rows"]:
        ok = sum(c["expected"] == c["predicted"] for c in r["verdicts"].values())
        fix = "—" if not r["fix"]["entered_loop"] else ("pass" if r["fix"]["passed"] else "fail")
        L.append(
            f"| {r['id']} | {r['route']['expected']} → {r['route']['predicted']} | {r['status_final']} | "
            f"{len(r['impact']['fp'])}/{len(r['impact']['fn'])} | {ok}/{len(r['verdicts'])} | {fix} | {r['fix']['retries']} | {r['latency_s']['end_to_end']:.2f} |"
        )
    orc = [
        (r["id"], k, r["oracle"][k])
        for r in result["rows"]
        for k in ("failed_builds", "failed_tests")
        if sorted(r["oracle"][k]["actual"]) != sorted(r["oracle"][k]["predicted"])
    ]
    L += ["", "## Oracle disagreements (prediction vs running the unchanged pipeline on the new schema)", ""]
    L += [f"- `{sid}` {k}: predicted {v['predicted']}, actual {v['actual']}" for sid, k, v in orc] or [
        "None."
    ]
    mism = [
        (r["id"], a, c)
        for r in result["rows"]
        for a, c in r["verdicts"].items()
        if c["expected"] != c["predicted"]
    ]
    imp = [(r["id"], k, x) for r in result["rows"] for k in ("fp", "fn") for x in r["impact"][k]]
    L += ["", "## Mismatches", ""]
    if not mism and not imp:
        L.append("None.")
    for sid, a, c in mism:
        L.append(f"- `{sid}` verdict `{a}`: expected **{c['expected']}**, got **{c['predicted']}**")
    for sid, k, x in imp:
        L.append(f"- `{sid}` impact {'false positive' if k == 'fp' else 'false negative'}: `{x}`")
    if result["metrics"]["errors"]:
        L += ["", "## Run errors", ""] + [f"- {e}" for e in result["metrics"]["errors"]]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", default="fake", choices=["fake", "azure", "openai", "anthropic"])
    ap.add_argument("--scenarios", type=Path, default=ROOT / "eval" / "scenarios")
    ap.add_argument("--out", type=Path, default=ROOT / "eval" / "results")
    ap.add_argument("--only", default="", help="comma-separated scenario ids")
    args = ap.parse_args()
    result = run(args)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.llm}-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    cmd = "uv run python eval/run_eval.py " + " ".join(sys.argv[1:])
    md = summary_md(result, cmd.strip())
    (args.out / "summary.md" if args.llm == "fake" else args.out / f"summary-{args.llm}.md").write_text(
        md, encoding="utf-8"
    )
    print(md)


if __name__ == "__main__":
    main()
