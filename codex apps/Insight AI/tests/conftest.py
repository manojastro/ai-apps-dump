import os
import secrets
import tempfile

import pytest

# Tests never write into the user's running application database.
_directory = tempfile.TemporaryDirectory(prefix="productionlens-tests-")
os.environ["PRODUCTIONLENS_DATA"] = _directory.name
os.environ["DATABASE_URL"] = "sqlite:///" + _directory.name.replace("\\", "/") + "/test.db"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from services.api.auth import attempts, passwords
    from services.api.db import Base, Session, User, engine
    from services.api.main import app

    attempts.clear()
    Base.metadata.create_all(engine)
    username = "test-" + secrets.token_hex(5)
    password = secrets.token_urlsafe(20)
    with Session() as db:
        db.add(User(username=username, password_hash=passwords.hash(password), role="administrator"))
        db.commit()
    with TestClient(app) as instance:
        response = instance.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        instance.headers["x-csrf-token"] = response.json()["csrf"]
        yield instance


def pytest_sessionfinish(session, exitstatus):
    from services.api.db import engine

    engine.dispose()
    _directory.cleanup()
