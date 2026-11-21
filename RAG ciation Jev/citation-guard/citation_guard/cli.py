"""citation-guard command line. Every command works in PowerShell."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config, paths

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Citation Guard: verify cited claims against their sources.")
console = Console()


def _fix_windows_loop() -> None:
    if sys.platform == "win32":
        # The selector loop avoids noisy Proactor shutdown errors with httpx on Windows.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@app.command()
def ingest() -> None:
    """Download (if missing), clean and section every document in the manifest."""
    from .ingest import ingest_all

    for doc in ingest_all():
        console.print(f"[green]{doc.doc_id}[/]: {len(doc.sections)} sections, {len(doc.clean_text):,} clean chars")


@app.command()
def models() -> None:
    """List Jev models visible to your TypeSafe account (needs TYPESAFE_API_KEY)."""
    from .judges.jev import list_models

    load_config()
    _fix_windows_loop()
    try:
        rows = asyncio.run(list_models())
    except Exception as e:
        console.print(f"[red]Could not list models:[/] {type(e).__name__}: {e}")
        raise typer.Exit(1)
    t = Table("name", "release_date", "description")
    for r in rows:
        t.add_row(r["name"], r["release_date"], r["description"])
    console.print(t)
    console.print(f"Pinned in config.yaml: [bold]{load_config().jev.model}[/] (aliases are not used)")


@app.command()
def generate(
    out: Path = typer.Option(None, help="Output JSONL (default data/eval/generated_answers.jsonl)"),
) -> None:
    """Run the generator LLM (system under test) on data/eval/questions.yaml."""
    from .generate import generate_all, load_questions
    from .ingest import load_document

    cfg = load_config()
    out = out or paths()["eval"] / "generated_answers.jsonl"
    qs = load_questions()
    doc = load_document(qs[0].get("doc_id", "rfc7519"))
    _fix_windows_loop()
    rows = asyncio.run(generate_all(cfg, doc, qs, out))
    n_claims = sum(len(r.get("claims", [])) for r in rows)
    errors = [r for r in rows if r.get("error")]
    console.print(f"Generator [bold]{cfg.generator.model}[/]: {len(rows)} answers, {n_claims} claims, {len(errors)} errors -> {out}")
    for r in errors:
        console.print(f"  [red]{r['question_id']}[/]: {r['error'][:200]}")


@app.command("build-claims")
def build_claims() -> None:
    """Merge generated + planted claims into data/eval/claims.jsonl (keeps reviewed labels)."""
    from .evaluate import build_claims_file

    path, stats = build_claims_file(load_config())
    console.print(f"Wrote {path}: {stats}")


@app.command()
def label(
    all_claims: bool = typer.Option(False, "--all", help="Also show claims already reviewed"),
    claims_file: Path = typer.Option(None, help="Claims JSONL (default data/eval/claims.jsonl)"),
) -> None:
    """Interactive labelling: confirm or change each label (sets label_source=manoj_reviewed)."""
    from .labeling import run_labeling

    run_labeling(claims_file or paths()["eval"] / "claims.jsonl", include_reviewed=all_claims, console=console)


@app.command()
def verify(
    answer_file: Path = typer.Argument(..., help='JSON file: {"doc_id", "answer", "claims": [...]}'),
    judge: str = typer.Option("mock", help="jev | llm | mock | stringmatch"),
) -> None:
    """Verify one cited answer and print per-claim verdicts."""
    from .ingest import load_document
    from .pipeline import ClaimIn, new_run_id, verify_answer

    cfg = load_config()
    data = json.loads(answer_file.read_text(encoding="utf-8"))
    doc = load_document(data.get("doc_id", "rfc7519"))
    claims = [ClaimIn.model_validate(c) for c in data["claims"]]
    run_dir = paths()["runs"] / new_run_id(f"verify-{judge}")
    _fix_windows_loop()
    res = asyncio.run(verify_answer(doc, claims, judge, cfg, run_dir=run_dir))
    t = Table("claim_id", "quote_status", "P(sup)", "P(con)", "P(none)", "verdict", title=f"{res.mode} run, judge={judge}")
    for d in res.claims:
        p = d.probabilities or {}
        f = lambda k: f"{p[k]:.2f}" if k in p else "-"
        t.add_row(d.claim_id, d.quote_status.value, f("supports"), f("contradicts"), f("says_nothing"), d.verdict.value)
    console.print(t)
    console.print(f"Answer result: [bold]{res.answer_result.value}[/]   log: {run_dir / 'decisions.jsonl'}")


@app.command("eval")
def eval_cmd(
    judge: str = typer.Option(..., help="jev | llm | mock | stringmatch"),
    claims_file: Path = typer.Option(None, help="Claims JSONL (default data/eval/claims.jsonl)"),
) -> None:
    """Run one judge over every claim (dev + test) and write runs/<run_id>/decisions.jsonl."""
    from .evaluate import run_eval

    cfg = load_config()
    _fix_windows_loop()
    try:
        run_dir = asyncio.run(run_eval(cfg, judge, claims_file or paths()["eval"] / "claims.jsonl"))
    except Exception as e:
        console.print(f"[red]Eval not run:[/] {type(e).__name__}: {e}")
        raise typer.Exit(1)
    console.print(f"Run written: {run_dir}")
    console.print("Next: citation-guard report")


@app.command()
def report(
    run: Optional[list[str]] = typer.Option(None, help="Run id(s). Default: latest eval run per judge."),
) -> None:
    """Write reports/eval_<date>_<run_id>.md/.csv per run plus a comparison summary."""
    from .report import write_reports

    cfg = load_config()
    written = write_reports(cfg, run or None)
    for p in written:
        console.print(f"[green]wrote[/] {p}")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the local API (no auth; binds to localhost by default)."""
    import uvicorn

    uvicorn.run("citation_guard.api:app", host=host, port=port)


if __name__ == "__main__":
    app()
