"""Deterministic normalization of extracted supplier facts into a typed, verified quote.

All money is Decimal. Landed cost comes from the supplier's checkout preview and is then
independently recomputed from its components; inconsistent arithmetic is flagged, never
silently corrected.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from .schemas import ExtractedCheckout, ExtractedProduct, NormalizedQuote, NormalizedSpec

PAISE = Decimal("0.01")
_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def money(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


def _key(label: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%@ ]+", " ", label.lower())).strip()


def parse_money(text: str | None) -> Decimal | None:
    if not text:
        return None
    m = _NUM.search(text.replace("₹", " "))
    if not m:
        return None
    try:
        return money(Decimal(m.group(0).replace(",", "")))
    except InvalidOperation:
        return None


def detect_currency(*texts: str | None) -> str | None:
    joined = " ".join(t for t in texts if t)
    found = set()
    if "INR" in joined or "₹" in joined or re.search(r"\bRs\.?\s", joined):
        found.add("INR")
    for code in ("USD", "EUR", "GBP"):
        if code in joined or {"USD": "$", "EUR": "€", "GBP": "£"}[code] in joined:
            found.add(code)
    return found.pop() if len(found) == 1 else None


def parse_int(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"-?\d+", text.replace(",", ""))
    return int(m.group(0)) if m else None


def parse_capacity_gb(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB|G|T)\b", text, re.IGNORECASE)
    if not m:
        return None
    value = Decimal(m.group(1))
    if m.group(2).upper().startswith("T"):
        value *= 1024
    return int(value)


def parse_iso_date(text: str | None) -> date | None:
    if not text:
        return None
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_rate(text: str | None) -> Decimal | None:
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    return (Decimal(m.group(1)) / 100) if m else None


def _first(fields: dict[str, str], patterns: list[str]) -> tuple[str, str] | None:
    """Return (label, value) for the first label matching any pattern, in pattern priority order."""
    keyed = [(label, _key(label), value) for label, value in fields.items()]
    for pat in patterns:
        rx = re.compile(pat)
        for label, k, value in keyed:
            if rx.search(k):
                return label, value
    return None


PRODUCT_FIELDS: dict[str, list[str]] = {
    "sku": [r"^(item code|sku|part number|reference|ref)$"],
    "cpu": [r"^(processor|cpu)$"],
    "ram": [r"^(memory ram|installed ram|ram|memory)$"],
    "storage": [r"^(storage|ssd capacity|ssd|drive)$"],
    "display": [r"^(display|screen size|screen)$"],
    "os": [r"^(operating system|os)$"],
    "pack": [r"^(units per listing|units per pack|bundle contents|pack)$"],
    "unit_price": [r"^(unit price|per unit price|price each|unit rate)", r"^price"],
    "stock": [r"^(availability|available quantity|stock level|stock)$"],
    "delivery": [r"^(estimated delivery|ships in|lead time|arrives in)"],
    "discount": [r"^(volume discount|discount)"],
    "shipping": [r"^(shipping|freight|delivery fee|delivery charge)"],
    "gst": [r"^gst"],
}

CHECKOUT_FIELDS: dict[str, list[str]] = {
    "item": [r"^(item|product|part number)$"],
    "quantity": [r"^(quantity|qty|order quantity)$"],
    "unit_price": [r"^(unit price|price each|unit rate)"],
    "subtotal": [r"^(subtotal|items total|goods value)"],
    "discount": [r"^(discount|savings|volume discount)"],
    "tax": [r"^gst"],
    "shipping": [r"^(shipping|freight|delivery fee|delivery charge)"],
    "total": [r"^(total payable|grand total|order value|total)$", r"^(total payable|grand total|order value)"],
    "currency": [r"^currency$"],
    "delivery_date": [r"^(estimated delivery date|arrives by|expected dispatch arrival|expected arrival)"],
    "quote_ref": [r"^quote reference$"],
}


@dataclass
class ProductFacts:
    sku: str | None
    product_name: str
    canonical_id: str | None
    spec: NormalizedSpec
    pack_size: int | None
    stock: int | None
    unit_price: Decimal | None
    price_basis: str | None
    delivery_days: int | None
    delivery_certain: bool
    advertised_discount: str | None
    issues: list[str] = field(default_factory=list)


def _pack_size(value: str | None, flags: list[str], name: str) -> tuple[int | None, list[str]]:
    texts = [t for t in [value, *flags] if t]
    issues = []
    for t in texts:
        low = t.lower()
        if re.search(r"bundle|multiple|varies|multi-unit|pack of|\bpack\b", low) and not re.search(
            r"single|individual", low
        ):
            issues.append(f"Pack quantity is ambiguous: '{t}'")
            return None, issues
        if re.search(r"single unit|sold individually|^1( unit)?$", low.strip()):
            return 1, issues
    if re.search(r"bundle|multi-unit|pack", name.lower()):
        issues.append(f"Listing name suggests a multi-unit pack: '{name}'")
        return None, issues
    if value is not None:
        n = parse_int(value)
        if n is not None:
            return n, issues
    issues.append("Units per listing not stated")
    return None, issues


def _price_basis(*texts: str | None) -> str | None:
    joined = " ".join(t.lower() for t in texts if t)
    inclusive = bool(re.search(r"incl\.?\s*gst|include[sd]?\s+gst|incl\. gst|inclusive", joined))
    exclusive = bool(
        re.search(
            r"excl\.?\s*gst|exclud\w*\s+gst|ex-tax|ex tax|excluding gst|exclusive|\+ gst|gst extra|"
            r"charged extra|added at checkout|% extra",
            joined,
        )
    )
    if inclusive and not exclusive:
        return "inclusive"
    if exclusive and not inclusive:
        return "exclusive"
    return None


def normalize_product(
    ext: ExtractedProduct, supplier_key: str, sku_map: dict[str, dict[str, str]], canonical: dict[str, Any]
) -> ProductFacts:
    f = ext.fields
    issues: list[str] = []
    hit = lambda name: _first(f, PRODUCT_FIELDS[name])  # noqa: E731
    sku = ext.sku or (hit("sku") or (None, None))[1]
    sku = sku.strip() if sku else None
    chip = {c.split(":", 1)[0].strip().lower(): c.split(":", 1)[1].strip() for c in ext.flags if ":" in c}
    cpu = (hit("cpu") or (None, chip.get("cpu")))[1]
    ram_txt = (hit("ram") or (None, chip.get("ram")))[1]
    ssd_txt = (hit("storage") or (None, chip.get("ssd")))[1]
    disp = (hit("display") or (None, chip.get("display")))[1]
    os_txt = (hit("os") or (None, chip.get("os")))[1]
    storage_type = (
        "SSD"
        if (ssd_txt and "ssd" in ssd_txt.lower())
        or "ssd" in chip
        or hit("storage")
        and "ssd" in (hit("storage")[0].lower())
        else None
    )
    if storage_type is None and ssd_txt and re.search(r"ssd", ext.product_name, re.IGNORECASE):
        storage_type = "SSD"
    canonical_id = sku_map.get(supplier_key, {}).get(sku or "")
    family = canonical.get(canonical_id, {}).get("family") if canonical_id else None
    if canonical_id is None:
        issues.append(f"SKU {sku!r} has no canonical mapping")
    display = None
    if disp:
        m = re.search(r"\d+(?:\.\d+)?", disp)
        display = float(m.group(0)) if m else None
    spec = NormalizedSpec(
        family=family,
        cpu=cpu.strip() if cpu else None,
        ram_gb=parse_capacity_gb(ram_txt),
        ssd_gb=parse_capacity_gb(ssd_txt),
        storage_type=storage_type,
        display_in=display,
        os=os_txt.strip() if os_txt else None,
    )
    pack_label = hit("pack")
    pack_size, pack_issues = _pack_size(pack_label[1] if pack_label else None, ext.flags, ext.product_name)
    issues += pack_issues
    price_hit = hit("unit_price")
    unit_price = parse_money(price_hit[1]) if price_hit else None
    basis = _price_basis(
        price_hit[0] if price_hit else None,
        price_hit[1] if price_hit else None,
        (hit("gst") or ("", ""))[1],
        " ".join(f.keys()),
    )
    stock_hit = hit("stock")
    stock = parse_int(stock_hit[1]) if stock_hit else None
    delivery_hit = hit("delivery")
    delivery_days = None
    certain = False
    if delivery_hit:
        m = re.search(r"(\d+)\s*(?:business\s+)?days?", delivery_hit[1], re.IGNORECASE)
        uncertain = re.search(
            r"tbc|to be confirmed|not confirmed|subject to|varies|\d+\s*-\s*\d+", delivery_hit[1], re.IGNORECASE
        )
        if m and not uncertain:
            delivery_days, certain = int(m.group(1)), True
    disc = hit("discount")
    return ProductFacts(
        sku,
        ext.product_name,
        canonical_id,
        spec,
        pack_size,
        stock,
        unit_price,
        basis,
        delivery_days,
        certain,
        disc[1] if disc else None,
        issues,
    )


def _close(a: Decimal | None, b: Decimal | None, tol: Decimal) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def normalize_quote(
    product: ProductFacts,
    checkout: ExtractedCheckout,
    *,
    supplier_key: str,
    requested_quantity: int,
    retrieved_at: datetime,
    tolerance: Decimal = Decimal("0.05"),
    extraction_method: str = "dom",
) -> NormalizedQuote:
    f = checkout.fields
    hit = lambda name: _first(f, CHECKOUT_FIELDS[name])  # noqa: E731
    issues = list(product.issues)
    val = lambda name: parse_money(hit(name)[1]) if hit(name) else None  # noqa: E731
    qty = parse_int(hit("quantity")[1]) if hit("quantity") else None
    unit_price, subtotal, discount = val("unit_price"), val("subtotal"), val("discount")
    tax, shipping, total = val("tax"), val("shipping"), val("total")
    tax_label = hit("tax")[0] if hit("tax") else ""
    tax_rate = parse_rate(tax_label)
    currency_txt = hit("currency")[1] if hit("currency") else None
    currency = (currency_txt or "").strip().upper() or detect_currency(*(f.values()))
    basis = (
        _price_basis(*checkout.notes, hit("unit_price")[0] if hit("unit_price") else None, tax_label)
        or product.price_basis
    )
    if tax_label and "included" in tax_label.lower():
        basis = "inclusive"
    delivery_txt = hit("delivery_date")[1] if hit("delivery_date") else None
    delivery_date = parse_iso_date(delivery_txt)
    confidence = (
        "confirmed" if delivery_date and product.delivery_certain else ("estimated" if delivery_date else "unknown")
    )
    quote_ref = hit("quote_ref")[1].strip() if hit("quote_ref") else None
    item_txt = hit("item")[1] if hit("item") else ""
    sku = product.sku or ""
    if item_txt and sku and sku not in item_txt:
        issues.append(f"Checkout item '{item_txt}' does not match inspected SKU {sku}")

    for name, value in (
        ("unit price", unit_price),
        ("subtotal", subtotal),
        ("discount", discount),
        ("tax", tax),
        ("shipping", shipping),
        ("total", total),
    ):
        if value is None:
            issues.append(f"Missing cost component: {name}")
    if qty is None:
        issues.append("Checkout quantity not shown")
    elif qty != requested_quantity:
        issues.append(f"Checkout quantity {qty} differs from requested {requested_quantity}")
    if currency is None:
        issues.append("Currency uncertain")
    if basis is None:
        issues.append("Tax basis (inclusive/exclusive) not stated")
    if product.unit_price is not None and unit_price is not None and product.unit_price != unit_price:
        issues.append(f"Product page unit price {product.unit_price} differs from checkout {unit_price}")
    if (
        product.advertised_discount
        and product.advertised_discount.lower() not in ("none", "")
        and (discount is None or discount == 0)
    ):
        issues.append(f"Advertised discount '{product.advertised_discount}' not applied at checkout")

    arithmetic_ok = False
    tax_basis = None
    if None not in (unit_price, subtotal, discount, tax, shipping, total) and qty:
        checks = [_close(money(unit_price * qty), subtotal, tolerance)]
        if not checks[0]:
            issues.append(f"Subtotal {subtotal} != unit price x quantity {money(unit_price * qty)}")
        if basis == "exclusive":
            ok_total = _close(subtotal - discount + tax + shipping, total, tolerance)
            if not ok_total:
                issues.append(f"Total {total} != subtotal - discount + tax + shipping")
            checks.append(ok_total)
            if tax_rate is not None:
                goods = subtotal - discount
                if _close(money(goods * tax_rate), tax, tolerance):
                    tax_basis = "goods_only"
                elif _close(money((goods + shipping) * tax_rate), tax, tolerance):
                    tax_basis = "goods_and_shipping"
                else:
                    issues.append(f"Tax {tax} does not match {tax_rate:%} of the taxable amount")
                    checks.append(False)
        elif basis == "inclusive":
            ok_total = _close(subtotal - discount + shipping, total, tolerance)
            if not ok_total:
                issues.append(f"Total {total} != subtotal - discount + shipping (tax-inclusive)")
            checks.append(ok_total)
            if tax_rate is not None:
                goods = subtotal - discount
                embedded = lambda g: money(g - g / (1 + tax_rate))  # noqa: E731
                if _close(embedded(goods + shipping), tax, tolerance):
                    tax_basis = "goods_and_shipping"
                elif _close(embedded(goods), tax, tolerance):
                    tax_basis = "goods_only"
                else:
                    issues.append("Embedded tax component inconsistent with stated rate")
                    checks.append(False)
        else:
            checks.append(False)
        arithmetic_ok = all(checks)

    return NormalizedQuote(
        supplier_key=supplier_key,
        sku=sku,
        product_name=product.product_name,
        canonical_id=product.canonical_id,
        spec=product.spec,
        quantity=qty or 0,
        pack_size=product.pack_size,
        stock_observed=product.stock,
        unit_price=unit_price,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        shipping=shipping,
        total=total,
        currency=currency,
        price_basis=basis,  # type: ignore[arg-type]
        tax_basis=tax_basis,
        tax_rate=tax_rate,
        delivery_date=delivery_date,
        delivery_confidence=confidence,  # type: ignore[arg-type]
        address_ref=checkout.address_ref,
        supplier_quote_ref=quote_ref,
        source_url=checkout.source_url,
        retrieved_at=retrieved_at,
        issues=issues,
        arithmetic_ok=arithmetic_ok,
        extraction_method=extraction_method,
    )


def _canon(value: Any) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _canon(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canon(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canon(value), sort_keys=True, separators=(",", ":"))


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


CART_FIELDS = (
    "supplier_key",
    "sku",
    "quantity",
    "unit_price",
    "discount",
    "tax",
    "shipping",
    "total",
    "currency",
    "delivery_date",
    "address_ref",
    "supplier_quote_ref",
)


def cart_view(q: NormalizedQuote) -> dict[str, Any]:
    return {k: getattr(q, k) for k in CART_FIELDS}


def cart_fingerprint(q: NormalizedQuote) -> str:
    return sha256_hex(cart_view(q))


def quote_hash(q: NormalizedQuote) -> str:
    data = q.model_dump(exclude={"retrieved_at", "issues", "source_url", "extraction_method"})
    return sha256_hex(data)
