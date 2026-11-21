"""Developer helper: render the initial schema once from an empty temporary database."""
from pathlib import Path

from alembic.autogenerate import produce_migrations, render_python_code
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from services.api.db import Base

temporary = create_engine("sqlite://")
with temporary.connect() as connection:
    migration = produce_migrations(MigrationContext.configure(connection), Base.metadata)
    upgrade = render_python_code(migration.upgrade_ops)
    downgrade = render_python_code(migration.downgrade_ops)
path = Path("infra/migrations/versions/0001_foundation.py")
path.write_text(
    '"""Frozen initial ProductionLens schema. Future changes require a new revision."""\n'
    "from alembic import op\nimport sqlalchemy as sa\n\n"
    'revision = "0001"\ndown_revision = None\n\n'
    f"def upgrade():\n{upgrade}\n\ndef downgrade():\n{downgrade}\n",
    encoding="utf-8",
)
temporary.dispose()
print("Rendered initial migration; existing databases were not modified.")
