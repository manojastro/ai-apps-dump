"""Typed extraction and quote schemas.

Extraction produces raw label/value text taken from rendered pages (by deterministic DOM reading
or a model). Normalization is always deterministic code; a model never supplies arithmetic.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedProduct(BaseModel):
    """Raw facts observed on a product page."""

    product_name: str
    sku: str | None = None
    fields: dict[str, str] = Field(default_factory=dict, description="label -> value text exactly as rendered")
    flags: list[str] = Field(default_factory=list, description="unlabelled spec chips or badges")
    source_url: str


class ExtractedCheckout(BaseModel):
    """Raw facts observed on a checkout preview / order summary."""

    fields: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list, description="statements such as 'Prices exclude GST'")
    address_ref: str | None = None
    source_url: str


class NormalizedSpec(BaseModel):
    family: str | None = None
    cpu: str | None = None
    ram_gb: int | None = None
    ssd_gb: int | None = None
    storage_type: str | None = None
    display_in: float | None = None
    os: str | None = None


class NormalizedQuote(BaseModel):
    supplier_key: str
    sku: str
    product_name: str
    canonical_id: str | None
    spec: NormalizedSpec
    quantity: int
    pack_size: int | None
    stock_observed: int | None
    unit_price: Decimal | None
    subtotal: Decimal | None
    discount: Decimal | None
    tax: Decimal | None
    shipping: Decimal | None
    total: Decimal | None
    currency: str | None
    price_basis: Literal["exclusive", "inclusive"] | None
    tax_basis: str | None
    tax_rate: Decimal | None
    delivery_date: date | None
    delivery_confidence: Literal["confirmed", "estimated", "unknown"]
    address_ref: str | None
    supplier_quote_ref: str | None
    source_url: str
    retrieved_at: datetime
    issues: list[str] = Field(default_factory=list)
    arithmetic_ok: bool = False
    extraction_method: str = "dom"
