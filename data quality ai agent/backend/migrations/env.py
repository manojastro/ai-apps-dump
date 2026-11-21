from alembic import context
from app.config import Settings
from app.db.models import Base
from sqlalchemy import create_engine

config = context.config
settings = Settings()
settings.prepare_paths()
url = config.attributes.get("database_url", settings.database_url)
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url)
    with engine.connect() as connection:
        if connection.dialect.name == "postgresql":
            connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
            connection.commit()
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
