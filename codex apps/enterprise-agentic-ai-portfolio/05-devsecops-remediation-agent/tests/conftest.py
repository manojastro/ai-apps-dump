from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(tmp_path / "test.db", tmp_path / "workspaces")
    with TestClient(app) as test_client:
        yield test_client
