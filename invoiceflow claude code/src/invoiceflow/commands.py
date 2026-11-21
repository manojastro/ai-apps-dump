"""CLI command groups added after Phase 1: databricks, retrieval, agent, audit, approvals, eval.

Every command works the same in PowerShell and bash. Imports are local so `--help` stays
fast and optional backends are only loaded when used.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from invoiceflow.backends import DATA_DIR

EVAL_REPORT = Path("docs/EVAL_REPORT.md")
RETRIEVAL_REPORT = Path("docs/RETRIEVAL_REPORT.md")


def register(commands: Any) -> None:
    db = commands.add_parser("databricks", help="Unity Catalog setup and parity (live workspace)")
    dbc = db.add_subparsers(dest="db_command", required=True)
    setup = dbc.add_parser("setup", help="create UC tables, volume and governed functions")
    setup.add_argument("--data", type=Path, default=DATA_DIR)
    dbc.add_parser("parity", help="compare every record on Databricks with the local dataset")
    index = dbc.add_parser("index", help="write policy chunks and create the AI Search index")
    index.add_argument("--index-name", default=None)

    retrieval = commands.add_parser("retrieval", help="retrieval evaluation")
    retrieval_eval = retrieval.add_subparsers(dest="r_command", required=True).add_parser(
        "eval", help="recall@k, abstention and access checks on the question set"
    )
    retrieval_eval.add_argument("--backend", choices=["local", "databricks"], default="local")

    agent = commands.add_parser("agent", help="run and approve cases")
    ac = agent.add_subparsers(dest="agent_command", required=True)
    run = ac.add_parser("run", help="run the agent on one invoice")
    run.add_argument("invoice_id")
    run.add_argument("--case-id", default=None)
    approve = ac.add_parser("approve", help="record an approval or rejection (dev operator tool)")
    approve.add_argument("case_id")
    approve.add_argument("--approver-id", required=True)
    approve.add_argument(
        "--role",
        required=True,
        choices=["AP_CLERK", "AP_MANAGER", "FINANCE_CONTROLLER", "AUDITOR", "PLATFORM_ADMIN"],
    )
    approve.add_argument("--reject", action="store_true")
    approve.add_argument(
        "--callback-done",
        action="store_true",
        help="the approver verified bank details by call-back",
    )
    approve.add_argument("--comment", default="")
    status = ac.add_parser("status", help="show a case")
    status.add_argument("case_id")
    for p in (run, approve, status):
        p.add_argument("--state-dir", type=Path, default=None)

    audit = commands.add_parser("audit", help="audit trail")
    verify = audit.add_subparsers(dest="audit_command", required=True).add_parser(
        "verify", help="verify the hash chain"
    )
    verify.add_argument("--db", type=Path, default=None)

    approvals = commands.add_parser("approvals", help="approval service helpers")
    approvals.add_subparsers(dest="ap_command", required=True).add_parser(
        "dev-tokens", help="create or show local dev tokens (v1 auth)"
    )

    ev = commands.add_parser("eval", help="agent evaluation and CI gate")
    evc = ev.add_subparsers(dest="eval_command", required=True)
    agent_eval = evc.add_parser("agent", help="evaluate the agent and write docs/EVAL_REPORT.md")
    agent_eval.add_argument("--split", choices=["dev", "eval"], default="dev")
    agent_eval.add_argument(
        "--held-out-ok", action="store_true", help="required to run on the held-out eval split"
    )
    agent_eval.add_argument(
        "--provider",
        choices=["stub", "databricks", "azure_openai"],
        default=None,
        help="default: LLM_PROVIDER from settings",
    )
    agent_eval.add_argument("--limit", type=int, default=None)
    agent_eval.add_argument(
        "--scenario",
        action="append",
        default=None,
        help="only these scenarios (repeatable); 'adversarial' = all adv_*",
    )
    agent_eval.add_argument("--report", type=Path, default=EVAL_REPORT)
    agent_eval.add_argument("--evidence", type=Path, default=None)
    agent_eval.add_argument(
        "--record", type=Path, default=None, help="record live model responses for CI replay"
    )
    gate = evc.add_parser("gate", help="deterministic CI gate against evals/gate_reference.json")
    gate.add_argument("--update-reference", action="store_true")


def dispatch(args: argparse.Namespace, command: str) -> int:
    handlers = {
        "databricks": _databricks,
        "retrieval": _retrieval,
        "agent": _agent,
        "audit": _audit,
        "approvals": _approvals,
        "eval": _eval,
    }
    return handlers[args.command](args, command)


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str, ensure_ascii=False))


# --- databricks ------------------------------------------------------------------------


def _databricks(args: argparse.Namespace, command: str) -> int:
    from invoiceflow.adapters.databricks.setup import Target, setup_unity_catalog
    from invoiceflow.adapters.databricks.sql import StatementRunner
    from invoiceflow.backends import DOCS_DIR, workspace_client
    from invoiceflow.config import Settings
    from invoiceflow.data.dataset import read_dataset

    settings = Settings()
    client = workspace_client(settings)
    runner = StatementRunner(settings.require("databricks_warehouse_id"), client)
    target = Target(
        settings.invoiceflow_catalog,
        settings.invoiceflow_schema,
        settings.invoiceflow_eval_schema,
        settings.invoiceflow_volume,
    )
    if args.db_command == "setup":
        counts = setup_unity_catalog(runner, client, read_dataset(args.data), target)
        _print({"target": target.volume_path, "rows": counts})
        return 0
    if args.db_command == "parity":
        import time

        from invoiceflow.adapters.databricks.reader import (
            DatabricksReader,
            Snapshot,
            snapshot_labels,
        )
        from invoiceflow.adapters.local.memory import MemoryReader

        started = time.perf_counter()
        dataset = read_dataset(DATA_DIR)
        # 1. Every record, read in bulk (one query per table), compared field by field.
        snap = Snapshot(runner, target.catalog, target.schema)
        local_sorted = {
            "vendors": tuple(sorted(dataset.vendors, key=lambda v: v.vendor_id)),
            "purchase_orders": tuple(sorted(dataset.purchase_orders, key=lambda p: p.po_id)),
            "goods_receipts": tuple(sorted(dataset.goods_receipts, key=lambda g: g.grn_id)),
            "invoices": tuple(sorted(dataset.invoices, key=lambda i: i.ledger_key)),
        }
        report: dict[str, Any] = {}
        mismatches: list[str] = []
        for name, local in local_sorted.items():
            remote = getattr(snap, name)
            bad = [str(a)[:60] for a, b in zip(local, remote, strict=False) if a != b]
            if len(local) != len(remote):
                bad.append(f"count {len(local)} local vs {len(remote)} databricks")
            report[name] = {"records": len(remote), "mismatches": len(bad)}
            mismatches += [f"{name}: {b}" for b in bad]
        labels = snapshot_labels(runner, target.catalog, target.eval_schema)
        local_labels = tuple(sorted(dataset.ground_truth, key=lambda g: g.invoice_id))
        label_bad = sum(1 for a, b in zip(local_labels, labels, strict=False) if a != b)
        label_bad += abs(len(local_labels) - len(labels))
        report["ground_truth"] = {"records": len(labels), "mismatches": label_bad}
        if label_bad:
            mismatches.append(f"ground_truth: {label_bad} mismatches")
        # 2. The per-record reader (the online path) on a sample, incl. prior-invoice queries.
        db, mem = DatabricksReader(runner, target.catalog, target.schema), MemoryReader(dataset)
        sample = dataset.invoices[::33]
        for inv in sample:
            if db.get_invoice(inv.invoice_id) != inv or db.prior_invoices(
                inv
            ) != mem.prior_invoices(inv):
                mismatches.append(f"per-record reader: {inv.invoice_id}")
        report["per_record_sample"] = {"invoices": len(sample)}
        report["mismatches"] = mismatches
        report["elapsed_s"] = round(time.perf_counter() - started, 1)
        _print(report)
        return 1 if mismatches else 0
    from invoiceflow.adapters.databricks.retrieval import (
        create_index,
        ensure_endpoint,
        write_chunk_table,
    )
    from invoiceflow.retrieval.chunking import load_chunks

    table = write_chunk_table(
        runner, client, load_chunks(DOCS_DIR), target.catalog, target.schema, target.volume
    )
    name = (
        args.index_name
        or settings.ai_search_index
        or f"{target.catalog}.{target.schema}.policy_index"
    )
    endpoint = settings.require("ai_search_endpoint")
    ensure_endpoint(client, endpoint)
    action = create_index(client, endpoint, name, table, settings.require("embedding_endpoint"))
    _print({"chunk_table": table, "endpoint": endpoint, "index": name, "index_action": action})
    return 0


# --- retrieval ---------------------------------------------------------------------------


def _retrieval_report(backend: str = "local") -> dict[str, Any]:
    from invoiceflow.agent.wiring import build_retriever
    from invoiceflow.config import Settings
    from invoiceflow.evals.retrieval_eval import load_questions, run_retrieval_eval

    settings = (
        Settings(_env_file=None)
        if backend == "local"
        else Settings().model_copy(update={"invoiceflow_backend": "databricks"})
    )
    report = run_retrieval_eval(build_retriever(settings), load_questions())
    return report.model_dump(mode="json")


def _retrieval(args: argparse.Namespace, command: str) -> int:
    from invoiceflow.config import Settings
    from invoiceflow.evals.report import _git

    report = _retrieval_report(args.backend)
    path = (
        RETRIEVAL_REPORT if args.backend == "local" else Path("docs/RETRIEVAL_REPORT_AISEARCH.md")
    )
    if args.backend == "local":
        title = "local hybrid retriever"
        note = (
            "The local retriever uses a hashing embedder, not a semantic model; AI Search "
            "is reported in RETRIEVAL_REPORT_AISEARCH.md."
        )
    else:
        settings = Settings()
        title = "Databricks AI Search"
        note = (
            f"Index `{settings.ai_search_index}` on endpoint `{settings.ai_search_endpoint}`, "
            f"embeddings `{settings.embedding_endpoint}`, hybrid queries with role and vendor "
            "filters. No similarity threshold, so off-topic questions are not abstained."
        )
    lines = [
        f"# Retrieval report ({title})",
        "",
        f"> Generated by `{command}`. Commit `{_git('rev-parse', '--short', 'HEAD')}`. "
        f"Synthetic documents. {note}",
        "",
        "| Metric | Result |",
        "|---|---|",
        f"| Questions | {report['questions']} ({report['answerable']} answerable) |",
        f"| Recall@1 / @3 / @5 | {report['recall_at']['1']} / {report['recall_at']['3']} / "
        f"{report['recall_at']['5']} |",
        f"| Off-topic questions abstained | {report['abstention_correct']} / "
        f"{report['abstention_cases']} |",
        f"| Access-control violations | {report['access_violations']} |",
        "",
        "| Question | Expected | Retrieved (top 3) | Hit@5 |",
        "|---|---|---|---|",
    ]
    for r in report["results"]:
        lines.append(
            f"| {r['id']} | {', '.join(r['expected']) or '(abstain)'} | "
            f"{', '.join(r['retrieved'][:3]) or '(abstained)'} | "
            f"{'yes' if r['hit_at']['5'] else ('n/a' if not r['expected'] else 'no')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    _print(
        {
            k: report[k]
            for k in ("recall_at", "abstention_correct", "abstention_cases", "access_violations")
        }
    )
    print(f"wrote {path}")
    return 0


# --- agent -----------------------------------------------------------------------------


def _runner(state_dir: Path | None) -> Any:
    from invoiceflow.agent.wiring import build_runner
    from invoiceflow.config import Settings

    return build_runner(Settings(), state_dir)


def _agent(args: argparse.Namespace, command: str) -> int:
    runner = _runner(args.state_dir)
    if args.agent_command == "run":
        outcome = runner.start(args.invoice_id, args.case_id)
    elif args.agent_command == "approve":
        identity = {"id": args.approver_id, "kind": "human", "role": args.role}
        resume: dict[str, Any] = {
            "decision": "reject" if args.reject else "approve",
            "approver": identity,
            "comment": args.comment,
        }
        if args.callback_done:
            resume["verification"] = {"kind": "BANK_DETAILS_CALLBACK", "performed_by": identity}
        outcome = runner.resume(args.case_id, resume)
    else:
        state = runner.state(args.case_id)
        _print(
            {
                "case_id": args.case_id,
                "status": state.get("status"),
                "fail_reason": state.get("fail_reason"),
                "proposal": state.get("proposal"),
            }
        )
        return 0
    _print(
        {
            "case_id": outcome.case_id,
            "status": outcome.status,
            "fail_reason": outcome.fail_reason,
            "interrupt": outcome.interrupt,
            "proposal": outcome.state.get("proposal"),
        }
    )
    return 0


def _audit(args: argparse.Namespace, command: str) -> int:
    from invoiceflow.audit.chain import verify_audit_chain
    from invoiceflow.config import Settings

    path = args.db or Path(Settings().invoiceflow_state_dir) / "audit.db"
    check = verify_audit_chain(path)
    _print(check.model_dump())
    return 0 if check.ok else 1


def _approvals(args: argparse.Namespace, command: str) -> int:
    from invoiceflow.config import Settings
    from invoiceflow.services.approvals.auth import DevTokenAuth

    path = Path(Settings().invoiceflow_state_dir) / "dev_tokens.json"
    DevTokenAuth.load_or_create(path)
    print(f"dev tokens (local only, git-ignored): {path}")
    for token, identity in json.loads(path.read_text(encoding="utf-8")).items():
        print(f"  {identity['role']:<20} {identity['id']:<12} {token}")
    return 0


# --- eval --------------------------------------------------------------------------------


def _eval(args: argparse.Namespace, command: str) -> int:
    import tempfile

    from invoiceflow.adapters.llm import build_chat_model
    from invoiceflow.adapters.llm.replay import RecordingChatModel
    from invoiceflow.adapters.local.memory import MemoryReader
    from invoiceflow.agent.wiring import build_runner
    from invoiceflow.config import Settings
    from invoiceflow.data.dataset import read_dataset
    from invoiceflow.data.models import Split
    from invoiceflow.evals.agent_eval import executed_without_allow, run_agent_eval, summarize_agent
    from invoiceflow.evals.agent_report import EvalMeta, write_eval
    from invoiceflow.evals.baseline import run_baseline
    from invoiceflow.evals.report import run_meta
    from invoiceflow.evals.scoring import summarize
    from invoiceflow.policy.matrix import load_matrix

    gate_mode = args.eval_command == "gate"
    split = Split.DEV if gate_mode else Split(args.split)
    if split is Split.EVAL and not args.held_out_ok:
        print("error: pass --held-out-ok to evaluate on the held-out split", file=sys.stderr)
        return 2
    settings = Settings() if not gate_mode else Settings(_env_file=None, llm_provider="stub")
    if not gate_mode and args.provider:
        settings = settings.model_copy(update={"llm_provider": args.provider})
    dataset = read_dataset(DATA_DIR)
    labels = list(dataset.labels(split))
    if not gate_mode and args.scenario:
        wanted = set(args.scenario)
        labels = [
            lbl
            for lbl in labels
            if lbl.scenario in wanted or ("adversarial" in wanted and lbl.adversarial_kind)
        ]
    if not gate_mode and args.limit:
        labels = labels[: args.limit]
    llm = build_chat_model(settings)
    if not gate_mode and args.record:
        llm = RecordingChatModel(llm, args.record)
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    # SQLite stores keep their files open until garbage collection; on Windows that blocks
    # deleting the directory, so cleanup errors are ignored (the OS temp dir is cleared later).
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        runner = build_runner(settings, Path(tmp), dataset, llm)
        runner.deps.kill_switch = lambda: False
        cases = run_agent_eval(runner, labels)
        violations = executed_without_allow(runner, [c.case_id for c in cases])
        runner.deps.audit.close()
    agent = summarize_agent(
        cases,
        violations,
        settings.llm_cost_per_1k_input_tokens,
        settings.llm_cost_per_1k_output_tokens,
    )
    matrix = load_matrix()

    if gate_mode:
        from invoiceflow.evals.gate import (
            REFERENCE_PATH,
            check_gate,
            load_reference,
            reference_from,
            save_reference,
        )

        if args.update_reference:
            save_reference(reference_from(agent))
            print(f"updated {REFERENCE_PATH}")
            return 0
        result = check_gate(agent, load_reference())
        for check in result.checks:
            print(
                f"{'PASS' if check.ok else 'FAIL'}  {check.name}: {check.value} ({check.threshold})"
            )
        print("gate:", "PASSED" if result.passed else "FAILED")
        return 0 if result.passed else 1

    baseline_cases = (
        run_baseline(MemoryReader(dataset), labels, matrix, Split.DEV)
        if split is Split.DEV
        else run_baseline_any(dataset, labels, matrix)
    )
    meta = EvalMeta(
        run=run_meta(command, settings.invoiceflow_backend, split.value, dataset, matrix),
        model=llm.name,
        provider=settings.llm_provider,
        retrieval=_retrieval_report(),
    )
    evidence = args.evidence or Path("docs/evidence/eval") / (
        f"agent-{split.value}-{settings.llm_provider}-{meta.run.run_at[:10]}.json"
    )
    write_eval(meta, agent, summarize(baseline_cases), cases, args.report, evidence)
    print(
        f"agent on {agent.cases} {split.value} invoices ({llm.name}): exception "
        f"{agent.exception.pct}%, action {agent.action.pct}%, approver {agent.approver.pct}%, "
        f"unsafe {agent.unsafe}, executed violations {agent.executed_violations}"
    )
    print(f"wrote {args.report} and {evidence}")
    return 0


def run_baseline_any(dataset: Any, labels: list[Any], matrix: Any) -> Any:
    """Baseline on the held-out split, used only by the Phase 5 eval comparison."""
    from invoiceflow.adapters.local.memory import MemoryReader
    from invoiceflow.data.models import Split
    from invoiceflow.evals.baseline import run_baseline

    relabelled = [label.model_copy(update={"split": Split.DEV}) for label in labels]
    return run_baseline(MemoryReader(dataset), relabelled, matrix, Split.DEV)
