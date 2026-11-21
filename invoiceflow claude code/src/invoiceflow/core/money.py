"""Exact money arithmetic. Amounts are Decimal rupees rounded half-up to paise; never float."""

from decimal import ROUND_HALF_UP, Decimal

PAISE = Decimal("0.01")
QUANTITY_STEP = Decimal("0.001")
PERCENT_STEP = Decimal("0.0001")


def to_money(value: Decimal | int | str) -> Decimal:
    """Round to paise, half-up (₹10.005 → ₹10.01)."""
    return Decimal(value).quantize(PAISE, rounding=ROUND_HALF_UP)


def to_quantity(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(QUANTITY_STEP, rounding=ROUND_HALF_UP)


def percent_of(part: Decimal, whole: Decimal) -> Decimal:
    """`part` as a percentage of `whole`, to 4 decimal places. A zero `whole` gives 0."""
    if whole == 0:
        return Decimal("0.0000")
    return (part * 100 / whole).quantize(PERCENT_STEP, rounding=ROUND_HALF_UP)


def format_inr(amount: Decimal) -> str:
    """Indian digit grouping: Decimal('1234567.5') → '₹12,34,567.50'."""
    value = to_money(amount)
    sign = "-" if value < 0 else ""
    whole, _, paise = f"{abs(value):.2f}".partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups: list[str] = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join([*groups, tail])
    return f"{sign}₹{whole}.{paise}"
