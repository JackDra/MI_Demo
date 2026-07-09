import os
from urllib.parse import urlparse

from sqlalchemy.engine import Engine
from sqlmodel import create_engine

from app.env import load_backend_env


def build_database_url() -> str:
    load_backend_env()
    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if database_url:
        if database_url.startswith("postgres://") or (
            database_url.startswith("postgresql://") and "+" not in database_url.split("://", 1)[0]
        ):
            parsed = urlparse(database_url)
            return parsed._replace(scheme="postgresql+psycopg").geturl()
        return database_url
    return "sqlite:///./mi_demo.db"


def create_app_engine() -> Engine:
    database_url = build_database_url()
    connect_args: dict[str, object] = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    if database_url.startswith("postgresql+psycopg://"):
        connect_args = {"prepare_threshold": None}
    return create_engine(
        database_url,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        connect_args=connect_args,
        pool_pre_ping=not database_url.startswith("sqlite"),
        pool_recycle=300,
    )
