import os
from logging.config import fileConfig
from urllib.parse import urlparse

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context
from app.env import load_backend_env

load_backend_env()

config = context.config
database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or "sqlite:///./mi_demo.db"
if database_url.startswith("postgres://") or (
    database_url.startswith("postgresql://") and "+" not in database_url.split("://", 1)[0]
):
    parsed = urlparse(database_url)
    database_url = parsed._replace(scheme="postgresql+psycopg").geturl()
config.set_main_option("sqlalchemy.url", database_url)

from app import models  # noqa: E402,F401

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connect_args = {"prepare_threshold": None} if url.startswith("postgresql+psycopg://") else {}
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
