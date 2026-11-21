"""File storage adapters. Keys are always prefixed by workspace id (tenant isolation)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from spreadlens.config import Settings

_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-./]{0,400}$")


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


def make_key(workspace_id: str, *parts: str) -> str:
    key = "/".join([workspace_id, *parts])
    if not _SAFE.match(key) or ".." in key:
        raise ValueError("unsafe storage key")
    return key


def key_belongs_to(key: str, workspace_id: str) -> bool:
    return key.startswith(workspace_id + "/")


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not _SAFE.match(key) or ".." in key:
            raise ValueError("unsafe storage key")
        p = (self.root / key).resolve()
        if self.root not in p.parents:
            raise ValueError("path escapes storage root")
        return p

    def put(self, key: str, data: bytes, content_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(p)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class GcsStorage:
    """Object-storage adapter for deployment (Google Cloud Storage, ADC credentials)."""

    def __init__(self, bucket: str) -> None:
        from google.cloud import storage  # optional extra: uv sync --extra gcs

        self.bucket = storage.Client().bucket(bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.bucket.blob(key).upload_from_string(data, content_type=content_type)

    def get(self, key: str) -> bytes:
        return self.bucket.blob(key).download_as_bytes()

    def delete(self, key: str) -> None:
        blob = self.bucket.blob(key)
        if blob.exists():
            blob.delete()

    def exists(self, key: str) -> bool:
        return self.bucket.blob(key).exists()


_storage: Storage | None = None


def get_storage(settings: Settings) -> Storage:
    global _storage
    if _storage is None:
        if settings.storage_backend == "gcs":
            if not settings.gcs_bucket:
                raise RuntimeError("SPREADLENS_GCS_BUCKET is required for gcs storage")
            _storage = GcsStorage(settings.gcs_bucket)
        else:
            _storage = LocalStorage(settings.storage_root)
    return _storage


def reset_storage() -> None:
    global _storage
    _storage = None
