"""Shared API helpers: pagination and domain-error translation."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.approvals.service import ApprovalError
from app.approvals.state_machine import InvalidTransition
from app.graphs.runner import WorkflowConflict
from app.integrations.scanners.file_import import ImportFormatError
from app.services.simulation import SimulationError
from app.tools.registry import ToolError


class Page(BaseModel):
    page: int
    page_size: int


def page_params(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)) -> Page:
    return Page(page=page, page_size=page_size)


def paginate(db: Session, query: Select[Any], page: Page, serialize: Any) -> dict[str, Any]:
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.scalars(query.offset((page.page - 1) * page.page_size).limit(page.page_size)).unique().all()
    return {"items": [serialize(r) for r in rows], "total": total, "page": page.page, "page_size": page.page_size}


@contextmanager
def domain_errors() -> Iterator[None]:
    try:
        yield
    except ApprovalError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    except (WorkflowConflict, InvalidTransition) as exc:
        raise HTTPException(409, str(exc)) from exc
    except (SimulationError, ToolError, ImportFormatError) as exc:
        raise HTTPException(400, str(exc)) from exc
