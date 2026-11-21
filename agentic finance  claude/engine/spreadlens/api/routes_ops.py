"""Health, taxonomy, operational metrics and retention."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from spreadlens.api.deps import J
from spreadlens.config import METRICS_VERSION, PARSER_VERSION, RULESET_VERSION, TAXONOMY_VERSION, get_settings
from spreadlens.db import get_db
from spreadlens.models import DocumentVersion, MetricEvent, Workspace, utcnow
from spreadlens.security.auth import Principal, get_principal, require_member
from spreadlens.services.audit import audit
from spreadlens.storage.base import get_storage
from spreadlens.taxonomy.loader import load_taxonomy

router = APIRouter(prefix="/api", tags=["ops"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("select 1"))
    s = get_settings()
    return J({"ok": True, "agent_mode": s.agent_mode, "ocr_provider": s.ocr_provider, "storage": s.storage_backend,
              "versions": {"parser": PARSER_VERSION, "taxonomy": TAXONOMY_VERSION, "ruleset": RULESET_VERSION, "metrics": METRICS_VERSION},
              "processing": {"ocr": "local (RapidOCR, on this machine)" if s.ocr_provider == "local" else "disabled",
                             "models": "none (deterministic demo adapters)" if s.agent_mode == "demo" else "external via eve + Vercel AI Gateway"}})


@router.get("/taxonomy")
def taxonomy():
    t = load_taxonomy()
    return J({"version": t.version, "items": [{"code": i.code, "label": i.label, "statement": i.statement, "unit": i.unit,
                                               "period": i.period, "sign": i.sign, "section": i.section, "is_total": i.total,
                                               "synonyms": list(i.synonyms)} for i in t.items]})


@router.get("/workspaces/{ws_id}/metrics")
def ops_metrics(ws_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_member(db, p, ws_id)
    rows = db.execute(select(MetricEvent.name, func.count(), func.sum(MetricEvent.value), func.avg(MetricEvent.value))
                      .where(MetricEvent.workspace_id == ws_id).group_by(MetricEvent.name)).all()
    return J({name: {"count": n, "sum": float(s or 0), "avg": float(a or 0)} for name, n, s, a in rows})


@router.post("/workspaces/{ws_id}/retention/purge")
def purge(ws_id: str, p: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    """Delete document versions older than the workspace retention period (admin only)."""
    require_member(db, p, ws_id, "admin", "retention.purge")
    ws = db.get(Workspace, ws_id)
    cutoff = utcnow() - timedelta(days=ws.retention_days)  # type: ignore[union-attr]
    old = list(db.scalars(select(DocumentVersion).where(DocumentVersion.workspace_id == ws_id, DocumentVersion.created_at < cutoff)))
    storage = get_storage(get_settings())
    for dv in old:
        storage.delete(dv.storage_key)
        db.delete(dv)
    audit(db, ws_id, p.id, "retention.purge", "workspace", ws_id, details={"deleted": len(old), "cutoff": cutoff.isoformat()})
    return J({"deleted": len(old)})
