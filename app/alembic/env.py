"""
Alembic env.py scaffolded to use app.data.models.Base.metadata
Reads DATABASE_URL from app/.env if present.
"""
from __future__ import with_statement
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ensure app package path is importable
HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.abspath(os.path.join(HERE, '..'))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Optionally load .env from app directory
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))
except Exception:
    pass

# If DATABASE_URL env var exists, set it into config
db_url = os.getenv('DATABASE_URL')
if db_url:
    config.set_main_option('sqlalchemy.url', db_url)

# Import your metadata object here
# for 'autogenerate' support
try:
    from data.models import Base
    target_metadata = Base.metadata
except Exception as e:
    # Fallback if import fails
    target_metadata = None
    print(f"Warning importing models for alembic: {e}")

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
