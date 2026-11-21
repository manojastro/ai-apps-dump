from __future__ import annotations

import uuid
from datetime import timedelta

from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app import clock
from app.data.models import Appointment, SupplyItem, SupplyOrder
from app.tools.base import MutatingInput, ToolContext, ToolError, register


class GetStockIn(BaseModel):
    sku: str | None = None
    low_only: bool = False


class StockOut(BaseModel):
    sku: str
    name: str
    on_hand: int
    reorder_level: int
    pack_size: int


class GetStockOut(BaseModel):
    items: list[StockOut]


@register("get_stock", "Current stock levels (no patient data).", GetStockIn)
def get_stock(ctx: ToolContext, a: GetStockIn) -> GetStockOut:
    q = select(SupplyItem).order_by(SupplyItem.sku)
    if a.sku:
        q = q.where(SupplyItem.sku == a.sku)
    if a.low_only:
        q = q.where(SupplyItem.on_hand <= SupplyItem.reorder_level)
    return GetStockOut(items=[StockOut(sku=r.sku, name=r.name, on_hand=r.on_hand, reorder_level=r.reorder_level,
                                       pack_size=r.pack_size) for r in ctx.session.scalars(q)])


class ForecastIn(BaseModel):
    days: int = Field(default=14, ge=1, le=30)


class ForecastLine(BaseModel):
    sku: str
    forecast_usage: float


class ForecastOut(BaseModel):
    days: int
    upcoming_appointments: int
    items: list[ForecastLine]


@register("get_usage_forecast", "Forecast supply usage from the COUNT of upcoming appointments (no patient data).",
          ForecastIn)
def get_usage_forecast(ctx: ToolContext, a: ForecastIn) -> ForecastOut:
    now = clock.now()
    n = ctx.session.scalar(select(func.count()).select_from(Appointment).where(
        Appointment.status == "booked", Appointment.start > now,
        Appointment.start <= now + timedelta(days=a.days))) or 0
    items = ctx.session.scalars(select(SupplyItem).order_by(SupplyItem.sku)).all()
    return ForecastOut(days=a.days, upcoming_appointments=n,
                       items=[ForecastLine(sku=i.sku, forecast_usage=round(i.usage_per_appointment * n, 1))
                              for i in items])


class OrderLine(BaseModel):
    sku: str
    quantity: int = Field(ge=1, le=1000)


class DraftOrderIn(MutatingInput):
    lines: list[OrderLine] = Field(min_length=1, max_length=40)


class DraftOrderOut(BaseModel):
    order_id: str
    status: str


@register("draft_supply_order", "Create a DRAFT supply order. It is not placed until a human approves it.",
          DraftOrderIn)
def draft_supply_order(ctx: ToolContext, a: DraftOrderIn) -> DraftOrderOut:
    skus = {ln.sku for ln in a.lines}
    if len(skus) != len(a.lines):
        raise ToolError("duplicate sku in order")
    known = set(ctx.session.scalars(select(SupplyItem.sku).where(SupplyItem.sku.in_(skus))))
    if unknown := skus - known:
        raise ToolError(f"unknown sku(s): {sorted(unknown)}")
    o = SupplyOrder(id=f"ord-{uuid.uuid4().hex[:8]}", workflow_id=ctx.workflow_id, status="draft",
                    lines=[ln.model_dump() for ln in a.lines], created_at=clock.now())
    ctx.session.add(o)
    return DraftOrderOut(order_id=o.id, status="draft")
