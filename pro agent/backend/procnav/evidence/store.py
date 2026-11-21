"""Evidence files (redacted screenshots, page text, receipts, exports) under tenant/run folders.

Files are only served through the authorized evidence API; the storage path is never exposed.
Screenshots can still contain sensitive business data and follow the retention policy.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.models import EvidenceArtifact


def _root() -> Path:
    root = Path(get_settings().evidence_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save(
    session: Session,
    *,
    tenant_id: uuid.UUID,
    run_id: uuid.UUID | None,
    kind: str,
    label: str,
    data: bytes,
    content_type: str,
    ext: str,
    redacted: bool = True,
) -> EvidenceArtifact:
    artifact_id = uuid.uuid4()
    rel = Path(str(tenant_id)) / (str(run_id) if run_id else "_tenant") / f"{artifact_id}.{ext}"
    path = _root() / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    s = get_settings()
    art = EvidenceArtifact(
        id=artifact_id,
        tenant_id=tenant_id,
        run_id=run_id,
        kind=kind,
        label=label[:200],
        storage_path=str(rel).replace("\\", "/"),
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        content_type=content_type,
        redacted=redacted,
        retention_until=datetime.now(UTC) + timedelta(days=s.evidence_retention_days),
    )
    session.add(art)
    session.flush()
    return art


def read(art: EvidenceArtifact) -> bytes:
    path = (_root() / art.storage_path).resolve()
    if _root().resolve() not in path.parents:
        raise PermissionError("evidence path escapes the evidence root")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != art.sha256:
        raise ValueError("evidence integrity check failed")
    return data


def purge_expired(session: Session, now: datetime | None = None) -> int:
    """Delete expired evidence for the session's tenant (RLS limits scope)."""
    now = now or datetime.now(UTC)
    rows = session.scalars(select(EvidenceArtifact).where(EvidenceArtifact.retention_until < now)).all()
    for art in rows:
        p = _root() / art.storage_path
        if p.exists():
            p.unlink()
        session.delete(art)
    return len(rows)
