from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .dataset import generate_demo_cases, load_jsonl, write_jsonl
from .engine import EvaluationEngine, compare_runs
from .gate import apply_gate
from .models import GateConfig, RunReport
from .reporting import html_report, markdown_report
from .store import Database
from .targets import CallableTarget, DemoAgentTarget, HttpTarget


def read_report(path: str) -> RunReport:
    return RunReport.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def write_report(report: RunReport, path: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="evalharness")
    commands = root.add_subparsers(dest="command", required=True)
    dataset = commands.add_parser("dataset", help="dataset operations")
    dataset_commands = dataset.add_subparsers(dest="dataset_command", required=True)
    import_command = dataset_commands.add_parser("import")
    import_command.add_argument("path")
    import_command.add_argument("--id", default="imported")
    import_command.add_argument("--name", default="Imported Dataset")
    export_command = dataset_commands.add_parser("export-demo")
    export_command.add_argument("path", nargs="?", default="data/demo-200.jsonl")
    commands.add_parser("seed")
    run = commands.add_parser("run")
    run.add_argument("--mode", choices=["good", "bad"], default="good")
    run.add_argument("--http-url")
    run.add_argument("--python-callable")
    run.add_argument("--dataset-id", default="demo-200")
    run.add_argument("--limit", type=int)
    run.add_argument("--output", default="reports/latest.json")
    run.add_argument("--baseline", action="store_true")
    compare = commands.add_parser("compare")
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--baseline", required=True)
    report = commands.add_parser("report")
    report.add_argument("--run", required=True)
    report.add_argument("--output", default="reports/report.md")
    gate = commands.add_parser("gate")
    gate.add_argument("--candidate", required=True)
    gate.add_argument("--baseline")
    gate.add_argument("--config", default="config/gates.yml")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    database = Database()
    database.initialize()
    if args.command == "seed":
        result = database.seed_demo()
        write_jsonl(generate_demo_cases(), "data/demo-200.jsonl")
        print(json.dumps(result))
        return 0
    if args.command == "dataset":
        if args.dataset_command == "export-demo":
            write_jsonl(generate_demo_cases(), args.path)
            print(f"wrote 200 cases to {args.path}")
        else:
            cases = load_jsonl(args.path)
            database.save_dataset(cases, args.id, args.name)
            print(f"imported {len(cases)} cases into {args.id}")
        return 0
    if args.command == "run":
        database.seed_demo()
        cases = database.get_cases(args.dataset_id)
        if args.limit:
            cases = cases[: args.limit]
        if args.http_url:
            target = HttpTarget(args.http_url)
        elif args.python_callable:
            target = CallableTarget.from_path(args.python_callable)
        else:
            target = DemoAgentTarget(args.mode)
        report = EvaluationEngine().run(cases, target, dataset_id=args.dataset_id)
        database.save_run(report)
        if args.baseline:
            database.mark_baseline(report.project_id, report.id)
        write_report(report, args.output)
        print(json.dumps({"run_id": report.id, "output": args.output, "aggregate": report.aggregate}))
        return 0
    if args.command == "compare":
        print(json.dumps(compare_runs(read_report(args.candidate), read_report(args.baseline)), indent=2))
        return 0
    if args.command == "report":
        report = read_report(args.run)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        content = html_report(report) if output.suffix.lower() == ".html" else markdown_report(report)
        output.write_text(content, encoding="utf-8")
        print(output)
        return 0
    if args.command == "gate":
        candidate = read_report(args.candidate)
        baseline = read_report(args.baseline) if args.baseline else None
        config = GateConfig.from_dict(yaml.safe_load(Path(args.config).read_text(encoding="utf-8")))
        result = apply_gate(candidate, config, baseline)
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())

