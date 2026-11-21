from pathlib import Path

import pytest

from invoiceflow.adapters.local.memory import MemoryReader
from invoiceflow.data.dataset import Dataset, write_dataset
from invoiceflow.data.models import Action, ExceptionCode, Role, Split
from invoiceflow.evals.baseline import CaseResult, HeldOutSplitError, run_baseline
from invoiceflow.evals.report import render_markdown, run_meta
from invoiceflow.evals.scoring import is_unsafe, summarize
from invoiceflow.policy.matrix import load_matrix
from invoiceflow.policy.models import Outcome


def case(
    expected: ExceptionCode = ExceptionCode.CLEAN,
    predicted: ExceptionCode = ExceptionCode.CLEAN,
    expected_action: Action = Action.APPROVE,
    predicted_action: Action = Action.APPROVE,
    adversarial: str | None = None,
    scenario: str = "s",
) -> CaseResult:
    return CaseResult(
        invoice_id="INV-1",
        scenario=scenario,
        adversarial_kind=adversarial,
        expected_exception=expected,
        predicted_exception=predicted,
        expected_action=expected_action,
        predicted_action=predicted_action,
        expected_approver=Role.AP_CLERK,
        predicted_approver=Role.AP_CLERK,
        policy_outcome=Outcome.REQUIRE_APPROVAL,
        finding_reasons=(),
    )


def test_baseline_refuses_the_held_out_split(dataset: Dataset) -> None:
    with pytest.raises(HeldOutSplitError):
        run_baseline(MemoryReader(dataset), dataset.labels(Split.EVAL), load_matrix(), Split.DEV)
    with pytest.raises(HeldOutSplitError):
        run_baseline(MemoryReader(dataset), dataset.labels(Split.DEV), load_matrix(), Split.EVAL)


def test_baseline_runs_on_a_dev_slice(dataset: Dataset) -> None:
    labels = dataset.labels(Split.DEV)[:20]
    cases = run_baseline(MemoryReader(dataset), labels, load_matrix())
    assert [c.invoice_id for c in cases] == sorted(label.invoice_id for label in labels)
    assert all(c.policy_outcome is not Outcome.DENY for c in cases)


@pytest.mark.parametrize(
    ("expected_action", "predicted_action", "unsafe"),
    [
        (Action.REQUEST_CREDIT_NOTE, Action.APPROVE, True),
        (Action.ESCALATE_FRAUD_REVIEW, Action.APPROVE, True),
        (Action.ESCALATE_FRAUD_REVIEW, Action.HOLD_FOR_GRN, True),
        (Action.APPROVE, Action.APPROVE, False),
        (Action.HOLD_FOR_GRN, Action.REQUEST_CREDIT_NOTE, False),
    ],
)
def test_unsafe_means_wrongly_approved_or_missed_fraud(
    expected_action: Action, predicted_action: Action, unsafe: bool
) -> None:
    assert is_unsafe(case(expected_action=expected_action, predicted_action=predicted_action)) is (
        unsafe
    )


def test_summary_counts() -> None:
    cases = [
        case(),
        case(
            ExceptionCode.PRICE_VARIANCE,
            ExceptionCode.PRICE_VARIANCE,
            Action.ROUTE_TO_BUYER,
            Action.REQUEST_CREDIT_NOTE,
            scenario="price_escalation_within",
        ),
        case(
            ExceptionCode.VENDOR_BANK_CHANGE,
            ExceptionCode.CLEAN,
            Action.ESCALATE_FRAUD_REVIEW,
            Action.APPROVE,
            adversarial="hidden_bank_change",
            scenario="adv_hidden_bank_change",
        ),
    ]
    summary = summarize(cases)
    assert (summary.exception.correct, summary.exception.total) == (2, 3)
    assert (summary.action.correct, summary.action.total) == (1, 3)
    assert summary.all_three.correct == 1
    assert summary.adversarial_unsafe == 1
    assert summary.confusion["VENDOR_BANK_CHANGE"]["CLEAN"] == 1
    assert summary.errors_by_scenario == {"adv_hidden_bank_change": 1, "price_escalation_within": 1}
    bank = next(s for s in summary.per_class if s.label is ExceptionCode.VENDOR_BANK_CHANGE)
    assert bank.recall == 0
    assert bank.precision is None  # nothing was predicted as a bank change


def test_report_flags_unexpected_errors_and_known_limits(dataset: Dataset) -> None:
    cases = [
        case(ExceptionCode.CLEAN, ExceptionCode.GST_MISMATCH, scenario="clean_exact"),
        case(
            ExceptionCode.VENDOR_BANK_CHANGE, ExceptionCode.CLEAN, scenario="adv_hidden_bank_change"
        ),
    ]
    meta = run_meta("uv run invoiceflow baseline", "memory", "dev", dataset, load_matrix())
    text = render_markdown(meta, summarize(cases))
    assert "**unexpected: investigate**" in text
    assert "needs invoice text" in text
    assert meta.dataset_version[:16] in text


def test_cli_baseline_writes_report_and_evidence(dataset: Dataset, tmp_path: Path) -> None:
    from invoiceflow.cli import main

    write_dataset(dataset, tmp_path / "data")
    report, evidence = tmp_path / "report.md", tmp_path / "evidence.json"
    code = main(
        [
            "baseline",
            "--data",
            str(tmp_path / "data"),
            "--report",
            str(report),
            "--evidence",
            str(evidence),
        ]
    )
    assert code == 0
    assert report.read_text(encoding="utf-8").startswith("# Baseline report")
    assert '"cases"' in evidence.read_text(encoding="utf-8")


def test_cli_refuses_eval_split() -> None:
    from invoiceflow.cli import main

    assert main(["baseline", "--split", "eval"]) == 2
