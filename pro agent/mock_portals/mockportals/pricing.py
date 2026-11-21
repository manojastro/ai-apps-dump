"""Supplier-side price calculation. Each synthetic supplier has its own convention.

Rounding: every monetary component is rounded half-up to 0.01 INR (paise) once, at the order
level. Synthetic GST of 18% is a fixture value, not tax advice.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

PAISE = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class CartTotals:
    sku: str
    qty: int
    unit_price: Decimal
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    price_basis: str
    tax_basis: str
    delivery_days: int
    delivery_certain: bool
    delivery_date: str
    quote_ref: str


def compute_totals(
    supplier_cfg: dict[str, Any],
    product: dict[str, Any],
    qty: int,
    address_ref: str,
    *,
    apply_discount: bool = True,
    today: date | None = None,
) -> CartTotals:
    rate = Decimal(supplier_cfg["tax_rate"])
    unit = Decimal(product["unit_price"])
    subtotal = money(unit * qty)
    discount = Decimal("0")
    if apply_discount and product["discount_pct"] and qty >= int(product["discount_min_qty"] or 0):
        discount = money(subtotal * Decimal(product["discount_pct"]))
    ship_amount = Decimal(supplier_cfg["shipping_amount"])
    shipping = money(ship_amount * qty) if supplier_cfg["shipping_mode"] == "per_unit" else money(ship_amount)

    if supplier_cfg["price_basis"] == "exclusive":
        taxable = subtotal - discount
        if supplier_cfg["tax_basis"] == "goods_and_shipping":
            taxable += shipping
        tax = money(taxable * rate)
        total = subtotal - discount + tax + shipping
    else:
        # Inclusive prices: shown prices already contain GST. Report the embedded tax component.
        gross = subtotal - discount + (shipping if supplier_cfg["tax_basis"] == "goods_and_shipping" else 0)
        tax = money(gross - gross / (1 + rate))
        total = subtotal - discount + shipping

    today = today or datetime.now(UTC).date()
    delivery = today + timedelta(days=int(product["delivery_days"]))
    ref_source = "|".join(
        str(x)
        for x in (
            product["supplier"],
            product["sku"],
            qty,
            unit,
            discount,
            tax,
            shipping,
            total,
            product["delivery_days"],
            product["price_version"],
            address_ref,
        )
    )
    quote_ref = "QR-" + hashlib.sha256(ref_source.encode()).hexdigest()[:12].upper()
    return CartTotals(
        sku=product["sku"],
        qty=qty,
        unit_price=money(unit),
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        shipping=shipping,
        total=money(total),
        price_basis=supplier_cfg["price_basis"],
        tax_basis=supplier_cfg["tax_basis"],
        delivery_days=int(product["delivery_days"]),
        delivery_certain=bool(product["delivery_certain"]),
        delivery_date=delivery.isoformat(),
        quote_ref=quote_ref,
    )


def inr(value: Decimal | int | str) -> str:
    """Indian digit grouping, e.g. 474000.00 -> '4,74,000.00'."""
    d = money(Decimal(value))
    sign = "-" if d < 0 else ""
    whole, frac = f"{abs(d):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}{whole}.{frac}"
