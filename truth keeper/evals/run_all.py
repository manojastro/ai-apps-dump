"""One command for every eval: detection + proposals, on both datasets, for each prompt version.

    python -m evals.run_all                                  # MOCK, clean profile, prompts v1+v2
    python -m evals.run_all --profile noisy                  # MOCK with fault injection
    LLM_MODE=real python -m evals.run_all --limit 50 --yes   # real model (costs money; ask first)

Writes evals/results/<date>_<prompt_version>.json per prompt version and
evals/results/<date>_summary.md with the comparison table. Every FAILED or wrong proposal is
saved to evals/regressions/ as a fixed test case (unless --no-regressions).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.config import ROOT, get_settings
from app.core.regressions import build_case, save_case
from app.llm.client import LLMClient
from app.llm.mock import MockLLM
from data.generator.generate import generate
from evals import detection_eval, proposal_eval

DATASETS = {
    "default": {"seed": 42, "profile": "default", "dir": "data/generated",
                "gt": "data/generator/ground_truth.json"},
    "hard": {"seed": 7, "profile": "hard", "dir": "data/generated_seed7",
             "gt": "data/generated_seed7/ground_truth.json"},
}


def ensure_dataset(name: str) -> tuple[Path, Path]:
    d = DATASETS[name]
    data_dir, gt = ROOT / d["dir"], ROOT / d["gt"]
    if not (data_dir / "crm.db").exists() or not gt.exists():
        generate(d["seed"], 500, data_dir, gt, d["profile"])
    return data_dir, gt


def harvest_regressions(result: dict, directory: Path) -> list[str]:
    saved = []
    for rec in result["records"]:
        conflict = {"id": rec["conflict_id"], "type": rec["type"], "customer_key": rec["customer_key"],
                    "evidence": rec["evidence"]}
        if rec["status"] == "FAILED":
            case = build_case(source="failed", conflict=conflict, prompt_version=result["prompt_version"],
                              recorded_responses=rec["raw_responses"],
                              expect_mock={"status": "FAILED", "failure_category": rec["failure_category"]},
                              expected_action=rec["expected_action"],
                              note=f"FAILED after retries: {rec['failure_reason']}")
        elif rec["expected_action"] and not rec["correct"]:
            case = build_case(source="wrong_action", conflict=conflict, prompt_version=result["prompt_version"],
                              recorded_responses=rec["raw_responses"],
                              expect_mock={"status": "PENDING_REVIEW", "action": rec["action"]},
                              expected_action=rec["expected_action"],
                              note=f"proposed {rec['action']}, ground truth expects {rec['expected_action']}")
        else:
            continue
        save_case(directory, case)
        saved.append(case["id"])
    return saved


def _slim(result: dict) -> dict:
    out = {k: v for k, v in result.items() if k != "records"}
    out["records"] = [{k: v for k, v in r.items() if k != "evidence"} for r in result["records"]]
    return out


def comparison_table(rows: list[dict]) -> str:
    head = ("| dataset | prompt | mode/model | n | action acc | params acc | schema-valid (1st try) | failure rate |"
            " mean attempts | tokens in/out | cost USD | p50 / p95 ms |\n" + "|---" * 12 + "|")
    lines = [head]
    for r in rows:
        m = r["metrics"]
        est = " (est.)" if m["tokens_estimated"] else ""
        lines.append(
            f"| {r['dataset']['profile']} (seed {r['dataset']['seed']}) | {r['prompt_version']} | "
            f"{r['llm_mode']}/{r['model']} | {r['n_conflicts']} | {m['action_accuracy']} | {m['params_accuracy']} | "
            f"{m['schema_valid_rate']} | {m['failure_rate']} | {m['mean_attempts']} | "
            f"{m['input_tokens']}/{m['output_tokens']}{est} | {m['cost_usd_total']} | "
            f"{m['latency_ms_p50']} / {m['latency_ms_p95']} |")
    return "\n".join(lines)


def detection_table(rows: list[dict]) -> str:
    lines = ["| dataset | type | precision | recall | F1 |", "|---|---|---|---|---|"]
    for r in rows:
        name = f"{r['dataset']['profile']} (seed {r['dataset']['seed']})"
        for t, m in list(r["per_type"].items()) + [("OVERALL", r["overall"])]:
            lines.append(f"| {name} | {t} | {m['precision']} | {m['recall']} | {m['f1']} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    s = get_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["default", "hard"], choices=list(DATASETS))
    ap.add_argument("--prompts", nargs="+", default=["v1", "v2"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--profile", default=None, help="mock profile: clean|noisy")
    ap.add_argument("--yes", action="store_true", help="confirm a real (paid) run")
    ap.add_argument("--no-regressions", action="store_true")
    ap.add_argument("--tag", default="", help="extra label for result file names")
    args = ap.parse_args(argv)
    if s.llm_mode == "real" and not args.yes:
        raise SystemExit("LLM_MODE=real costs money. Re-run with --yes after checking the expected cost.")

    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    tag = f"_{args.tag}" if args.tag else ""
    s.results_dir.mkdir(parents=True, exist_ok=True)
    det_rows, prop_rows, saved = [], [], []
    for ds in args.datasets:
        data_dir, gt = ensure_dataset(ds)
        det = detection_eval.evaluate(data_dir, gt)
        det_rows.append(det)
        print(f"\n== detection: {ds}\n{detection_eval.format_table(det)}")
    by_prompt: dict[str, list[dict]] = {}
    for pv in args.prompts:
        for ds in args.datasets:
            data_dir, gt = ensure_dataset(ds)
            profile = args.profile or s.mock_profile
            llm = LLMClient(s, mock=MockLLM(profile=profile) if s.llm_mode == "mock" else None)
            r = proposal_eval.evaluate(data_dir, gt, llm, pv, args.limit)
            prop_rows.append(r)
            by_prompt.setdefault(pv, []).append(r)
            print(proposal_eval.summary_line(r))
            if not args.no_regressions:
                saved += harvest_regressions(r, s.regressions_dir)
    for pv, rows in by_prompt.items():
        path = s.results_dir / f"{stamp}_{pv}{tag}.json"
        path.write_text(json.dumps({"generated_at": datetime.now(UTC).isoformat(), "prompt_version": pv,
                                    "detection": det_rows, "proposals": [_slim(r) for r in rows]},
                                   indent=2, default=str), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    md = s.results_dir / f"{stamp}_summary{tag}.md"
    mode_note = ("MOCK mode: the 'model' is a deterministic fixture, so these numbers test the pipeline and "
                 "validators, not a real LLM." if s.llm_mode == "mock" else "REAL model run.")
    md.write_text(
        f"# Eval summary {stamp}{tag}\n\n{mode_note}\n\n## Detection\n\n{detection_table(det_rows)}\n\n"
        f"## Proposals\n\n{comparison_table(prop_rows)}\n\n"
        f"Regression cases saved this run: {len(set(saved))}\n", encoding="utf-8")
    print(f"wrote {md.relative_to(ROOT)}  (regression cases saved: {len(set(saved))})")


if __name__ == "__main__":
    main()
