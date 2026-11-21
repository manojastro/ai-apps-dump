"""Markdown + CSV reports. Every number comes from a run's decisions.jsonl."""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from .config import Config, paths
from .evaluate import BAD_LABELS, DRAFT, REVIEWED, compute_metrics, tune_thresholds
from .gate import Thresholds
from .judges.base import LABELS
from .pipeline import ClaimDecision, read_decisions

SMALL_SAMPLE = "**Small sample. Results are indicative, not statistically strong.**"

BANNERS = {
    "MOCK": (
        "**MODE: MOCK.** Judge outputs come from the offline heuristic MockJudge. "
        "They are not Jev results and say nothing about Jev or any model."
    ),
    "LIVE": "**MODE: LIVE.** Judge outputs come from real API calls to the model(s) listed below.",
    "NO-MODEL": (
        "**MODE: NO-MODEL (string-match baseline).** Check A only. No model was called; "
        "every quote found in the source passes."
    ),
}


# --------------------------------------------------------------------------- helpers


def list_runs() -> list[dict]:
    out = []
    for p in sorted(paths()["runs"].glob("*/run.json")):
        meta = json.loads(p.read_text(encoding="utf-8"))
        if meta.get("kind") == "eval":
            meta["_dir"] = p.parent
            out.append(meta)
    return out


def select_runs(run_ids: list[str] | None) -> list[dict]:
    runs = list_runs()
    if run_ids:
        chosen = [r for r in runs if r["run_id"] in run_ids]
        missing = set(run_ids) - {r["run_id"] for r in chosen}
        if missing:
            raise FileNotFoundError(f"unknown run id(s): {sorted(missing)}")
        return chosen
    latest: dict[str, dict] = {}
    for r in runs:
        if r["judge"] not in latest or r["started"] >= latest[r["judge"]]["started"]:
            latest[r["judge"]] = r
    order = {"jev": 0, "llm": 1, "stringmatch": 2, "mock": 3}
    return sorted(latest.values(), key=lambda r: order.get(r["judge"], 9))


def frac(num: int | None, den: int | None) -> str:
    if not den:
        return "n/a (0 items)"
    return f"{num}/{den} ({100 * num / den:.1f}%)"


def num(x: float | None, digits: int = 1, suffix: str = "") -> str:
    return "n/a" if x is None else f"{x:.{digits}f}{suffix}"


def money(x: float | None) -> str:
    return "unknown" if x is None else f"${x:.4f}"


def split_of(decisions: list[ClaimDecision], split: str) -> list[ClaimDecision]:
    return [d for d in decisions if d.split == split]


def sizes(ds: list[ClaimDecision]) -> str:
    good = sum(1 for d in ds if d.label == "supports")
    bad = sum(1 for d in ds if d.label in BAD_LABELS)
    return f"n={len(ds)} (good {good} / bad {bad})"


# --------------------------------------------------------------------------- per-run report


def analyse_run(meta: dict, cfg: Config, decisions: list[ClaimDecision] | None = None) -> dict:
    if decisions is None:
        decisions = read_decisions(meta["_dir"])
    dev, test = split_of(decisions, "dev"), split_of(decisions, "test")
    th_run = Thresholds(**meta["thresholds_at_run"])
    tuned, grid = tune_thresholds(dev, cfg)
    return {
        "meta": meta,
        "decisions": decisions,
        "dev": dev,
        "test": test,
        "th_run": th_run,
        "th_tuned": tuned,
        "grid": grid,
        "test_run": compute_metrics(test, th_run),
        "test_tuned": compute_metrics(test, tuned) if tuned else None,
        "dev_run": compute_metrics(dev, th_run),
        "dev_tuned": compute_metrics(dev, tuned) if tuned else None,
        "label_sources": {
            DRAFT: sum(1 for d in decisions if d.label_source == DRAFT),
            REVIEWED: sum(1 for d in decisions if d.label_source == REVIEWED),
            "unlabelled": sum(1 for d in decisions if d.label is None),
        },
    }


def _headline_rows(m: dict) -> list[tuple[str, str]]:
    return [
        ("**Wrong-pass rate** (bad claims that got PASS)", f"**{frac(m['wrong_pass'], m['n_bad'])}**"),
        ("Bad-citation catch rate (bad claims -> FAIL or HUMAN_REVIEW)", frac(m["caught"], m["n_bad"])),
        ("False alarm rate (good claims not PASS)", frac(m["false_alarm"], m["n_good"])),
        ("Human-review rate", frac(m["human_review"], m["n"])),
        ("Verdict counts", ", ".join(f"{k} {v}" for k, v in sorted(m["verdict_counts"].items()))),
        ("Judge errors", str(m["errors"])),
    ]


def render_run_md(a: dict, cfg: Config) -> str:
    meta = a["meta"]
    mode = meta["mode"]
    ls = a["label_sources"]
    tuned: Thresholds | None = a["th_tuned"]
    t_run, t_tun = a["test_run"], a["test_tuned"]
    L: list[str] = []
    L.append(f"# Citation Guard eval: `{meta['judge']}` judge ({mode})")
    L.append("")
    L.append(f"> {BANNERS.get(mode, mode)}")
    L.append(">")
    L.append(f"> {SMALL_SAMPLE}")
    L.append(">")
    L.append(
        f"> Labels: {ls[DRAFT]} `claude_draft`, {ls[REVIEWED]} `manoj_reviewed`"
        + (f", {ls['unlabelled']} unlabelled (excluded)" if ls["unlabelled"] else "")
        + ". Any metric based on draft labels is provisional."
    )
    L.append("")
    L.append("| Field | Value |")
    L.append("|---|---|")
    L.append(f"| Mode | **{mode}** |")
    L.append(f"| Judge | `{meta['judge']}` |")
    L.append(f"| Model id(s) answering | {', '.join(f'`{m}`' for m in meta['models_seen']) or 'none (no model called)'} |")
    L.append(f"| Pinned Jev model (config) | `{cfg.jev.model}` |")
    L.append(f"| Run date | {meta['started']} |")
    L.append(f"| Run id | `{meta['run_id']}` |")
    L.append(f"| Claims file | `{meta['claims_file']}` (sha256 `{meta['claims_sha256'][:12]}`) |")
    L.append(f"| Dev split | {sizes(a['dev'])} |")
    L.append(f"| Test split | {sizes(a['test'])} |")
    L.append(f"| External API calls | {meta['api_calls']} (cap {meta['max_api_calls_per_run']}) |")
    L.append(f"| Source log | `runs/{meta['run_id']}/decisions.jsonl` |")
    L.append("")

    L.append("## Thresholds")
    L.append("")
    L.append(f"- At run time (config.yaml): pass_supports >= {a['th_run'].pass_supports:.2f}, fail_contradicts >= {a['th_run'].fail_contradicts:.2f}")
    if tuned:
        L.append(f"- Tuned on the **dev split only**: pass_supports >= {tuned.pass_supports:.2f}, fail_contradicts >= {tuned.fail_contradicts:.2f}")
        L.append(
            f"  (policy: dev wrong-pass rate <= {cfg.tuning.max_wrong_pass_rate:.2f}, then lowest false-alarm rate, "
            "then lowest review rate; ties go to the stricter threshold)"
        )
    else:
        L.append("- No thresholds to tune (string-match baseline has no probabilities).")
    if meta["judge"] == "llm":
        L.append("- LLM probabilities are prompted estimates, not calibrated. Its thresholds are tuned separately and must not be swapped with Jev's.")
    if meta["judge"] == "mock":
        L.append("- Mock thresholds are tuned only to exercise the code path. They mean nothing for Jev.")
    L.append("")

    L.append("## Test split: headline")
    L.append("")
    if t_tun:
        L.append("| Metric | Config thresholds | Dev-tuned thresholds |")
        L.append("|---|---|---|")
        for (name, v1), (_, v2) in zip(_headline_rows(t_run), _headline_rows(t_tun)):
            L.append(f"| {name} | {v1} | {v2} |")
    else:
        L.append("| Metric | Value |")
        L.append("|---|---|")
        for name, v in _headline_rows(t_run):
            L.append(f"| {name} | {v} |")
    L.append("")

    L.append("## Test split: confusion matrix (claims that reached Check B)")
    L.append("")
    if t_run["n_reached_check_b"]:
        L.append("Rows are labels, columns are the judge's highest-probability label.")
        L.append("")
        L.append("| label \\ predicted | " + " | ".join(LABELS) + " |")
        L.append("|---|" + "---|" * len(LABELS))
        for t in LABELS:
            L.append(f"| {t} | " + " | ".join(str(t_run["confusion"][t][p]) for p in LABELS) + " |")
        if t_run["fabricated_reached_check_b"]:
            L.append("")
            L.append(f"{t_run['fabricated_reached_check_b']} claim(s) labelled `fabricated` reached Check B (quote was found): check those labels.")
    else:
        L.append("No claims reached Check B in this run (no judge).")
    L.append("")

    cal = t_run["calibration"]
    L.append("## Test split: calibration")
    L.append("")
    if cal["n"]:
        L.append(f"Confidence = judge confidence in its top label; accuracy = top label equals the 3-way label. n={cal['n']}.")
        L.append("")
        L.append("| Confidence bin | n | Avg confidence | Accuracy | Note |")
        L.append("|---|---|---|---|---|")
        for b in cal["bins"]:
            if b["n"] == 0:
                continue
            note = f"WARNING: {b['warning']}" if b["warning"] else ""
            L.append(f"| {b['bin']} | {b['n']} | {num(b['avg_confidence'], 3)} | {num(b['accuracy'], 3)} | {note} |")
        L.append("")
        L.append(f"Expected calibration error (ECE, 10 equal-width bins): **{num(cal['ece'], 3)}**")
        if any(b["warning"] == "fewer than 10 items" for b in cal["bins"]):
            L.append("")
            L.append("WARNING: one or more bins hold fewer than 10 items. ECE on this sample is not reliable.")
    else:
        L.append("Not applicable: no judge probabilities in this run.")
    L.append("")

    L.append("## Latency and cost (test split)")
    L.append("")
    L.append("| Measure | Value |")
    L.append("|---|---|")
    L.append(f"| Per-claim latency p50 / p95 (Check A + judge) | {num(t_run['latency_ms_p50'])} ms / {num(t_run['latency_ms_p95'])} ms |")
    L.append(f"| Judge call latency p50 / p95 | {num(t_run['judge_latency_ms_p50'])} ms / {num(t_run['judge_latency_ms_p95'])} ms |")
    L.append(f"| Reported input tokens (judge) | {t_run['input_tokens_total']} |")
    cost = money(t_run["cost_usd_per_1k_claims"])
    if t_run["cost_note"]:
        cost += f" ({t_run['cost_note']})"
    L.append(f"| Estimated cost per 1,000 claims | {cost} |")
    price = {"jev": cfg.pricing.get("jev"), "llm": cfg.llm_judge.pricing}.get(meta["judge"])
    if price:
        L.append(f"| Price used | ${price.usd_per_million_input_tokens}/M input, ${price.usd_per_million_output_tokens}/M output (checked {price.checked_on}) |")
    L.append("")

    L.append("## Dev split (used for tuning only)")
    L.append("")
    d_run, d_tun = a["dev_run"], a["dev_tuned"]
    L.append("| Metric | Config thresholds | Dev-tuned thresholds |")
    L.append("|---|---|---|")
    for (name, v1), (_, v2) in zip(_headline_rows(d_run), _headline_rows(d_tun or d_run)):
        L.append(f"| {name} | {v1} | {v2 if d_tun else 'n/a'} |")
    L.append("")
    if a["grid"]:
        L.append("Top 5 threshold pairs on dev:")
        L.append("")
        L.append("| pass_supports | fail_contradicts | wrong-pass | false alarm | review |")
        L.append("|---|---|---|---|---|")
        for g in a["grid"][:5]:
            L.append(f"| {g['pass_supports']:.2f} | {g['fail_contradicts']:.2f} | {num(g['wrong_pass_rate'], 3)} | {num(g['false_alarm_rate'], 3)} | {num(g['human_review_rate'], 3)} |")
        L.append("")

    L.append("## Per-claim results (test split)")
    L.append("")
    th_t = tuned or a["th_run"]
    from .evaluate import regate

    L.append("| claim_id | origin | label | quote status | P(sup) | P(con) | P(none) | verdict (config) | verdict (tuned) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for d in sorted(a["test"], key=lambda d: d.claim_id):
        p = d.probabilities or {}
        f = lambda k: f"{p[k]:.2f}" if k in p else "-"
        L.append(
            f"| {d.claim_id} | {d.origin} | {d.label} | {d.quote_status.value} | {f('supports')} | {f('contradicts')} | {f('says_nothing')} | "
            f"{regate(d, a['th_run']).value} | {regate(d, th_t).value if tuned else '-'} |"
        )
    L.append("")
    L.append("---")
    L.append(f"Generated by `citation-guard report` from `runs/{meta['run_id']}/decisions.jsonl`. Do not edit numbers by hand.")
    return "\n".join(L) + "\n"


def write_run_csv(a: dict, path: Path) -> None:
    meta = a["meta"]
    rows = []
    for split, kind, m in [
        ("test", "config", a["test_run"]), ("test", "dev_tuned", a["test_tuned"]),
        ("dev", "config", a["dev_run"]), ("dev", "dev_tuned", a["dev_tuned"]),
    ]:
        if not m:
            continue
        for k in ("n", "n_good", "n_bad", "wrong_pass", "wrong_pass_rate", "caught", "catch_rate", "false_alarm",
                  "false_alarm_rate", "human_review", "human_review_rate", "n_reached_check_b", "latency_ms_p50",
                  "latency_ms_p95", "judge_latency_ms_p50", "judge_latency_ms_p95", "input_tokens_total",
                  "cost_usd_per_1k_claims", "errors"):
            rows.append([meta["run_id"], meta["mode"], meta["judge"], split, kind, k, m[k]])
        rows.append([meta["run_id"], meta["mode"], meta["judge"], split, kind, "ece", m["calibration"]["ece"]])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run_id", "mode", "judge", "split", "thresholds", "metric", "value"])
        w.writerows(rows)


# --------------------------------------------------------------------------- summary


def render_summary(analyses: list[dict], run_reports: dict[str, Path]) -> str:
    today = date.today().isoformat()
    shas = {a["meta"]["claims_sha256"] for a in analyses}
    L = [f"# Citation Guard: judge comparison ({today})", ""]
    L.append(f"> {SMALL_SAMPLE}")
    L.append(">")
    draft = sum(a["label_sources"][DRAFT] for a in analyses[:1])
    reviewed = sum(a["label_sources"][REVIEWED] for a in analyses[:1])
    L.append(f"> Labels: {draft} `claude_draft`, {reviewed} `manoj_reviewed`. Any metric based on draft labels is provisional.")
    L.append(">")
    L.append("> Each row shows its own MODE. Only LIVE rows come from real model calls; MOCK rows are an offline heuristic and say nothing about Jev.")
    L.append("")
    if len(shas) > 1:
        L.append("WARNING: these runs used different claims files, so their test splits are not the same. Do not compare them directly.")
        L.append("")
    L.append("Test split, dev-tuned thresholds (string-match has none).")
    L.append("")
    L.append("| Judge | Mode | Model | Test n | Wrong-pass | Catch | False alarm | Human review | ECE | p50 / p95 ms | Cost / 1k claims | Report |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for a in analyses:
        m = a["test_tuned"] or a["test_run"]
        meta = a["meta"]
        rep = run_reports[meta["run_id"]]
        L.append(
            f"| `{meta['judge']}` | **{meta['mode']}** | {', '.join(meta['models_seen']) or '-'} | {m['n']} | "
            f"**{frac(m['wrong_pass'], m['n_bad'])}** | {frac(m['caught'], m['n_bad'])} | {frac(m['false_alarm'], m['n_good'])} | "
            f"{frac(m['human_review'], m['n'])} | {num(m['calibration']['ece'], 3)} | {num(m['latency_ms_p50'])} / {num(m['latency_ms_p95'])} | "
            f"{money(m['cost_usd_per_1k_claims'])} | [{rep.name}]({rep.name}) |"
        )
    L.append("")
    missing = {"jev", "llm", "stringmatch", "mock"} - {a["meta"]["judge"] for a in analyses}
    if missing:
        L.append(f"Not run: {', '.join(sorted(missing))}.")
        L.append("")
    L.append("---")
    L.append("Generated by `citation-guard report`. Numbers trace to each run's `decisions.jsonl`.")
    return "\n".join(L) + "\n"


def write_reports(cfg: Config, run_ids: list[str] | None = None) -> list[Path]:
    runs = select_runs(run_ids)
    if not runs:
        raise FileNotFoundError("no eval runs found under runs/; run `citation-guard eval --judge mock` first")
    out_dir = paths()["reports"]
    out_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    written: list[Path] = []
    analyses = []
    run_reports: dict[str, Path] = {}
    for meta in runs:
        a = analyse_run(meta, cfg)
        analyses.append(a)
        base = out_dir / f"eval_{today}_{meta['run_id']}"
        md, csv_path = base.with_suffix(".md"), base.with_suffix(".csv")
        md.write_text(render_run_md(a, cfg), encoding="utf-8", newline="\n")
        write_run_csv(a, csv_path)
        run_reports[meta["run_id"]] = md
        written += [md, csv_path]
    summary = render_summary(analyses, run_reports)
    s_path = out_dir / f"summary_{today}.md"
    s_path.write_text(summary, encoding="utf-8", newline="\n")
    (out_dir / "LATEST.md").write_text(summary, encoding="utf-8", newline="\n")
    written += [s_path, out_dir / "LATEST.md"]
    return written
