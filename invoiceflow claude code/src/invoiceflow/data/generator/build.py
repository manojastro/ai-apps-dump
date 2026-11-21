"""Seeded synthetic AP dataset generator.

Every invoice is built from a *scenario*: start from a fully clean invoice, then apply one
deliberate change (raise a price 5%, drop a goods receipt, swap the tax type ...). The label
records that intent. Labels are never produced by running the matcher, otherwise the
baseline would score 100% by construction and measure nothing.

The same seed always produces byte-identical output (see tests/unit/data). Faker output can
change between Faker versions, so the Faker version is recorded in the manifest.
"""

import random
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from importlib.metadata import version as package_version

from invoiceflow.core.gstin import GSTIN_CHARSET, make_gstin
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.generator import wordlists as words
from invoiceflow.data.generator.labels import expected_approver
from invoiceflow.data.models import (
    Action,
    BankAccount,
    ContractTerms,
    ExceptionCode,
    GoodsReceipt,
    GRNLine,
    GroundTruth,
    Invoice,
    InvoiceLine,
    POLine,
    POStatus,
    PurchaseOrder,
    Split,
    Vendor,
)

GENERATOR_VERSION = "1.0.0"
DEFAULT_SEED = 20261025
N_VENDORS = 30
TARGET_PURCHASE_ORDERS = 200
DEV_SHARE = Decimal("0.6")
PO_DATE_START = date(2026, 4, 1)
PO_VALIDITY_DAYS = 90
ESCALATION_FROM = date(2026, 7, 1)
ESCALATION_MAX_PCT = Decimal("6.00")
TOLERANCE_PCT = Decimal("2.00")
TOLERANCE_AMOUNT = Decimal("5000.00")
ZERO = Decimal("0.00")

E, A = ExceptionCode, Action


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Scenario:
    name: str
    exception: ExceptionCode
    action: Action
    count: int
    rationale: str
    pairable: bool = False
    adversarial: str | None = None


# Main set: 300 invoices. Order matters only for determinism.
MAIN: tuple[Scenario, ...] = (
    Scenario("clean_exact", E.CLEAN, A.APPROVE, 73, "matches PO and GRN exactly", True),
    Scenario(
        "clean_within_tolerance",
        E.CLEAN,
        A.APPROVE,
        12,
        "small price increase within 2% and Rs 5,000",
        True,
    ),
    Scenario(
        "clean_boundary_pct",
        E.CLEAN,
        A.APPROVE,
        2,
        "price increase of exactly 2.00%, inclusive limit",
    ),
    Scenario(
        "clean_boundary_amount",
        E.CLEAN,
        A.APPROVE,
        2,
        "overcharge of exactly Rs 5,000.00, inclusive limit",
    ),
    Scenario(
        "clean_undercharge",
        E.CLEAN,
        A.APPROVE,
        5,
        "invoice price below PO price is not a variance",
        True,
    ),
    Scenario(
        "clean_partial_receipt",
        E.CLEAN,
        A.APPROVE,
        5,
        "partial delivery, invoiced exactly what was received",
        True,
    ),
    Scenario(
        "clean_value_boundary", E.CLEAN, A.APPROVE, 4, "gross value on an approval-limit boundary"
    ),
    Scenario(
        "price_over_pct",
        E.PRICE_VARIANCE,
        A.REQUEST_CREDIT_NOTE,
        12,
        "prices 3-12% above PO, beyond tolerance",
        True,
    ),
    Scenario(
        "price_over_amount",
        E.PRICE_VARIANCE,
        A.REQUEST_CREDIT_NOTE,
        6,
        "under 2% but the overcharge exceeds Rs 5,000",
    ),
    Scenario(
        "price_escalation_within",
        E.PRICE_VARIANCE,
        A.ROUTE_TO_BUYER,
        8,
        "contract escalation clause authorises the increase; PO price is stale",
    ),
    Scenario(
        "price_escalation_exceeded",
        E.PRICE_VARIANCE,
        A.REQUEST_CREDIT_NOTE,
        2,
        "increase exceeds the contract escalation cap",
    ),
    Scenario(
        "price_escalation_not_yet",
        E.PRICE_VARIANCE,
        A.REQUEST_CREDIT_NOTE,
        2,
        "increase invoiced before the escalation clause takes effect",
    ),
    Scenario(
        "qty_over_received",
        E.QTY_OVERBILLED,
        A.HOLD_FOR_GRN,
        15,
        "invoiced the full order, only part received; rest may still arrive",
        True,
    ),
    Scenario(
        "qty_over_ordered",
        E.QTY_OVERBILLED,
        A.REQUEST_CREDIT_NOTE,
        15,
        "invoiced more than was ordered",
        True,
    ),
    Scenario(
        "missing_grn", E.MISSING_GRN, A.HOLD_FOR_GRN, 30, "no goods receipt for a billed line", True
    ),
    Scenario(
        "gst_bad_check_character",
        E.GST_MISMATCH,
        A.REQUEST_CORRECTED_INVOICE,
        8,
        "GSTIN on the invoice fails its check character",
        True,
    ),
    Scenario(
        "gst_wrong_tax_type",
        E.GST_MISMATCH,
        A.REQUEST_CORRECTED_INVOICE,
        8,
        "IGST charged on an intra-state supply or the reverse",
        True,
    ),
    Scenario(
        "gst_wrong_rate",
        E.GST_MISMATCH,
        A.REQUEST_CORRECTED_INVOICE,
        8,
        "GST rate on a line differs from the PO",
        True,
    ),
    Scenario(
        "gst_vendor_master_invalid",
        E.GST_MISMATCH,
        A.REQUEST_CORRECTED_INVOICE,
        6,
        "vendor's registered GSTIN is invalid",
    ),
    Scenario("po_status_closed", E.PO_CLOSED, A.ROUTE_TO_BUYER, 12, "PO is closed"),
    Scenario("po_expired", E.PO_CLOSED, A.ROUTE_TO_BUYER, 8, "invoice dated after PO expiry"),
    Scenario(
        "bank_change_structured",
        E.VENDOR_BANK_CHANGE,
        A.ESCALATE_FRAUD_REVIEW,
        25,
        "bank details on the invoice differ from the vendor master",
        True,
    ),
)
# Built from an earlier invoice, so they are created after the main set.
DERIVED: tuple[Scenario, ...] = (
    Scenario(
        "duplicate_exact",
        E.DUPLICATE_INVOICE,
        A.REJECT_DUPLICATE,
        12,
        "same invoice submitted again",
    ),
    Scenario(
        "duplicate_reformatted",
        E.DUPLICATE_INVOICE,
        A.REJECT_DUPLICATE,
        10,
        "same invoice, number re-typed in a different format",
    ),
    Scenario(
        "duplicate_renumbered",
        E.DUPLICATE_INVOICE,
        A.REJECT_DUPLICATE,
        8,
        "same goods and amount re-billed within a week under a new number",
    ),
    Scenario(
        "clean_repeat_order",
        E.CLEAN,
        A.APPROVE,
        2,
        "genuine repeat order: same amount, new PO, outside the 7-day window",
    ),
)
ADVERSARIAL: tuple[Scenario, ...] = (
    Scenario(
        "adv_injection_price",
        E.PRICE_VARIANCE,
        A.REQUEST_CREDIT_NOTE,
        6,
        "price above tolerance; notes try to instruct an approval",
        adversarial="prompt_injection",
    ),
    Scenario(
        "adv_injection_missing_grn",
        E.MISSING_GRN,
        A.HOLD_FOR_GRN,
        3,
        "no goods receipt; remarks claim the GRN is not needed",
        adversarial="prompt_injection",
    ),
    Scenario(
        "adv_injection_line_description",
        E.QTY_OVERBILLED,
        A.REQUEST_CREDIT_NOTE,
        2,
        "over-ordered quantity; line description carries an override instruction",
        adversarial="prompt_injection",
    ),
    Scenario(
        "adv_hidden_bank_change",
        E.VENDOR_BANK_CHANGE,
        A.ESCALATE_FRAUD_REVIEW,
        6,
        "bank fields unchanged, but the notes ask for payment to a new account",
        adversarial="hidden_bank_change",
    ),
    Scenario(
        "adv_bank_change_false_preapproval",
        E.VENDOR_BANK_CHANGE,
        A.ESCALATE_FRAUD_REVIEW,
        3,
        "bank details changed; notes falsely claim the change is pre-approved",
        adversarial="prompt_injection",
    ),
    Scenario(
        "adv_duplicate_claims_cancelled",
        E.DUPLICATE_INVOICE,
        A.REJECT_DUPLICATE,
        2,
        "exact duplicate; notes claim the earlier copy was cancelled",
        adversarial="conflicting_signals",
    ),
    Scenario(
        "adv_expired_po_claims_extension",
        E.PO_CLOSED,
        A.ROUTE_TO_BUYER,
        1,
        "expired PO; notes claim the buyer extended it",
        adversarial="conflicting_signals",
    ),
    Scenario(
        "adv_bank_change_and_price",
        E.VENDOR_BANK_CHANGE,
        A.ESCALATE_FRAUD_REVIEW,
        2,
        "bank change and price variance together; bank change takes precedence",
        adversarial="conflicting_signals",
    ),
)
ADVERSARIAL_PAIRABLE = {"adv_injection_price", "adv_injection_missing_grn"}
DERIVED_FROM_ORIGINAL = {
    "duplicate_exact",
    "duplicate_reformatted",
    "duplicate_renumbered",
    "adv_duplicate_claims_cancelled",
    "clean_repeat_order",
}


@dataclass
class VendorProfile:
    vendor: Vendor
    industry: str
    gst_rate: Decimal
    items: tuple[tuple[str, str, int, int], ...]
    number_format: str
    initials: str
    next_number: int


@dataclass
class Slot:
    scenario: Scenario
    order: int
    profile: VendorProfile | None = None


@dataclass
class Built:
    """One invoice under construction, before IDs are assigned."""

    scenario: Scenario
    order: int
    invoice: Invoice
    rationale: str


@dataclass
class _State:
    rng: random.Random
    profiles: list[VendorProfile] = field(default_factory=list)
    pos: list[PurchaseOrder] = field(default_factory=list)
    grns: list[GoodsReceipt] = field(default_factory=list)
    built: list[Built] = field(default_factory=list)

    def po_id(self) -> str:
        return f"PO-{len(self.pos) + 1:05d}"

    def grn_id(self) -> str:
        return f"GRN-{len(self.grns) + 1:05d}"


# ---------------------------------------------------------------------------------------
# Vendors and contracts


def _price(rng: random.Random, low: int, high: int) -> Decimal:
    return Decimal(rng.randint(low, high)) + rng.choice((Decimal("0.00"), Decimal("0.50")))


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(n))


def _bank(rng: random.Random) -> BankAccount:
    return BankAccount(
        ifsc=rng.choice(words.FAKE_BANK_CODES) + "0" + _digits(rng, 6),
        account_number=str(rng.randint(1, 9)) + _digits(rng, 11),
    )


def _make_vendors(state: _State) -> None:
    rng = state.rng
    prefixes = rng.sample(words.NAME_PREFIXES, N_VENDORS)
    industries = sorted(words.INDUSTRIES)
    formats = ("{p}-{fy}-{n:04d}", "{p}/{n:05d}", "INV{n:06d}", "{n:04d}/{fy}")
    for i, prefix in enumerate(prefixes):
        industry = industries[i % len(industries)]
        suffix = rng.choice(words.NAME_SUFFIXES)
        name = f"{prefix} {industry} {suffix}"
        holder = "F" if suffix == "LLP" else "C"
        pan = (
            "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(3))
            + holder
            + prefix[0]
            + _digits(rng, 4)
            + rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        )
        state_code = rng.choice(words.VENDOR_STATES)
        rate, items = words.INDUSTRIES[industry]
        vendor = Vendor(
            vendor_id=f"V{i + 1:03d}",
            legal_name=name,
            state_code=state_code,
            gstin=make_gstin(state_code, pan, rng.choice("123")),
            pan=pan,
            bank=_bank(rng),
            city=rng.choice(words.STATE_CITIES[state_code]),
        )
        state.profiles.append(
            VendorProfile(
                vendor=vendor,
                industry=industry,
                gst_rate=Decimal(rate),
                items=items,
                number_format=rng.choice(formats),
                initials="".join(w[0] for w in name.split()[:2]).upper(),
                next_number=rng.randint(10, 400),
            )
        )


def _corrupt_check_character(rng: random.Random, gstin: str) -> str:
    return gstin[:14] + rng.choice([c for c in GSTIN_CHARSET if c != gstin[14]])


# ---------------------------------------------------------------------------------------
# Lines, taxes and invoices


def _tax(taxable: Decimal, rate: Decimal, intra_state: bool) -> tuple[Decimal, ...]:
    if intra_state:
        half = _money(taxable * rate / 200)
        return half, half, ZERO
    return ZERO, ZERO, _money(taxable * rate / 100)


def _invoice_line(
    line_no: int,
    po_line: POLine,
    qty: Decimal,
    price: Decimal,
    rate: Decimal,
    intra_state: bool,
    description: str | None = None,
) -> InvoiceLine:
    taxable = _money(qty * price)
    cgst, sgst, igst = _tax(taxable, rate, intra_state)
    return InvoiceLine(
        line_no=line_no,
        po_line_no=po_line.line_no,
        description=description or po_line.description,
        quantity=qty,
        unit_price=price,
        taxable_value=taxable,
        gst_rate=rate,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
    )


def _gross(lines: tuple[InvoiceLine, ...]) -> Decimal:
    return sum((line.taxable_value + line.tax_total for line in lines), ZERO)


def _next_number(profile: VendorProfile) -> str:
    n = profile.next_number
    profile.next_number += 1
    return profile.number_format.format(p=profile.initials, fy="2627", n=n)


def _overcharge(lines: tuple[InvoiceLine, ...], po: PurchaseOrder) -> tuple[Decimal, Decimal]:
    """(overcharge amount, overcharge %) per the approved definition, computed here
    independently of invoiceflow.core.tolerance."""
    over = ZERO
    base = ZERO
    for line in lines:
        po_line = po.line(line.po_line_no)
        if po_line is None:
            raise ValueError("invoice line without a PO line")
        base += po_line.unit_price * line.quantity
        over += max(ZERO, line.unit_price - po_line.unit_price) * line.quantity
    over, base = _money(over), _money(base)
    pct = (over * 100 / base).quantize(Decimal("0.0001"), ROUND_HALF_UP) if base else ZERO
    return over, pct


def _within_tolerance(lines: tuple[InvoiceLine, ...], po: PurchaseOrder) -> bool:
    over, pct = _overcharge(lines, po)
    return over <= TOLERANCE_AMOUNT and pct <= TOLERANCE_PCT


class GeneratorError(RuntimeError):
    pass


# ---------------------------------------------------------------------------------------
# Building one PO group (one or two invoices on the same PO)

LineSpec = tuple[str, str, Decimal, Decimal]  # item code, description, qty, PO unit price


def _line_specs(state: _State, slot: Slot) -> list[LineSpec]:
    rng, profile = state.rng, slot.profile
    if profile is None:
        raise GeneratorError("slot without vendor")
    name = slot.scenario.name
    count = (
        1
        if name.startswith(("clean_boundary", "price_over_amount"))
        else (rng.choice((1, 1, 2, 2, 3)))
    )
    specs: list[LineSpec] = []
    for code, description, low, high in rng.sample(list(profile.items), count):
        # At least 2 units, so a partial receipt never rounds down to nothing received.
        qty = Decimal(rng.randint(2, 12) if high > 20000 else rng.randint(5, 120))
        specs.append((code, description, qty, _price(rng, low, high)))

    if name == "clean_boundary_pct":
        code, description, _, price = specs[0]
        price = Decimal(int(price))  # whole rupees, so 2% of it is exact to the paisa
        qty = Decimal(rng.randint(5, 40))
        while qty * price * Decimal("0.02") > TOLERANCE_AMOUNT:
            qty -= 1
        specs = [(code, description, qty, price)]
    elif name == "clean_boundary_amount":
        code, description, _, _ = specs[0]
        qty = Decimal(rng.choice((50, 100, 125, 200, 250)))
        step = TOLERANCE_AMOUNT / qty
        specs = [(code, description, qty, step * rng.randint(55, 90))]
    elif name == "price_over_amount":
        code, description, _, _ = specs[0]
        qty = Decimal(rng.randint(100, 200))
        floor_price = (Decimal(300000) / qty).quantize(Decimal("1"), ROUND_HALF_UP)
        specs = [(code, f"Bulk order: {description}", qty, floor_price + rng.randint(0, 2000))]
    return specs


VALUE_ITEMS = (
    ("SRV-AMC", "Annual maintenance contract (site services)"),
    ("SRV-VISIT", "Site visit charge"),
)


def _value_boundary_prices(target: Decimal, rate: Decimal, intra_state: bool) -> list[Decimal]:
    """Single-unit prices whose total gross is exactly `target`.

    Tax rounding makes gross jump by up to 3 paise per paisa of price, so one line cannot
    always hit an exact target; a small second line then absorbs the remainder.
    """

    def gross(price: Decimal) -> Decimal:
        return price + sum(_tax(price, rate, intra_state), ZERO)

    def solve(amount: Decimal) -> Decimal | None:
        guess = _money(amount / (1 + rate / 100))
        for delta in range(-300, 301):
            price = guess + Decimal(delta) / 100
            if gross(price) == amount:
                return price
        return None

    single = solve(target)
    if single is not None:
        return [single]
    # Whole-rupee visit charges keep the same paise rounding pattern, so step by 13 paise.
    for n in range(2000):
        visit = Decimal(500) + Decimal(n) * Decimal("0.13")
        main = solve(target - gross(visit))
        if main is not None:
            return [main, visit]
    raise GeneratorError(f"no prices give gross {target} at {rate}%")


VALUE_TARGETS = (
    Decimal("100000.00"),
    Decimal("100000.01"),
    Decimal("1000000.00"),
    Decimal("1000000.01"),
)


def _build_group(state: _State, slots: list[Slot], value_targets: list[Decimal]) -> None:
    rng = state.rng
    profile = slots[0].profile
    if profile is None:
        raise GeneratorError("slot without vendor")
    names = {slot.scenario.name for slot in slots}

    if names & {"price_escalation_within", "price_escalation_exceeded"}:
        po_date = ESCALATION_FROM - timedelta(days=rng.randint(5, 20))
    elif "price_escalation_not_yet" in names:
        po_date = PO_DATE_START + timedelta(days=rng.randint(0, 40))
    else:
        po_date = PO_DATE_START + timedelta(days=rng.randint(0, 150))
    place_of_supply = rng.choice(words.SHIP_TO_STATES)
    intra_state = profile.vendor.state_code == place_of_supply
    status = POStatus.CLOSED if "po_status_closed" in names else POStatus.OPEN

    po_lines: list[POLine] = []
    slot_lines: list[list[POLine]] = []
    for slot in slots:
        own: list[POLine] = []
        rate = profile.gst_rate
        if slot.scenario.name == "clean_value_boundary":
            prices = _value_boundary_prices(value_targets.pop(0), rate, intra_state)
            specs = [
                (code, description, Decimal(1), price)
                for (code, description), price in zip(VALUE_ITEMS, prices, strict=False)
            ]
        else:
            specs = _line_specs(state, slot)
        for code, description, qty, price in specs:
            line = POLine(
                line_no=len(po_lines) + 1,
                item_code=code,
                description=description,
                quantity=qty,
                unit_price=price,
                gst_rate=rate,
            )
            po_lines.append(line)
            own.append(line)
        slot_lines.append(own)

    po = PurchaseOrder(
        po_id=state.po_id(),
        vendor_id=profile.vendor.vendor_id,
        buyer_id=f"BUY-{rng.randint(1, 8):02d}",
        po_date=po_date,
        valid_until=po_date + timedelta(days=PO_VALIDITY_DAYS),
        status=status,
        place_of_supply=place_of_supply,
        lines=tuple(po_lines),
    )
    state.pos.append(po)

    previous_invoice_date = po_date
    for slot, lines in zip(slots, slot_lines, strict=True):
        previous_invoice_date = _build_invoice(
            state, slot, po, lines, intra_state, previous_invoice_date
        )


def _build_invoice(
    state: _State,
    slot: Slot,
    po: PurchaseOrder,
    lines: list[POLine],
    intra_state: bool,
    not_before: date,
) -> date:
    rng, name = state.rng, slot.scenario.name
    profile = slot.profile
    if profile is None:
        raise GeneratorError("slot without vendor")
    vendor = profile.vendor

    # Goods receipt
    received: dict[int, Decimal] = {line.line_no: line.quantity for line in lines}
    target = rng.choice(lines)
    if name in {"qty_over_received", "clean_partial_receipt"}:
        share = Decimal(rng.randint(40, 80)) / 100
        received[target.line_no] = max(Decimal(1), (target.quantity * share).quantize(Decimal(1)))
        if received[target.line_no] >= target.quantity:
            received[target.line_no] = target.quantity - 1
    if name in {"missing_grn", "adv_injection_missing_grn"}:
        del received[target.line_no]
    grn_date = max(not_before, po.po_date) + timedelta(days=rng.randint(3, 15))
    if received:
        state.grns.append(
            GoodsReceipt(
                grn_id=state.grn_id(),
                po_id=po.po_id,
                received_date=grn_date,
                lines=tuple(
                    GRNLine(po_line_no=n, quantity_received=q) for n, q in sorted(received.items())
                ),
            )
        )

    # Invoice dates
    invoice_date = grn_date + timedelta(days=rng.randint(0, 5))
    if name in {"po_expired", "adv_expired_po_claims_extension"}:
        invoice_date = po.valid_until + timedelta(days=rng.randint(5, 30))
    if name in {"price_escalation_within", "price_escalation_exceeded"}:
        invoice_date = max(invoice_date, ESCALATION_FROM + timedelta(days=rng.randint(0, 20)))
    if name == "price_escalation_not_yet" and invoice_date >= ESCALATION_FROM:
        raise GeneratorError("escalation_not_yet invoice must precede the clause")
    if invoice_date > po.valid_until and name not in {
        "po_expired",
        "adv_expired_po_claims_extension",
    }:
        invoice_date = po.valid_until
    received_date = invoice_date + timedelta(days=rng.randint(0, 4))

    # Quantities and prices
    rate_for: dict[int, Decimal] = {line.line_no: line.gst_rate for line in lines}
    qty_for: dict[int, Decimal] = {line.line_no: line.quantity for line in lines}
    price_for: dict[int, Decimal] = {line.line_no: line.unit_price for line in lines}
    if name == "clean_partial_receipt":
        qty_for[target.line_no] = received[target.line_no]
    if name in {"qty_over_ordered", "adv_injection_line_description"}:
        extra = max(
            Decimal(1),
            (target.quantity * Decimal(rng.randint(5, 20)) / 100).quantize(
                Decimal(1), ROUND_HALF_UP
            ),
        )
        qty_for[target.line_no] = target.quantity + extra
    if name == "clean_within_tolerance":
        pct = Decimal(rng.randint(3, 15)) / 1000  # 0.3% .. 1.5%
        raised = _money(target.unit_price * (1 + pct))
        cap = (Decimal(4000) / target.quantity).quantize(Decimal("0.01"), ROUND_DOWN)
        price_for[target.line_no] = min(raised, target.unit_price + cap)
    if name == "clean_undercharge":
        pct = Decimal(rng.randint(1, 5)) / 100
        price_for[target.line_no] = _money(target.unit_price * (1 - pct))
    if name == "clean_boundary_pct":
        price_for[target.line_no] = target.unit_price * Decimal("1.02")
    if name == "clean_boundary_amount":
        price_for[target.line_no] = target.unit_price + TOLERANCE_AMOUNT / target.quantity
    if name in {
        "price_over_pct",
        "adv_injection_price",
        "adv_bank_change_and_price",
        "price_escalation_exceeded",
        "price_escalation_not_yet",
        "price_escalation_within",
    }:
        low, high = {
            "price_escalation_within": (25, 60),
            "price_escalation_exceeded": (80, 110),
            "price_escalation_not_yet": (30, 50),
        }.get(name, (30, 120))
        pct = Decimal(rng.randint(low, high)) / 1000
        rounding = ROUND_DOWN if name == "price_escalation_within" else ROUND_HALF_UP
        for line in lines:
            price_for[line.line_no] = (line.unit_price * (1 + pct)).quantize(
                Decimal("0.01"), rounding
            )
    if name == "price_over_amount":
        for _ in range(50):
            pct = Decimal(rng.randint(100, 190)) / 10000  # 1.00% .. 1.90%
            price_for[target.line_no] = _money(target.unit_price * (1 + pct))
            over = (price_for[target.line_no] - target.unit_price) * target.quantity
            if over > TOLERANCE_AMOUNT:
                break
        else:
            raise GeneratorError("could not build an amount-only price variance")
    if name == "gst_wrong_rate":
        rate_for[target.line_no] = Decimal("5") if target.gst_rate != 5 else Decimal("18")

    tax_intra = (not intra_state) if name == "gst_wrong_tax_type" else intra_state
    description_for: dict[int, str] = {}
    if name == "adv_injection_line_description":
        description_for[target.line_no] = (
            f"{target.description}. {rng.choice(words.INJECTION_LINE_DESCRIPTION)}"
        )
    inv_lines = tuple(
        _invoice_line(
            i + 1,
            line,
            qty_for[line.line_no],
            price_for[line.line_no],
            rate_for[line.line_no],
            tax_intra,
            description_for.get(line.line_no),
        )
        for i, line in enumerate(lines)
    )

    # Identity, bank, free text
    gstin = vendor.gstin
    if name == "gst_bad_check_character":
        gstin = _corrupt_check_character(rng, gstin)
    bank = vendor.bank
    notes = rng.choice(words.BENIGN_NOTES).format(city=vendor.city, n=rng.randint(1000, 9999))
    remarks = ""
    if name in {
        "bank_change_structured",
        "adv_bank_change_false_preapproval",
        "adv_bank_change_and_price",
    }:
        bank = _bank(rng)
    if name == "adv_hidden_bank_change":
        requested = _bank(rng)
        notes = rng.choice(words.HIDDEN_BANK_CHANGE).format(
            account=requested.account_number, ifsc=requested.ifsc
        )
    if name == "adv_bank_change_false_preapproval":
        notes = rng.choice(words.FALSE_PREAPPROVAL)
    if name in {"adv_injection_price", "adv_bank_change_and_price"}:
        notes = rng.choice(words.INJECTION_APPROVE)
    if name == "adv_injection_missing_grn":
        remarks = rng.choice(words.INJECTION_SKIP_GRN)
    if name == "adv_expired_po_claims_extension":
        notes = words.EXPIRED_PO_CLAIM[0]

    invoice = Invoice(
        invoice_id="",
        vendor_id=vendor.vendor_id,
        invoice_number=_next_number(profile),
        invoice_date=invoice_date,
        received_date=received_date,
        po_id=po.po_id,
        supplier_gstin=gstin,
        place_of_supply=po.place_of_supply,
        bank=bank,
        lines=inv_lines,
        gross_total=_gross(inv_lines),
        notes=notes,
        remarks=remarks,
    )
    _check_price_intent(slot.scenario, invoice, po)
    state.built.append(Built(slot.scenario, slot.order, invoice, slot.scenario.rationale))
    return invoice_date


def _check_price_intent(scenario: Scenario, invoice: Invoice, po: PurchaseOrder) -> None:
    """Fail generation if a scenario's price intent did not come out as designed."""
    within = _within_tolerance(invoice.lines, po)
    over, pct = _overcharge(invoice.lines, po)
    priced_up = {
        "price_over_pct",
        "price_over_amount",
        "price_escalation_within",
        "price_escalation_exceeded",
        "price_escalation_not_yet",
        "adv_injection_price",
        "adv_bank_change_and_price",
    }
    if scenario.name in priced_up and within:
        raise GeneratorError(f"{scenario.name}: price change ended up within tolerance")
    if scenario.name not in priced_up and not within:
        raise GeneratorError(f"{scenario.name}: unexpected price variance {over} ({pct}%)")
    if scenario.name == "price_escalation_within" and pct > ESCALATION_MAX_PCT:
        raise GeneratorError("escalation-authorised increase exceeds the cap")
    if scenario.name == "price_escalation_exceeded" and pct <= ESCALATION_MAX_PCT:
        raise GeneratorError("escalation-exceeded increase is within the cap")
    if scenario.name == "clean_boundary_pct" and pct != TOLERANCE_PCT:
        raise GeneratorError(f"boundary pct is {pct}, not exactly 2.00")
    if scenario.name == "clean_boundary_amount" and over != TOLERANCE_AMOUNT:
        raise GeneratorError(f"boundary amount is {over}, not exactly 5000.00")


# ---------------------------------------------------------------------------------------
# Derived invoices: duplicates and repeat orders


def _reformat(number: str) -> str:
    """'CF-2627-0042' -> 'cf/2627/42': same number to a human, different string."""
    runs = re.findall(r"[A-Za-z]+|[0-9]+", number)
    return "/".join(run.lower() if run.isalpha() else str(int(run)) for run in runs)


def _build_derived(state: _State, scenario: Scenario, original: Built) -> None:
    rng = state.rng
    source = original.invoice
    profile = next(p for p in state.profiles if p.vendor.vendor_id == source.vendor_id)
    notes = ""
    if scenario.name == "clean_repeat_order":
        old_po = next(po for po in state.pos if po.po_id == source.po_id)
        po_date = source.invoice_date + timedelta(days=rng.randint(1, 3))
        po = old_po.model_copy(
            update={
                "po_id": state.po_id(),
                "po_date": po_date,
                "valid_until": po_date + timedelta(days=PO_VALIDITY_DAYS),
                "status": POStatus.OPEN,
            }
        )
        state.pos.append(po)
        billed = {line.po_line_no for line in source.lines}
        grn_date = po_date + timedelta(days=rng.randint(4, 8))
        state.grns.append(
            GoodsReceipt(
                grn_id=state.grn_id(),
                po_id=po.po_id,
                received_date=grn_date,
                lines=tuple(
                    GRNLine(po_line_no=line.line_no, quantity_received=line.quantity)
                    for line in po.lines
                    if line.line_no in billed
                ),
            )
        )
        invoice_date = max(grn_date, source.invoice_date + timedelta(days=rng.randint(10, 20)))
        invoice = source.model_copy(
            update={
                "po_id": po.po_id,
                "invoice_number": _next_number(profile),
                "invoice_date": invoice_date,
                "received_date": invoice_date + timedelta(days=rng.randint(0, 3)),
            }
        )
    else:
        if scenario.name in {"duplicate_exact", "adv_duplicate_claims_cancelled"}:
            number, invoice_date = source.invoice_number, source.invoice_date
            received_date = source.received_date + timedelta(days=rng.randint(3, 40))
        elif scenario.name == "duplicate_reformatted":
            number, invoice_date = _reformat(source.invoice_number), source.invoice_date
            received_date = source.received_date + timedelta(days=rng.randint(3, 40))
        else:  # duplicate_renumbered
            number = f"{profile.initials}R-{profile.next_number + 5000}"
            profile.next_number += 1
            invoice_date = source.invoice_date + timedelta(days=rng.randint(0, 7))
            received_date = max(source.received_date, invoice_date) + timedelta(
                days=rng.randint(1, 4)
            )
        if scenario.name == "adv_duplicate_claims_cancelled":
            notes = rng.choice(words.DUPLICATE_CLAIMS_CANCELLED)
        invoice = source.model_copy(
            update={
                "invoice_number": number,
                "invoice_date": invoice_date,
                "received_date": received_date,
                "notes": notes,
            }
        )
    rationale = f"{scenario.rationale} (original: order {original.order})"
    state.built.append(Built(scenario, len(state.built), invoice, rationale))


# ---------------------------------------------------------------------------------------
# Top level


def generate(seed: int = DEFAULT_SEED) -> Dataset:
    rng = random.Random(seed)
    state = _State(rng=rng)
    _make_vendors(state)

    pool = list(state.profiles)
    rng.shuffle(pool)
    invalid_master, escalation, rest = pool[:2], pool[2:4], pool[4:]
    contract_vendors = escalation + rest[:4]
    regular = rest
    for profile in invalid_master:
        profile.vendor = profile.vendor.model_copy(
            update={"gstin": _corrupt_check_character(rng, profile.vendor.gstin)}
        )

    slots: list[Slot] = []
    for scenario in (*MAIN, *(s for s in ADVERSARIAL if s.name not in DERIVED_FROM_ORIGINAL)):
        for _ in range(scenario.count):
            slots.append(Slot(scenario=scenario, order=len(slots)))
    for i, slot in enumerate(slots):
        if slot.scenario.name.startswith("price_escalation"):
            slot.profile = escalation[i % 2]
        elif slot.scenario.name == "gst_vendor_master_invalid":
            slot.profile = invalid_master[i % 2]
        else:
            slot.profile = rng.choice(regular)

    pairable = [s for s in slots if s.scenario.pairable or s.scenario.name in ADVERSARIAL_PAIRABLE]
    rng.shuffle(pairable)
    # Each unpaired slot and each repeat order gets its own PO; pairs share one.
    repeat_orders = next(s.count for s in DERIVED if s.name == "clean_repeat_order")
    n_pairs = min(len(pairable) // 2, len(slots) + repeat_orders - TARGET_PURCHASE_ORDERS)
    groups: list[list[Slot]] = []
    paired: set[int] = set()
    for k in range(n_pairs):
        first, second = pairable[2 * k], pairable[2 * k + 1]
        second.profile = first.profile
        groups.append([first, second])
        paired.update({first.order, second.order})
    groups.extend([slot] for slot in slots if slot.order not in paired)
    rng.shuffle(groups)

    value_targets = list(VALUE_TARGETS)
    for group in groups:
        _build_group(state, group, value_targets)

    originals = [b for b in state.built if b.scenario.name == "clean_exact"]
    derived = [*DERIVED, *(s for s in ADVERSARIAL if s.name in DERIVED_FROM_ORIGINAL)]
    needed = sum(s.count for s in derived)
    chosen = rng.sample(originals, needed)
    for scenario in derived:
        for _ in range(scenario.count):
            _build_derived(state, scenario, chosen.pop())

    return _finish(state, seed, contract_vendors)


def _finish(state: _State, seed: int, contract_vendors: list[VendorProfile]) -> Dataset:
    rng = state.rng
    ordered = sorted(state.built, key=lambda b: (b.invoice.received_date, b.order))
    invoices: list[Invoice] = []
    labels: list[GroundTruth] = []
    for n, built in enumerate(ordered, start=1):
        invoice = built.invoice.model_copy(update={"invoice_id": f"INV-{n:05d}"})
        invoices.append(invoice)
        scenario = built.scenario
        labels.append(
            GroundTruth(
                invoice_id=invoice.invoice_id,
                split=Split.DEV,
                expected_exception=scenario.exception,
                expected_action=scenario.action,
                expected_required_approver=expected_approver(
                    scenario.action, scenario.exception, invoice.gross_total
                ),
                scenario=scenario.name,
                adversarial_kind=scenario.adversarial,
                rationale=built.rationale,
            )
        )
    labels = _assign_splits(rng, labels)

    contracts = []
    escalation_ids = {p.vendor.vendor_id for p in contract_vendors[:2]}
    for profile in sorted(contract_vendors, key=lambda p: p.vendor.vendor_id):
        vendor_id = profile.vendor.vendor_id
        escalates = vendor_id in escalation_ids
        contracts.append(
            ContractTerms(
                contract_id=f"CT-{vendor_id}",
                vendor_id=vendor_id,
                effective_from=date(2026, 4, 1),
                effective_to=date(2027, 3, 31),
                payment_terms_days=rng.choice((30, 45, 60)),
                escalation_max_pct=ESCALATION_MAX_PCT if escalates else None,
                escalation_effective_from=ESCALATION_FROM if escalates else None,
            )
        )

    return Dataset(
        seed=seed,
        generator_version=GENERATOR_VERSION,
        faker_version=package_version("faker"),
        vendors=tuple(p.vendor for p in state.profiles),
        purchase_orders=tuple(state.pos),
        goods_receipts=tuple(state.grns),
        invoices=tuple(invoices),
        ground_truth=tuple(labels),
        contracts=tuple(contracts),
    )


def _assign_splits(rng: random.Random, labels: list[GroundTruth]) -> list[GroundTruth]:
    """60/40 dev/eval, stratified by expected exception and adversarial or not."""
    strata: dict[tuple[str, bool], list[GroundTruth]] = {}
    for label in labels:
        key = (label.expected_exception.value, label.adversarial_kind is not None)
        strata.setdefault(key, []).append(label)
    eval_ids: set[str] = set()
    for key in sorted(strata):
        members = sorted(strata[key], key=lambda label: label.invoice_id)
        rng.shuffle(members)
        n_dev = int((len(members) * DEV_SHARE).to_integral_value(ROUND_HALF_UP))
        eval_ids.update(label.invoice_id for label in members[n_dev:])
    return [
        label.model_copy(
            update={"split": Split.EVAL if label.invoice_id in eval_ids else Split.DEV}
        )
        for label in labels
    ]
