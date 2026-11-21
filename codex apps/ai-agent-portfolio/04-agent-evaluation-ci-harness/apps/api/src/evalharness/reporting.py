from __future__ import annotations

import html

from .models import RunReport


def markdown_report(report: RunReport) -> str:
    failures = [sample for sample in report.samples if sample.metrics.get("task_success", 0) < 1]
    lines = [
        f"# Evaluation run `{report.id}`", "", f"Target: **{report.target}**  ",
        f"Dataset: **{report.dataset_id}**  ",
        f"Judge: **{report.judge_config['provider']} / {report.judge_config['model']}**", "",
        "## Aggregate metrics", "", "| Metric | Value |", "|---|---:|",
    ]
    lines.extend(f"| {key} | {value:.6f} |" for key, value in sorted(report.aggregate.items()))
    lines += ["", f"## Failed cases ({len(failures)})", ""]
    for sample in failures[:25]:
        lines.append(f"- `{sample.case.id}` — {sample.case.user_input}")
    return "\n".join(lines) + "\n"


def html_report(report: RunReport) -> str:
    body = markdown_report(report)
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Evaluation report</title>"
        "<style>body{font:16px system-ui;max-width:960px;margin:40px auto;padding:0 20px}"
        "pre{white-space:pre-wrap;background:#f4f4f5;padding:24px;border-radius:12px}</style>"
        f"</head><body><pre>{html.escape(body)}</pre></body></html>"
    )

