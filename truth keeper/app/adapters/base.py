"""Common adapter interface. One adapter per simulated system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, text

from app.core.models import CustomerRecord, System


@contextmanager
def sqlite_engine(path: Path) -> Iterator[Engine]:
    """Open a short-lived engine and always dispose it (Windows keeps file locks otherwise)."""
    if not Path(path).exists():
        raise FileNotFoundError(f"database not found: {path} (run the generator first)")
    engine = create_engine(f"sqlite:///{Path(path).as_posix()}")
    try:
        yield engine
    finally:
        engine.dispose()


class SystemAdapter(ABC):
    system: System
    filename: str

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.filename

    def _query(self, sql: str, **params) -> list[dict]:
        with sqlite_engine(self.db_path) as engine, engine.connect() as conn:
            return [dict(r._mapping) for r in conn.execute(text(sql), params)]

    @abstractmethod
    def read_all(self) -> list[CustomerRecord]:
        """Read every record into the common CustomerRecord model (normalised)."""
