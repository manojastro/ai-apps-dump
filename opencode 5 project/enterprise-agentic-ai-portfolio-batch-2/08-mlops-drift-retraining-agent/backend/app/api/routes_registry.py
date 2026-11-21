"""Registry listing and KPI endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import get_session
from backend.app.repositories.decision_repo import AuditRepository, KpiRepository
from backend.app.services.kpi import snapshot_kpis

router = APIRouter(prefix="/api/v1", tags=["registry"])


@router.get("/registry")
def get_registry(session: Session = Depends(get_session)) -> dict:
    from backend.app.services.registry import registry_service

    rows = registry_service.list_all(session)
    return {
        "models": [
            {
                "version": r.version,
                "status": r.status,
                "kind": r.kind,
                "algorithm": r.algorithm,
                "metrics": r.metrics,
                "thresholds": r.thresholds,
                "notes": r.notes,
                "created_at": str(r.created_at),
            }
            for r in rows
        ]
    }


@router.get("/kpis")
def get_kpis(session: Session = Depends(get_session)) -> dict:
    return snapshot_kpis(session)


@router.get("/audit/tool-calls")
def get_tool_calls(session: Session = Depends(get_session)) -> dict:
    rows = AuditRepository.list_recent(session)
    return {
        "tool_calls": [
            {
                "id": r.id,
                "tool_name": r.tool_name,
                "permission": r.permission,
                "success": r.success,
                "error": r.error,
                "duration_ms": r.duration_ms,
                "created_at": str(r.created_at),
            }
            for r in rows
        ]
    }


@router.get("/kpi-snapshots")
def list_kpi_snapshots(session: Session = Depends(get_session)) -> dict:
    from sqlalchemy import select

    from backend.app.models.entities import KpiSnapshot

    rows = list(session.scalars(select(KpiSnapshot).order_by(KpiSnapshot.id.desc()).limit(20)))
    KpiRepository.latest(session)
    return {
        "snapshots": [
            {"id": r.id, "captured_at": str(r.captured_at), "payload": r.payload} for r in rows
        ]
    }
