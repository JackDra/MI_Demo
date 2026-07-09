import os
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_app_engine
from app.services import DemoService
from app.supabase_service import SupabaseService

APP_NAME = "MI Demo API"
APP_VERSION = "0.1.0"


@dataclass
class HApp:
    app: FastAPI
    demo_service: DemoService
    supabase_service: SupabaseService


def _cors_origins() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def build_backend(engine: Any | None = None) -> HApp:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    demo_service = DemoService(engine=engine or create_app_engine())
    supabase_service = SupabaseService.from_env()
    demo_service.ensure_schema()
    happ = HApp(app=app, demo_service=demo_service, supabase_service=supabase_service)

    from app.routes import register_routes

    register_routes(happ)
    return happ
