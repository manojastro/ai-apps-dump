"""`schemaguard` command line.  `uv run schemaguard --help`."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from schemaguard.config import REPO_ROOT, get_settings


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_demo_setup(args: argparse.Namespace) -> None:
    from schemaguard.lineage.builder import build_lineage
    from schemaguard.pipeline import run_pipeline
    from schemaguard.pipeline.generator import generate_all, write_jsonl
    from schemaguard.schemas.avro import load_pipeline_schemas
    from schemaguard.schemas.registry import make_registry, seed_registry

    s = get_settings()
    s.home.mkdir(parents=True, exist_ok=True)
    pipe = Path(s.pipeline_dir)
    events = generate_all(load_pipeline_schemas(pipe / "avro"), seed=42)
    write_jsonl(events, pipe / "data")
    print(f"generated {sum(len(v) for v in events.values())} synthetic events")
    reg = make_registry(s.registry_url, s.resolved_registry_dir)
    print("registered:", seed_registry(reg, pipe / "avro"))
    res = run_pipeline(pipe, s.home / "warehouse.duckdb")
    print(f"pipeline ok={res.ok}: {sum(t.passed for t in res.tests)}/{len(res.tests)} data tests passed")
    b = build_lineage(pipe)
    print(
        f"lineage: {b.graph.g.number_of_nodes()} nodes, {b.graph.g.number_of_edges()} edges, warnings={b.warnings}"
    )


def cmd_pipeline(args: argparse.Namespace) -> None:
    from schemaguard.pipeline import run_pipeline

    s = get_settings()
    res = run_pipeline(Path(s.pipeline_dir), s.home / "warehouse.duckdb")
    _print(res.to_dict())
    sys.exit(0 if res.ok else 1)


def cmd_lineage(args: argparse.Namespace) -> None:
    from schemaguard.lineage.builder import build_lineage

    lg = build_lineage(Path(get_settings().pipeline_dir)).graph
    if args.action == "build":
        from schemaguard.lineage.store import SqlLineageStore
        from schemaguard.store.db import open_database

        s = get_settings()
        v = SqlLineageStore(open_database(s.database_url, s.sqlite_path)).save(lg, source=str(s.pipeline_dir))
        print(
            f"lineage version {v}: {lg.g.number_of_nodes()} nodes, {lg.g.number_of_edges()} edges, hash {lg.content_hash()}"
        )
    elif args.action == "paths":
        print("\n".join(lg.impact_paths(args.node)))
    elif args.action == "downstream":
        _print([n.to_dict() for n in lg.downstream(args.node)])
    elif args.action == "upstream":
        _print([n.to_dict() for n in lg.upstream(args.node)])
    elif args.action == "summary":
        _print(lg.blast_radius_summary(args.node))


def _service() -> Any:
    from schemaguard.service import SchemaGuardService

    return SchemaGuardService()


def cmd_change(args: argparse.Namespace) -> None:
    from schemaguard.schemas.avro import load_pipeline_schemas
    from schemaguard.schemas.mutate import apply_mutations
    from schemaguard.schemas.registry import make_registry, subject_for_topic

    s = get_settings()
    current = load_pipeline_schemas(Path(s.pipeline_dir) / "avro")[args.topic].raw
    new = (
        json.loads(Path(args.schema).read_text(encoding="utf-8"))
        if args.schema
        else apply_mutations(current, json.loads(args.ops))
    )
    if args.register:
        reg = make_registry(s.registry_url, s.resolved_registry_dir)
        v = reg.register(subject_for_topic(args.topic), new)
        print(f"registered {subject_for_topic(args.topic)} version {v}; the worker will pick it up")
        return
    svc = _service()
    run_id, created = svc.submit_change(args.topic, new, source="cli")
    run = svc.get_run(run_id)
    print(f"run {run_id} ({'new' if created else 'existing'}): {run['status']}")


def cmd_runs(args: argparse.Namespace) -> None:
    svc = _service()
    if args.action == "list":
        for r in svc.list_runs():
            print(f"{r['run_id']}  {r['status']:<18} {r['topic']:<14} {r['change_class'] or ''}")
    elif args.action == "show":
        run = svc.get_run(args.run_id)
        print(
            run["state"].get("report")
            or json.dumps({k: run[k] for k in ("status", "next", "pending_approval")}, indent=2, default=str)
        )
    elif args.action in ("approve", "reject"):
        getattr(svc, args.action)(args.run_id, args.reviewer, args.comment)
        print(f"{args.action}d; status now {svc.get_run(args.run_id)['status']}")


def cmd_api(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run("schemaguard.api.app:app", host=args.host, port=args.port, log_level="info")


def cmd_ui(args: argparse.Namespace) -> None:
    ui = Path(__file__).parent / "ui" / "app.py"
    sys.exit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(ui),
                "--server.port",
                str(args.port),
                "--server.headless",
                "true",
                "--server.address",
                "localhost",
                "--browser.gatherUsageStats",
                "false",
            ],
            env=os.environ.copy(),
        )
    )


def cmd_worker(args: argparse.Namespace) -> None:
    from schemaguard.schemas.registry import make_registry
    from schemaguard.worker import RegistryPoller

    s = get_settings()
    poller = RegistryPoller(_service(), make_registry(s.registry_url, s.resolved_registry_dir))
    if args.once:
        print("runs:", poller.poll_once())
    else:
        poller.run_forever(s.worker_poll_s)


def cmd_export_mermaid(args: argparse.Namespace) -> None:
    from schemaguard.agent.graph import build_graph
    from schemaguard.agent.state import Deps
    from schemaguard.lineage.model import LineageGraph
    from schemaguard.llm.fake import FakeLLM

    s = get_settings()
    mermaid = (
        build_graph(Deps(s, FakeLLM(), LineageGraph(), None, Path(s.pipeline_dir)))
        .compile()
        .get_graph()
        .draw_mermaid()
    )
    doc = REPO_ROOT / "docs" / "ARCHITECTURE.md"
    text = doc.read_text(encoding="utf-8")
    start, end = "<!-- AGENT_GRAPH_START -->", "<!-- AGENT_GRAPH_END -->"
    block = f"{start}\n```mermaid\n{mermaid.strip()}\n```\n{end}"
    if start in text:
        text = text[: text.index(start)] + block + text[text.index(end) + len(end) :]
    else:
        text += "\n" + block + "\n"
    doc.write_text(text, encoding="utf-8")
    print(f"wrote compiled agent graph to {doc}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="schemaguard")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "demo-setup", help="generate data, seed registry, run pipeline, build lineage"
    ).set_defaults(fn=cmd_demo_setup)
    sub.add_parser("pipeline", help="run the demo pipeline + data tests").set_defaults(fn=cmd_pipeline)
    p = sub.add_parser("lineage")
    p.add_argument("action", choices=["build", "paths", "downstream", "upstream", "summary"])
    p.add_argument("node", nargs="?", default="field:orders.v1.amount")
    p.set_defaults(fn=cmd_lineage)
    p = sub.add_parser("change", help="submit a schema change")
    p.add_argument("--topic", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--ops", help='JSON list, e.g. [{"op":"rename_field","field":"amount","to":"total_amount"}]'
    )
    g.add_argument("--schema", help="path to a new .avsc")
    p.add_argument(
        "--register", action="store_true", help="register in the schema registry instead of submitting"
    )
    p.set_defaults(fn=cmd_change)
    p = sub.add_parser("runs")
    p.add_argument("action", choices=["list", "show", "approve", "reject"])
    p.add_argument("run_id", nargs="?")
    p.add_argument("--reviewer", default=os.environ.get("USERNAME") or os.environ.get("USER") or "cli")
    p.add_argument("--comment", default="")
    p.set_defaults(fn=cmd_runs)
    p = sub.add_parser("api")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(fn=cmd_api)
    p = sub.add_parser("ui")
    p.add_argument("--port", type=int, default=8501)
    p.set_defaults(fn=cmd_ui)
    p = sub.add_parser("worker", help="poll the schema registry for new versions")
    p.add_argument("--once", action="store_true")
    p.set_defaults(fn=cmd_worker)
    sub.add_parser(
        "export-mermaid", help="write the compiled agent graph into docs/ARCHITECTURE.md"
    ).set_defaults(fn=cmd_export_mermaid)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
