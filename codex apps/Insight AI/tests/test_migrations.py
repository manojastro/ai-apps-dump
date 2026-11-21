from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from services.api import db


def test_frozen_migration_matches_models_and_downgrades(monkeypatch):
    temporary = create_engine("sqlite://")
    monkeypatch.setattr(db, "engine", temporary)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    with temporary.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), db.Base.metadata) == []
    command.downgrade(config, "base")
    assert inspect(temporary).get_table_names() == ["alembic_version"]
    temporary.dispose()
