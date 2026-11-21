"""Alembic environment. Migrations run as the owner role (APP_MIGRATION_DATABASE_URL)."""

from sqlalchemy import engine_from_config, pool

from alembic import context
from procnav.core.config import get_settings
from procnav.core.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().app_migration_database_url.replace("%", "%%"))
target_metadata = Base.metadata

# LangGraph owns its checkpoint tables; never let autogenerate touch them.
EXTERNAL_TABLES = {"checkpoints", "checkpoint_blobs", "checkpoint_writes", "checkpoint_migrations"}


def include_object(obj, name, type_, reflected, compare_to):
    table = obj.table.name if type_ in ("index", "column") and hasattr(obj, "table") else name
    return table not in EXTERNAL_TABLES


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True, include_object=include_object
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
