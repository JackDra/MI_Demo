from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.init_app import build_backend


def build_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    happ = build_backend(engine=engine)
    return TestClient(happ.app)


def test_dashboard_and_scene_flow() -> None:
    client = build_client()
    empty_dashboard = client.get("/api/dashboard")
    assert empty_dashboard.status_code == 200
    assert empty_dashboard.json()["summary"]["region_count"] == 0

    imported = client.post("/api/demo-datasets/import-template")
    assert imported.status_code == 200

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["summary"]["region_count"] >= 4

    region_id = payload["regions"][0]["id"]
    scene = client.get(f"/api/regions/{region_id}/scene")
    assert scene.status_code == 200
    scene_payload = scene.json()
    assert scene_payload["river_sections"]

    gate = scene_payload["gates"][0]
    detail = client.get(f"/api/components/gate/{gate['id']}")
    assert detail.status_code == 200
    assert detail.json()["component_type"] == "gate"


def test_upload_rejects_empty_dataset() -> None:
    client = build_client()
    response = client.post("/api/demo-datasets/upload", json={"data": {"regions": []}})

    assert response.status_code == 400
