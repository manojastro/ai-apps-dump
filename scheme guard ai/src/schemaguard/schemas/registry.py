"""Schema registry clients behind one interface.

* FileSchemaRegistry: versions stored as <dir>/<subject>/<n>.avsc. Default, offline.
* ConfluentSchemaRegistry: Confluent Schema Registry REST API (GET/POST /subjects/...).
  Read paths are used by the poller; `register` is only used to seed the demo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@dataclass(frozen=True)
class SchemaVersion:
    subject: str
    version: int
    schema: dict[str, Any]


def subject_for_topic(topic: str) -> str:
    return f"{topic}-value"


def topic_for_subject(subject: str) -> str:
    return subject.removesuffix("-value")


class SchemaRegistry(Protocol):
    def subjects(self) -> list[str]: ...
    def versions(self, subject: str) -> list[int]: ...
    def get(self, subject: str, version: int | str = "latest") -> SchemaVersion: ...
    def register(self, subject: str, schema: dict[str, Any]) -> int: ...


class RegistryUnavailable(RuntimeError):
    pass


class FileSchemaRegistry:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def subjects(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())

    def versions(self, subject: str) -> list[int]:
        d = self.root / subject
        return sorted(int(p.stem) for p in d.glob("*.avsc")) if d.exists() else []

    def get(self, subject: str, version: int | str = "latest") -> SchemaVersion:
        vs = self.versions(subject)
        if not vs:
            raise KeyError(f"subject {subject!r} not found")
        v = vs[-1] if version == "latest" else int(version)
        if v not in vs:
            raise KeyError(f"{subject} version {v} not found")
        schema = json.loads((self.root / subject / f"{v}.avsc").read_text(encoding="utf-8"))
        return SchemaVersion(subject, v, schema)

    def register(self, subject: str, schema: dict[str, Any]) -> int:
        vs = self.versions(subject)
        if vs:
            latest = self.get(subject).schema
            if json.dumps(latest, sort_keys=True) == json.dumps(schema, sort_keys=True):
                return vs[-1]
        v = (vs[-1] + 1) if vs else 1
        d = self.root / subject
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{v}.avsc").write_text(json.dumps(schema, indent=2), encoding="utf-8")
        return v


class ConfluentSchemaRegistry:
    def __init__(self, url: str, timeout_s: float = 5.0):
        self.url = url.rstrip("/")
        self.client = httpx.Client(timeout=timeout_s)

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        wait=wait_exponential(multiplier=0.5, max=8),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(self, path: str) -> Any:
        r = self.client.get(f"{self.url}{path}")
        if r.status_code == 404:
            raise KeyError(path)
        r.raise_for_status()
        return r.json()

    def _call(self, path: str) -> Any:
        try:
            return self._get(path)
        except httpx.TransportError as exc:
            raise RegistryUnavailable(f"schema registry unreachable at {self.url}: {exc}") from exc

    def subjects(self) -> list[str]:
        return sorted(self._call("/subjects"))

    def versions(self, subject: str) -> list[int]:
        return sorted(self._call(f"/subjects/{subject}/versions"))

    def get(self, subject: str, version: int | str = "latest") -> SchemaVersion:
        data = self._call(f"/subjects/{subject}/versions/{version}")
        return SchemaVersion(subject, int(data["version"]), json.loads(data["schema"]))

    def register(self, subject: str, schema: dict[str, Any]) -> int:
        r = self.client.post(
            f"{self.url}/subjects/{subject}/versions",
            json={"schema": json.dumps(schema), "schemaType": "AVRO"},
            headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        )
        r.raise_for_status()
        return int(self.get(subject).version)


def make_registry(registry_url: str, registry_dir: Path) -> SchemaRegistry:
    return ConfluentSchemaRegistry(registry_url) if registry_url else FileSchemaRegistry(registry_dir)


def seed_registry(registry: SchemaRegistry, avro_dir: Path) -> dict[str, int]:
    """Register the pipeline's v1 schemas (idempotent)."""
    out = {}
    for p in sorted(Path(avro_dir).glob("*.avsc")):
        topic = p.name.removesuffix(".avsc")
        out[subject_for_topic(topic)] = registry.register(
            subject_for_topic(topic), json.loads(p.read_text(encoding="utf-8"))
        )
    return out
