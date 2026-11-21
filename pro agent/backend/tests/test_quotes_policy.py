"""Milestone 2 gate (unit level): all three portal layouts normalize, and incompatible or
over-budget offers fail with the exact rule. Inputs mirror real extraction output."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from procnav.policies.defaults import DEFAULT_POLICY
from procnav.policies.engine import RequestSpec, SupplierStatus, evaluate, material_changes, rank
from procnav.quotes.normalize import cart_view, normalize_product, normalize_quote, parse_money
from procnav.quotes.schemas import ExtractedCheckout, ExtractedProduct

FIX = Path(__file__).resolve().parents[2] / "fixtures"
SKU_MAP = json.loads((FIX / "sku_map.json").read_text())
CANON = json.loads((FIX / "canonical_products.json").read_text())
NOW = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
DEADLINE = date(2026, 10, 13)

REQ = RequestSpec(
    canonical_product_id="NW-PRO14-16-512",
    required_spec={
        "family": "Northwind Pro 14",
        "cpu": "Core i5-1335U",
        "min_ram_gb": 16,
        "min_ssd_gb": 512,
        "storage_type": "SSD",
        "os": "Windows 11 Pro",
    },
    quantity=10,
    currency="INR",
    budget_total=Decimal("500000.00"),
    address_ref="ADDR-BLR-01",
    delivery_deadline=DEADLINE,
    allowed_supplier_keys=("alpha", "beta", "gamma"),
)
OK_SUPPLIER = lambda k: SupplierStatus(k, True, "approved")  # noqa: E731

ALPHA_PRODUCT = ExtractedProduct(
    product_name="Northwind Pro 14 Business Laptop - 16GB RAM / 512GB SSD",
    fields={
        "Item code": "A-NW14-16-512",
        "Processor": "Core i5-1335U",
        "Memory (RAM)": "16 GB",
        "Storage": "512 GB SSD",
        "Display": "14 inch",
        "Operating system": "Windows 11 Pro",
        "Units per listing": "1 unit",
        "Unit price (excl. GST)": "INR 41,500.00",
        "GST": "18% extra on goods (synthetic rate)",
        "Shipping": "INR 1,500.00 per order",
        "Availability": "25 in stock",
        "Estimated delivery": "4 days",
    },
    source_url="http://127.0.0.1:8301/item/A-NW14-16-512",
)
ALPHA_CHECKOUT = ExtractedCheckout(
    fields={
        "Item": "A-NW14-16-512 Northwind Pro 14 Business Laptop - 16GB RAM / 512GB SSD",
        "Quantity": "10",
        "Unit price (excl. GST)": "INR 41,500.00",
        "Subtotal": "INR 4,15,000.00",
        "Discount": "INR 0.00",
        "GST (18%, synthetic, on goods)": "INR 74,700.00",
        "Shipping": "INR 1,500.00",
        "Total payable": "INR 4,91,200.00",
        "Currency": "INR",
        "Estimated delivery date": "2026-10-10",
        "Quote reference": "QR-463BBC0C38BD",
    },
    address_ref="ADDR-BLR-01",
    source_url="http://127.0.0.1:8301/checkout/confirm",
)


def beta(ram="16G", price="47,200.00", items="4,72,000.00", gst="72,305.08", total="4,74,000.00", sku="B-77821"):
    p = ExtractedProduct(
        product_name=f"NW Pro14 i5 / {ram} / 512G SSD / W11P",
        fields={
            "Price each (incl. GST)": f"₹{price}",
            "Delivery fee (incl. GST)": "₹2,000.00 per order",
            "Stock": "12 units",
            "Ships in": "6 days",
            "SKU": sku,
        },
        flags=[
            "CPU: Core i5-1335U",
            f"RAM: {ram}",
            "SSD: 512G",
            'Display: 14"',
            "OS: Windows 11 Pro",
            "Sold individually",
        ],
        source_url=f"http://127.0.0.1:8302/p/{sku}",
    )
    c = ExtractedCheckout(
        fields={
            "Product": f"NW Pro14 ({sku})",
            "Qty": "10",
            "Price each (incl. GST)": f"₹{price}",
            "Items total (incl. GST)": f"₹{items}",
            "Savings": "₹0.00",
            "Delivery fee (incl. GST)": "₹2,000.00",
            "GST included in total (18%, synthetic)": f"₹{gst}",
            "Grand total": f"₹{total}",
            "Currency": "INR",
            "Arrives by": "2026-10-12",
            "Quote reference": "QR-AAAA",
        },
        address_ref="ADDR-BLR-01",
        source_url="http://127.0.0.1:8302/checkout/final",
    )
    return p, c


GAMMA_PRODUCT = ExtractedProduct(
    product_name="Northwind Professional 14-inch Notebook",
    fields={
        "Part number": "G-PRO14-16",
        "CPU": "Core i5-1335U",
        "RAM": "16 GB",
        "SSD capacity": "512 GB",
        "Screen": "14 inch",
        "OS": "Windows 11 Pro",
        "Units per pack": "1",
        "Unit rate (ex-tax)": "INR 42,900.00",
        "Volume discount": "None",
        "GST": "18% on goods, charged extra (synthetic)",
        "Freight": "INR 350.00 per unit",
        "Available quantity": "40",
        "Lead time": "5 days",
    },
    source_url="http://127.0.0.1:8303/products/G-PRO14-16",
)
GAMMA_CHECKOUT = ExtractedCheckout(
    fields={
        "Part number": "G-PRO14-16",
        "Order quantity": "10",
        "Unit rate (ex-tax)": "INR 42,900.00",
        "Goods value": "INR 4,29,000.00",
        "Volume discount": "INR 0.00",
        "GST @18% (synthetic)": "INR 77,220.00",
        "Freight": "INR 3,500.00",
        "Order value": "INR 5,09,720.00",
        "Currency": "INR",
        "Expected dispatch arrival": "2026-10-11",
        "Quote reference": "QR-BBBB",
    },
    address_ref="ADDR-BLR-01",
    source_url="http://127.0.0.1:8303/purchase/confirm",
)


def quote(supplier, product, checkout):
    facts = normalize_product(product, supplier, SKU_MAP, CANON)
    return normalize_quote(facts, checkout, supplier_key=supplier, requested_quantity=10, retrieved_at=NOW)


def failed(ev):
    return {r.rule for r in ev.failed_hard}


def test_parse_money_indian_grouping():
    assert parse_money("INR 4,91,200.00") == Decimal("491200.00")
    assert parse_money("₹47,200.00") == Decimal("47200.00")


def test_all_three_layouts_normalize_with_consistent_arithmetic():
    a = quote("alpha", ALPHA_PRODUCT, ALPHA_CHECKOUT)
    b = quote("beta", *beta())
    g = quote("gamma", GAMMA_PRODUCT, GAMMA_CHECKOUT)
    assert (a.total, b.total, g.total) == (Decimal("491200.00"), Decimal("474000.00"), Decimal("509720.00"))
    assert a.price_basis == "exclusive" and b.price_basis == "inclusive" and g.price_basis == "exclusive"
    assert a.tax_basis == "goods_only" and b.tax_basis == "goods_and_shipping" and g.tax_basis == "goods_only"
    for q in (a, b, g):
        assert q.arithmetic_ok, q.issues
        assert q.spec.ram_gb == 16 and q.spec.ssd_gb == 512 and q.spec.storage_type == "SSD"
        assert q.pack_size == 1 and q.delivery_confidence == "confirmed" and q.currency == "INR"


def test_policy_ranks_beta_first_and_rejects_gamma_on_landed_cost():
    quotes = [
        quote("alpha", ALPHA_PRODUCT, ALPHA_CHECKOUT),
        quote("beta", *beta()),
        quote("gamma", GAMMA_PRODUCT, GAMMA_CHECKOUT),
    ]
    evaluated = [(q, evaluate(q, REQ, OK_SUPPLIER(q.supplier_key), DEFAULT_POLICY, NOW)) for q in quotes]
    ranked = rank(evaluated)
    assert [q.supplier_key for q, _ in ranked] == ["beta", "alpha", "gamma"]
    gamma_eval = ranked[2][1]
    # Visible unit price x quantity (429000) is under budget; tax and freight push it over.
    assert failed(gamma_eval) == {"budget.landed_total"}


def test_cheaper_8gb_laptop_fails_exact_spec_rule():
    q = quote(
        "beta",
        *beta(ram="8G", price="38,900.00", items="3,89,000.00", gst="59,644.07", total="3,91,000.00", sku="B-77805"),
    )
    ev = evaluate(q, REQ, OK_SUPPLIER("beta"), DEFAULT_POLICY, NOW)
    assert not ev.eligible
    assert failed(ev) == {"spec.ram_gb"}
    rule = next(r for r in ev.results if r.rule == "spec.ram_gb")
    assert rule.expected == ">= 16 GB" and rule.observed == "8 GB"


def test_ambiguous_pack_and_uncertain_delivery_and_stock():
    p = ALPHA_PRODUCT.model_copy(deep=True)
    p.fields.pop("Units per listing")
    p.fields["Bundle contents"] = "Multiple units (allocation confirmed after order)"
    p.fields["Estimated delivery"] = "To be confirmed by supplier"
    p.fields["Availability"] = "6 in stock"
    q = quote("alpha", p, ALPHA_CHECKOUT)
    ev = evaluate(q, REQ, OK_SUPPLIER("alpha"), DEFAULT_POLICY, NOW)
    assert {"unit.pack_size", "delivery.confirmed", "stock.available"} <= failed(ev)
    assert q.pack_size is None


def test_inconsistent_arithmetic_and_missing_components_rejected():
    c = ALPHA_CHECKOUT.model_copy(deep=True)
    c.fields["Total payable"] = "INR 4,81,200.00"
    ev = evaluate(quote("alpha", ALPHA_PRODUCT, c), REQ, OK_SUPPLIER("alpha"), DEFAULT_POLICY, NOW)
    assert "arithmetic.consistent" in failed(ev)
    c2 = ALPHA_CHECKOUT.model_copy(deep=True)
    c2.fields.pop("Shipping")
    ev2 = evaluate(quote("alpha", ALPHA_PRODUCT, c2), REQ, OK_SUPPLIER("alpha"), DEFAULT_POLICY, NOW)
    assert {"cost.components_present", "arithmetic.consistent"} <= failed(ev2)


def test_stale_quote_suspended_supplier_wrong_destination():
    q = quote("alpha", ALPHA_PRODUCT, ALPHA_CHECKOUT.model_copy(update={"address_ref": "ADDR-PUN-02"}))
    ev = evaluate(q, REQ, SupplierStatus("alpha", True, "suspended"), DEFAULT_POLICY, NOW + timedelta(hours=2))
    assert {"quote.fresh", "supplier.eligible", "destination.match"} <= failed(ev)


def test_authorized_exception_is_explicit():
    q = quote("gamma", GAMMA_PRODUCT, GAMMA_CHECKOUT)
    ev = evaluate(q, REQ, OK_SUPPLIER("gamma"), DEFAULT_POLICY, NOW, exceptions={"budget.landed_total"})
    assert ev.eligible
    assert "authorized exception" in next(r for r in ev.results if r.rule == "budget.landed_total").message


def test_material_change_detects_price_rise():
    approved = cart_view(quote("beta", *beta()))
    current = quote("beta", *beta(price="48,900.00", items="4,89,000.00", gst="74,898.31", total="4,91,000.00"))
    changes = material_changes(approved, current, DEFAULT_POLICY["material_change_fields"])
    fields = {c["field"] for c in changes}
    assert {"unit_price", "total", "tax"} <= fields
    assert next(c for c in changes if c["field"] == "total") == {
        "field": "total",
        "approved": "474000.00",
        "current": "491000.00",
    }
    assert material_changes(approved, quote("beta", *beta()), DEFAULT_POLICY["material_change_fields"]) == []
