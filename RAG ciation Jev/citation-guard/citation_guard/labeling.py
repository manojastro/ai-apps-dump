"""Interactive terminal labelling (`citation-guard label`). Plain input(), works in PowerShell."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import load_config
from .evaluate import ALL_LABELS, REVIEWED, read_jsonl, write_jsonl_atomic
from .ingest import load_document
from .quote_match import match_quote, passage_window

KEYS = {"s": "supports", "c": "contradicts", "n": "says_nothing", "f": "fabricated"}


def _passage_view(rec: dict, window: int, min_chars: int) -> tuple[Text, str]:
    doc = load_document(rec.get("doc_id", "rfc7519"))
    m = match_quote(doc, rec["quote"], rec["section_id"], min_chars)
    if m.found:
        p = passage_window(doc, m.start, m.end, window)
        raw = doc.clean_text[p.start:p.end]
        t = Text(raw)
        t.stylize("bold yellow", m.start - p.start, m.end - p.start)
        return t, f"{m.status.value} (section {m.found_section_id})"
    sec = doc.section(rec["section_id"])
    body = sec.text[:1800] if sec else "(cited section does not exist)"
    return Text(body), f"{m.status.value} - closest fuzzy score {m.closest_fuzzy_score} (debug only)"


def run_labeling(path: Path, include_reviewed: bool = False, console: Console | None = None) -> None:
    console = console or Console()
    cfg = load_config()
    records = read_jsonl(path)
    if not records:
        console.print(f"[red]No claims in {path}. Run `citation-guard build-claims` first.[/]")
        return
    todo = [i for i, r in enumerate(records) if include_reviewed or r.get("label_source") != REVIEWED]
    console.print(f"{len(todo)} claims to review ({len(records)} total). Changes are saved after every answer.")
    for n, i in enumerate(todo, start=1):
        r = records[i]
        passage, status = _passage_view(r, 600, cfg.quote.min_chars)
        console.rule(f"[{n}/{len(todo)}] {r['claim_id']}  origin={r['origin']}  split={r.get('split')}  section={r['section_id']}")
        console.print(Panel(r["claim"], title="CLAIM", border_style="cyan"))
        console.print(Panel(r["quote"], title="QUOTE", border_style="magenta"))
        console.print(Panel(passage, title=f"SOURCE PASSAGE - {status}", border_style="white"))
        if r.get("note"):
            console.print(f"[dim]note: {r['note']}[/]")
        console.print(f"Current label: [bold]{r.get('label')}[/] ({r.get('label_source')})")
        prompt = "[Enter]=confirm  s=supports c=contradicts n=says_nothing f=fabricated  k=skip  q=quit > "
        while True:
            ans = console.input(prompt).strip().lower()
            if ans in ("", *KEYS, "k", "q"):
                break
            console.print("[red]Unknown key.[/]")
        if ans == "q":
            break
        if ans == "k":
            continue
        if ans == "" and r.get("label") not in ALL_LABELS:
            console.print("[yellow]No current label to confirm; choose s/c/n/f.[/]")
            continue
        if ans in KEYS:
            r["label"] = KEYS[ans]
        r["label_source"] = REVIEWED
        write_jsonl_atomic(path, records)
    left = sum(1 for r in records if r.get("label_source") != REVIEWED)
    console.print(f"Done. {left} claims not yet reviewed.")
