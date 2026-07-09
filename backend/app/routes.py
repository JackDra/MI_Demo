from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.init_app import APP_NAME, APP_VERSION, HApp
from app.models import (
    ComponentDetail,
    DashboardPayload,
    DemoDataset,
    DemoDatasetUpload,
    HealthzResponse,
    Notification,
    Region,
    ScenePayload,
    Severity,
    VersionResponse,
)
from app.supabase_service import MapAsset


def register_routes(happ: HApp) -> None:
    @happ.app.get("/healthz")
    def healthz() -> HealthzResponse:
        return HealthzResponse(status="ok")

    @happ.app.get("/readyz")
    def readyz() -> HealthzResponse:
        try:
            happ.demo_service.check_database()
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable",
            ) from exc
        return HealthzResponse(status="ok")

    @happ.app.get("/api/version")
    def version() -> VersionResponse:
        return VersionResponse(name=APP_NAME, version=APP_VERSION)

    @happ.app.get("/api/dashboard")
    def dashboard() -> DashboardPayload:
        return happ.demo_service.get_dashboard()

    @happ.app.get("/api/assets/topographic-map")
    def topographic_map_asset() -> MapAsset:
        map_path = (
            Path(__file__).resolve().parents[2]
            / "frontend"
            / "static"
            / "maps"
            / "murrumbidgee-opentopomap-z10.png"
        )
        try:
            return happ.supabase_service.ensure_topographic_map_asset(map_path)
        except (FileNotFoundError, RuntimeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

    @happ.app.get("/api/regions/{region_id}")
    def get_region(region_id: int) -> Region:
        region = happ.demo_service.get_region(region_id)
        if region is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
        return region

    @happ.app.get("/api/regions/{region_id}/scene")
    def get_region_scene(region_id: int) -> ScenePayload:
        scene = happ.demo_service.get_region_scene(region_id)
        if scene is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
        return scene

    @happ.app.get("/api/components/{component_type}/{component_id}")
    def get_component(component_type: str, component_id: int) -> ComponentDetail:
        detail = happ.demo_service.get_component_detail(component_type, component_id)
        if detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found",
            )
        return detail

    @happ.app.get("/api/notifications")
    def list_notifications(
        severity: Severity | None = Query(default=None),
        source_entity_type: str | None = None,
    ) -> list[Notification]:
        return happ.demo_service.list_notifications(
            severity=severity,
            source_entity_type=source_entity_type,
        )

    @happ.app.post("/api/demo-datasets/upload")
    def upload_dataset(payload: DemoDatasetUpload) -> DemoDataset:
        data = dict(payload.data)
        if payload.name is not None:
            data["name"] = payload.name
        if payload.version is not None:
            data["version"] = payload.version
        if payload.description is not None:
            data["description"] = payload.description
        try:
            return happ.demo_service.upload_dataset_to_supabase(data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @happ.app.post("/api/demo-datasets/{dataset_id}/activate")
    def activate_dataset(dataset_id: int) -> DemoDataset:
        dataset = happ.demo_service.activate_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset
