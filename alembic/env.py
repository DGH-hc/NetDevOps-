import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ------------------------------------------
# Add app directory to path for imports
# ------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# ------------------------------------------
# Import app database + models
# ------------------------------------------
from app.db.database import Base
from app.models.device import DeviceDB
from app.models.job import JobDB, JobAttempt, JobLog
from app.models.audit import AuditEvent
from app.models.snapshot import ConfigSnapshot
from app.core.config import settings

# ------------------------------------------
# Alembic Config Setup
# ------------------------------------------
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# ------------------------------------------
# Set target metadata for autogenerate
# ------------------------------------------
target_metadata = Base.metadata

# ------------------------------------------
# Replace sqlalchemy.url dynamically with .env
# ------------------------------------------
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL
)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ------------------------------------------
# Migration Runner
# ------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
