"""Default purchasing policy (version 1) for the synthetic demo tenants.

Policy lives in data and code, never in model prompts. Values are synthetic demo constraints.
"""

from __future__ import annotations

from typing import Any

DEFAULT_POLICY: dict[str, Any] = {
    "name": "Demo laptop purchasing policy",
    "allowed_currencies": ["INR"],
    "require_distinct_approver": True,
    "max_quote_age_seconds": 3600,
    "approval_ttl_seconds": 3600,
    "per_order_spending_limit": "600000.00",
    "arithmetic_tolerance": "0.05",
    "tax_convention": {
        "note": "Synthetic GST 18% fixture rate; not tax advice.",
        "exclusive": (
            "tax = round_half_up((subtotal - discount [+ shipping if tax_basis=goods_and_shipping]) * rate, 0.01)"
        ),
        "inclusive": "displayed prices include tax; tax component = gross - gross / (1 + rate), informational",
        "rounding": "ROUND_HALF_UP to 0.01 INR, once per component at order level",
    },
    "ranking": ["landed_total", "delivery_date", "supplier_key"],
    "destinations": {"ADDR-BLR-01": "Bengaluru HQ", "ADDR-PUN-02": "Pune Office"},
    "hard_rules": [
        "spec.canonical_family",
        "spec.ram_gb",
        "spec.ssd_gb",
        "spec.storage_type",
        "spec.os",
        "unit.pack_size",
        "quantity.match",
        "stock.available",
        "supplier.eligible",
        "delivery.confirmed",
        "delivery.deadline",
        "destination.match",
        "currency.allowed",
        "quote.fresh",
        "cost.components_present",
        "arithmetic.consistent",
        "budget.landed_total",
        "budget.spending_limit",
    ],
    "soft_preferences": {"max_delivery_days_preferred": 5, "preferred_suppliers": []},
    "material_change_fields": [
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
    ],
}
