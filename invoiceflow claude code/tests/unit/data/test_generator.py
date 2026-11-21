"""Invariants of the synthetic dataset. These check the generator, not the matcher."""

from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal as D

import pytest

from invoiceflow.core.gstin import validate_gstin
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.generator import generate
from invoiceflow.data.generator.build import ADVERSARIAL, DERIVED, ESCALATION_FROM, MAIN
from invoiceflow.data.generator.wordlists import FAKE_BANK_CODES
from invoiceflow.data.models import ExceptionCode, GroundTruth, Invoice, Split

ALL_SCENARIOS = (*MAIN, *DERIVED, *ADVERSARIAL)


def labels_by_id(ds: Dataset) -> dict[str, GroundTruth]:
    return {label.invoice_id: label for label in ds.ground_truth}


def test_same_seed_gives_identical_dataset(dataset: Dataset) -> None:
    again = generate(dataset.seed)
    assert again.version == dataset.version
    assert again == dataset


def test_other_seeds_also_build_and_differ(dataset: Dataset) -> None:
    other = generate(7)
    assert other.version != dataset.version
    assert len(other.invoices) == len(dataset.invoices)


def test_table_sizes(dataset: Dataset) -> None:
    assert len(dataset.vendors) == 30
    assert len(dataset.purchase_orders) == 200
    assert len(dataset.invoices) == len(dataset.ground_truth) == 325
    assert len(dataset.contracts) == 6


def test_every_scenario_has_its_planned_count(dataset: Dataset) -> None:
    counts = Counter(label.scenario for label in dataset.ground_truth)
    assert counts == {s.name: s.count for s in ALL_SCENARIOS}


def test_main_set_matches_the_planned_exception_mix(dataset: Dataset) -> None:
    main = Counter(
        label.expected_exception for label in dataset.ground_truth if not label.adversarial_kind
    )
    assert main == {
        ExceptionCode.CLEAN: 105,
        ExceptionCode.PRICE_VARIANCE: 30,
        ExceptionCode.QTY_OVERBILLED: 30,
        ExceptionCode.MISSING_GRN: 30,
        ExceptionCode.DUPLICATE_INVOICE: 30,
        ExceptionCode.GST_MISMATCH: 30,
        ExceptionCode.PO_CLOSED: 20,
        ExceptionCode.VENDOR_BANK_CHANGE: 25,
    }
    assert sum(1 for label in dataset.ground_truth if label.adversarial_kind) == 25


def test_split_is_stratified_60_40(dataset: Dataset) -> None:
    strata: dict[tuple[ExceptionCode, bool], Counter[Split]] = defaultdict(Counter)
    for label in dataset.ground_truth:
        strata[(label.expected_exception, bool(label.adversarial_kind))][label.split] += 1
    for key, counts in strata.items():
        total = counts[Split.DEV] + counts[Split.EVAL]
        assert abs(counts[Split.DEV] - round(total * 0.6)) <= 1, key


def test_references_are_consistent(dataset: Dataset) -> None:
    pos = {po.po_id: po for po in dataset.purchase_orders}
    vendor_ids = {v.vendor_id for v in dataset.vendors}
    for invoice in dataset.invoices:
        po = pos[invoice.po_id]
        assert invoice.vendor_id == po.vendor_id
        assert invoice.vendor_id in vendor_ids
        assert invoice.place_of_supply == po.place_of_supply
        for line in invoice.lines:
            assert po.line(line.po_line_no) is not None
        assert invoice.gross_total == sum(
            (line.taxable_value + line.tax_total for line in invoice.lines), D("0")
        )
    for grn in dataset.goods_receipts:
        po = pos[grn.po_id]
        assert all(po.line(line.po_line_no) for line in grn.lines)


def test_ids_are_unique_and_follow_ledger_order(dataset: Dataset) -> None:
    ids = [inv.invoice_id for inv in dataset.invoices]
    assert len(set(ids)) == len(ids)
    assert [inv.invoice_id for inv in sorted(dataset.invoices, key=lambda i: i.ledger_key)] == ids


def test_answers_cannot_leak_through_invoice_fields() -> None:
    leaked = {"expected_exception", "expected_action", "scenario", "split", "rationale"}
    assert leaked.isdisjoint(Invoice.model_fields)


def test_po_lines_are_billed_once_except_by_duplicates(dataset: Dataset) -> None:
    labels = labels_by_id(dataset)
    billed: Counter[tuple[str, int]] = Counter()
    for invoice in dataset.invoices:
        if labels[invoice.invoice_id].expected_exception is ExceptionCode.DUPLICATE_INVOICE:
            continue
        for line in invoice.lines:
            billed[(invoice.po_id, line.po_line_no)] += 1
    assert max(billed.values()) == 1


def test_no_accidental_duplicate_pairs(dataset: Dataset) -> None:
    """Outside the duplicate scenarios, no two invoices of a vendor share a gross amount
    within 7 days, and no invoice numbers repeat. Checked independently of core."""
    labels = labels_by_id(dataset)
    clean_side = [
        inv
        for inv in dataset.invoices
        if labels[inv.invoice_id].expected_exception is not ExceptionCode.DUPLICATE_INVOICE
    ]
    numbers = Counter((inv.vendor_id, inv.invoice_number) for inv in clean_side)
    assert max(numbers.values()) == 1
    for a in clean_side:
        for b in clean_side:
            if a.invoice_id < b.invoice_id and a.vendor_id == b.vendor_id:
                close = abs((a.invoice_date - b.invoice_date).days) <= 7
                assert not (close and a.gross_total == b.gross_total), (a.invoice_id, b.invoice_id)


def test_gstins_are_valid_except_where_intended(dataset: Dataset) -> None:
    invalid_vendors = [v for v in dataset.vendors if not validate_gstin(v.gstin).valid]
    assert len(invalid_vendors) == 2
    labels = labels_by_id(dataset)
    for invoice in dataset.invoices:
        intended = labels[invoice.invoice_id].scenario in {
            "gst_bad_check_character",
            "gst_vendor_master_invalid",
        }
        assert validate_gstin(invoice.supplier_gstin).valid is not intended


def test_bank_codes_are_fictional(dataset: Dataset) -> None:
    for invoice in dataset.invoices:
        assert invoice.bank.ifsc[:4] in FAKE_BANK_CODES
    for vendor in dataset.vendors:
        assert vendor.bank.ifsc[:4] in FAKE_BANK_CODES


def test_value_boundary_invoices_hit_the_limits_exactly(dataset: Dataset) -> None:
    labels = labels_by_id(dataset)
    grosses = sorted(
        inv.gross_total
        for inv in dataset.invoices
        if labels[inv.invoice_id].scenario == "clean_value_boundary"
    )
    assert grosses == [D("100000.00"), D("100000.01"), D("1000000.00"), D("1000000.01")]


@pytest.mark.parametrize(
    ("scenario", "after_clause"),
    [
        ("price_escalation_within", True),
        ("price_escalation_exceeded", True),
        ("price_escalation_not_yet", False),
    ],
)
def test_escalation_invoices_are_dated_relative_to_the_clause(
    dataset: Dataset, scenario: str, after_clause: bool
) -> None:
    labels = labels_by_id(dataset)
    escalating = {c.vendor_id for c in dataset.contracts if c.escalation_max_pct is not None}
    selected = [inv for inv in dataset.invoices if labels[inv.invoice_id].scenario == scenario]
    assert selected
    for invoice in selected:
        assert invoice.vendor_id in escalating
        assert (invoice.invoice_date >= ESCALATION_FROM) is after_clause


def test_adversarial_text_is_present(dataset: Dataset) -> None:
    labels = labels_by_id(dataset)
    for invoice in dataset.invoices:
        kind = labels[invoice.invoice_id].adversarial_kind
        if kind in {"prompt_injection", "hidden_bank_change"}:
            text = " ".join(
                [invoice.notes, invoice.remarks, *(line.description for line in invoice.lines)]
            )
            assert len(text) > 40, invoice.invoice_id


def test_renumbered_duplicates_fall_inside_the_window(dataset: Dataset) -> None:
    labels = labels_by_id(dataset)
    by_vendor: dict[str, list[Invoice]] = defaultdict(list)
    for invoice in dataset.invoices:
        by_vendor[invoice.vendor_id].append(invoice)
    for invoice in dataset.invoices:
        if labels[invoice.invoice_id].scenario != "duplicate_renumbered":
            continue
        earlier = [
            other
            for other in by_vendor[invoice.vendor_id]
            if other.ledger_key < invoice.ledger_key and other.gross_total == invoice.gross_total
        ]
        assert any(
            abs(other.invoice_date - invoice.invoice_date) <= timedelta(days=7) for other in earlier
        )
