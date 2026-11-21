"""Persist typed agent artifacts (content-addressed, validated against pydantic contracts)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from spreadlens.models import Artifact


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()


def save_artifact(db: Session, workspace_id: str, run_id: str | None, artifact: BaseModel, produced_by: str) -> Artifact:
    payload = artifact.model_dump(mode="json")
    a = Artifact(workspace_id=workspace_id, run_id=run_id, artifact_type=getattr(artifact, "artifact_type", type(artifact).__name__),
                 schema_version=getattr(artifact, "schema_version", "1"), produced_by=produced_by,
                 content_hash=content_hash(payload), payload=payload)
    db.add(a)
    db.flush()
    return a


def save_raw_artifact(db: Session, workspace_id: str, run_id: str | None, artifact_type: str, payload: dict,
                      produced_by: str, schema_version: str = "1") -> Artifact:
    a = Artifact(workspace_id=workspace_id, run_id=run_id, artifact_type=artifact_type, schema_version=schema_version,
                 produced_by=produced_by, content_hash=content_hash(payload), payload=payload)
    db.add(a)
    db.flush()
    return a
