"""Command-line entry point: `uv run invoiceflow ...`.

A single Python CLI keeps every project command identical in PowerShell and bash.
Subcommands are added phase by phase.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from invoiceflow import __version__

DATA_DIR = Path("data/generated")
CONTRACTS_DIR = Path("data/docs/contracts")
SAMPLES_DIR = Path("data/samples")
REPORT_PATH = Path("docs/BASELINE_REPORT.md")
EVIDENCE_DIR = Path("docs/evidence/phase-1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="invoiceflow",
        description="InvoiceFlow: AP exception-resolution agent (synthetic data only).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")

    data = commands.add_parser("data", help="generate and load the synthetic dataset")
    data_commands = data.add_subparsers(dest="data_command", required=True)
    generate = data_commands.add_parser("generate", help="write the seeded dataset to disk")
    generate.add_argument("--seed", type=int, default=None, help="default: the project seed")
    generate.add_argument("--out", type=Path, default=DATA_DIR)
    generate.add_argument("--contracts", type=Path, default=CONTRACTS_DIR)
    generate.add_argument("--samples", type=Path, default=SAMPLES_DIR)
    load = data_commands.add_parser("load", help="load the dataset into local Postgres")
    load.add_argument("--data", type=Path, default=DATA_DIR)

    baseline = commands.add_parser("baseline", help="run the rule-only baseline and report")
    baseline.add_argument(
        "--split",
        default="dev",
        help="dev only; the held-out eval split is locked until Phase 5",
    )
    baseline.add_argument("--data", type=Path, default=DATA_DIR)
    baseline.add_argument("--backend", choices=("memory", "postgres"), default="memory")
    baseline.add_argument("--report", type=Path, default=REPORT_PATH)
    baseline.add_argument("--evidence", type=Path, default=None)

    from invoiceflow.commands import register

    register(commands)
    return parser


def _generate(args: argparse.Namespace) -> int:
    from invoiceflow.data.export import export_dataset
    from invoiceflow.data.generator import DEFAULT_SEED, generate

    dataset = generate(DEFAULT_SEED if args.seed is None else args.seed)
    manifest = export_dataset(dataset, args.out, args.contracts, args.samples)
    rows = ", ".join(f"{name} {info['rows']}" for name, info in manifest["files"].items())
    print(f"dataset {manifest['dataset_version'][:16]} (seed {dataset.seed}): {rows}")
    print(f"wrote {args.out}, {args.contracts}, {args.samples}")
    return 0


def _load(args: argparse.Namespace) -> int:
    import psycopg

    from invoiceflow.config import Settings
    from invoiceflow.data.dataset import read_dataset
    from invoiceflow.data.loader import load_dataset

    dataset = read_dataset(args.data)
    with psycopg.connect(Settings().postgres_conninfo()) as conn:
        counts = load_dataset(conn, dataset)
    tables = ", ".join(f"{table} {n}" for table, n in counts.items())
    print(f"loaded dataset {dataset.version[:16]}: {tables}")
    return 0


def _baseline(args: argparse.Namespace, command: str) -> int:
    from invoiceflow.adapters.local.memory import MemoryReader
    from invoiceflow.data.dataset import read_dataset
    from invoiceflow.data.models import Split
    from invoiceflow.evals.baseline import run_baseline
    from invoiceflow.evals.report import run_meta, write_report
    from invoiceflow.evals.scoring import summarize
    from invoiceflow.policy.matrix import load_matrix

    if args.split != "dev":
        print("error: the held-out eval split is locked until Phase 5", file=sys.stderr)
        return 2
    dataset = read_dataset(args.data)
    matrix = load_matrix()
    labels = dataset.labels(Split.DEV)
    if args.backend == "postgres":
        import psycopg

        from invoiceflow.adapters.local.postgres import PostgresReader
        from invoiceflow.config import Settings
        from invoiceflow.data.loader import loaded_version

        with psycopg.connect(Settings().postgres_conninfo()) as conn:
            if loaded_version(conn) != dataset.version:
                print(
                    "error: Postgres holds a different dataset; run `invoiceflow data load`",
                    file=sys.stderr,
                )
                return 2
            cases = run_baseline(PostgresReader(conn), labels, matrix)
    else:
        cases = run_baseline(MemoryReader(dataset), labels, matrix)

    summary = summarize(cases)
    meta = run_meta(command, args.backend, "dev", dataset, matrix)
    today = datetime.now(UTC).astimezone().date().isoformat()
    evidence = args.evidence or EVIDENCE_DIR / f"baseline-dev-{args.backend}-{today}.json"
    write_report(meta, summary, cases, args.report, evidence)
    print(
        f"baseline on {summary.cases} dev invoices ({args.backend}): "
        f"exception {summary.exception.pct}%, action {summary.action.pct}%, "
        f"approver {summary.approver.pct}%, policy denials {summary.policy_denials}"
    )
    print(f"wrote {args.report} and {evidence}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.command == "data" and args.data_command == "generate":
        return _generate(args)
    if args.command == "data" and args.data_command == "load":
        return _load(args)
    if args.command == "baseline":
        return _baseline(args, " ".join(["uv run invoiceflow", *arguments]))
    if args.command:
        from invoiceflow.commands import dispatch

        return dispatch(args, " ".join(["uv run invoiceflow", *arguments]))
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
