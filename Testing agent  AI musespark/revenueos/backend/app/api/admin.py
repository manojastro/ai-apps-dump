"""Admin endpoints: audit log, model registry, data health."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import Db, Pagination, require_roles
from app.api.schemas import AuditRow, DataHealth, ModelRow, Page
from app.db.models import CopilotAudit, DataQualityRun, LoadReject, ModelVersion, User

router = APIRouter(prefix="/admin", tags=["admin"])
AdminOnly = Annotated[User, Depends(require_roles("admin"))]
AdminOrRevOps = Annotated[User, Depends(require_roles("admin", "revops"))]


@router.get("/audit", response_model=Page[AuditRow])
def audit(db: Db, _: AdminOnly, paging: Pagination) -> Page[AuditRow]:
    total = db.scalar(select(func.count()).select_from(CopilotAudit)) or 0
    rows = db.execute(
        select(CopilotAudit, User.email).join(User, CopilotAudit.user_id == User.id)
        .order_by(CopilotAudit.created_at.desc(), CopilotAudit.id.desc())
        .limit(paging.page_size).offset((paging.page - 1) * paging.page_size)
    ).all()
    items = [AuditRow(
        id=r.id, user_id=r.user_id, user_email=email, question=r.question,
        tools_called=r.tools_called_json, answer=r.answer, cited_sources=r.cited_sources_json,
        created_at=r.created_at,
    ) for r, email in rows]
    return Page(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/models", response_model=list[ModelRow])
def models(db: Db, _: AdminOrRevOps) -> list[ModelRow]:
    rows = db.scalars(
        select(ModelVersion).order_by(ModelVersion.trained_at.desc())
    ).all()
    return [ModelRow(
        model_name=r.model_name, version=r.version, algorithm=r.algorithm,
        trained_at=r.trained_at, is_active=r.is_active, metrics=r.metrics_json,
    ) for r in rows]


@router.get("/data-quality", response_model=DataHealth)
def data_quality(db: Db, _: AdminOrRevOps) -> DataHealth:
    latest = db.scalars(select(DataQualityRun).order_by(DataQualityRun.run_at.desc())).first()
    rejects = db.scalar(select(func.count()).select_from(LoadReject)) or 0
    results = latest.results_json if latest else {}
    return DataHealth(
        run_at=latest.run_at if latest else None, summary=results.get("summary", {}),
        load_rejects=rejects, row_counts=results.get("row_counts", {}),
    )
