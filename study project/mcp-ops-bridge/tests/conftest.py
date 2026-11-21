"""Shared fixtures: isolated temp SQLite DB per test session function."""

from __future__ import annotations

import pytest

from mock_itsm.db import init_db
from mock_itsm.seed import seed_db


@pytest.fixture()
def db_path(tmp_path):  # type: ignore[no-untyped-def]
    p = str(tmp_path / "test-itsm.db")
    init_db(p)
    seed_db(p)
    return p
