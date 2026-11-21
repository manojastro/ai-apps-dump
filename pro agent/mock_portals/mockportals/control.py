"""Private fixture control API for the operator and evaluator.

Never add these endpoints to the browser allowlist or the agent tool registry. Every call
requires the X-Control-Token header.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from . import db
from .portal import mfa_code_for


def control_token() -> str:
    return os.environ.get("FIXTURE_CONTROL_TOKEN", "dev-control-token")


def require_token(x_control_token: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_control_token, control_token()):
        raise HTTPException(status_code=401, detail="invalid control token")


class ResetBody(BaseModel):
    scenario: str = "happy_path"
    keep_orders: bool = False


class MutateBody(BaseModel):
    supplier: str
    products: dict[str, dict[str, Any]] = Field(default_factory=dict)
    effects: dict[str, Any] | None = None


def create_control_app() -> FastAPI:
    app = FastAPI(title="Supplier fixture control (private)")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    api = APIRouter(dependencies=[Depends(require_token)])

    @api.get("/_control/scenarios")
    def scenarios():
        return {k: {"description": v["description"]} for k, v in db.load_scenarios().items()}

    @api.post("/_control/reset")
    def reset(body: ResetBody):
        try:
            return db.reset(body.scenario, keep_orders=body.keep_orders)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown scenario") from exc

    @api.get("/_control/state")
    def state():
        with db.engine().connect() as conn:
            st = db.get_state(conn)
            stock = {
                f"{r['supplier']}:{r['sku']}": {"stock": r["stock"], "unit_price": str(r["unit_price"]),
                                                 "price_version": r["price_version"]}
                for r in conn.execute(select(db.products)).mappings()
            }
        return {"scenario": st["name"], "counters": st["counters"], "products": stock}

    @api.post("/_control/mutate")
    def mutate(body: MutateBody):
        with db.engine().begin() as conn:
            db.apply_product_changes(conn, body.supplier, body.products)
            if body.effects is not None:
                st = db.get_state(conn)
                effects = dict(st["effects"])
                effects[body.supplier] = {**effects.get(body.supplier, {}), **body.effects}
                conn.execute(db.scenario_state.update().where(db.scenario_state.c.id == 1).values(effects=effects))
        return {"ok": True}

    @api.get("/_control/orders")
    def orders(supplier: str | None = None):
        with db.engine().connect() as conn:
            q = select(db.orders).order_by(db.orders.c.id)
            if supplier:
                q = q.where(db.orders.c.supplier == supplier)
            rows = [
                {k: (str(v) if not isinstance(v, (int, str, type(None))) else v) for k, v in dict(r).items()}
                for r in conn.execute(q).mappings()
            ]
        return {"orders": rows, "count": len(rows)}

    @api.get("/_control/requests")
    def requests(supplier: str | None = None, limit: int = 500):
        with db.engine().connect() as conn:
            q = select(db.request_log).order_by(db.request_log.c.id.desc()).limit(min(limit, 5000))
            if supplier:
                q = q.where(db.request_log.c.supplier == supplier)
            rows = [dict(r) | {"at": r["at"].isoformat()} for r in conn.execute(q).mappings()]
            counts = dict(
                conn.execute(
                    select(db.request_log.c.supplier, func.count()).group_by(db.request_log.c.supplier)
                ).all()
            )
        return {"requests": rows, "counts": counts}

    @api.get("/_control/mfa-code")
    def mfa_code(supplier: str):
        """Operator-only: shows the pending one-time code so a human can complete the challenge."""
        with db.engine().connect() as conn:
            row = conn.execute(
                select(db.sessions.c.token)
                .where(db.sessions.c.supplier == supplier, db.sessions.c.mfa_pending.is_(True))
                .order_by(db.sessions.c.created_at.desc())
            ).first()
        if row is None:
            raise HTTPException(status_code=404, detail="no pending challenge")
        return {"supplier": supplier, "code": mfa_code_for(row[0])}

    app.include_router(api)
    return app
