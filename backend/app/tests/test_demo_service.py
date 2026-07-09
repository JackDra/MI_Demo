from copy import deepcopy
from typing import Any

from sqlmodel import SQLModel, create_engine

from app.models import Severity
from app.services import DemoService


def sample_dataset() -> dict[str, Any]:
    return {
        "name": "Uploaded test dataset",
        "version": "1.0",
        "regions": [
            {
                "slug": "test-region",
                "name": "Test Region",
                "summary": "Upload-backed test region",
                "map_x": 0.5,
                "map_y": 0.5,
                "river_sections": [
                    {
                        "name": "Main Channel",
                        "start_x": 0,
                        "start_y": 0,
                        "end_x": 10,
                        "end_y": 0,
                        "flow_rate_ml_per_day": 70,
                        "target_flow_rate_ml_per_day": 100,
                        "water_level_m": 1.7,
                        "absorption_rate_percent": 4,
                        "evaporation_rate_mm_per_day": 6,
                        "display": {"max_water_level_m": 2},
                    }
                ],
                "gates": [
                    {
                        "name": "North Gate",
                        "asset_id": "G-001",
                        "x": 2,
                        "y": 1,
                        "opening_percent": 45,
                        "planned_action": "Inspect actuator",
                    }
                ],
                "sensors": [
                    {
                        "name": "Downstream Level Sensor",
                        "sensor_id": "S-001",
                        "sensor_type": "level",
                        "x": 4,
                        "y": 1,
                        "reading": 0.9,
                        "unit": "m",
                        "health": "critical",
                    }
                ],
                "reservoirs": [
                    {
                        "name": "Leeton Buffer Reservoir",
                        "x": 8,
                        "y": 3,
                        "capacity_ml": 1000,
                        "current_amount_ml": 150,
                        "percent_filled": 15,
                        "low_threshold_percent": 25,
                    },
                    {
                        "name": "Balanced Storage",
                        "x": 6,
                        "y": 2,
                        "capacity_ml": 900,
                        "current_amount_ml": 720,
                        "percent_filled": 80,
                        "low_threshold_percent": 25,
                    }
                ],
                "vegetation_zones": [],
            }
        ],
    }


def build_service() -> DemoService:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return DemoService(engine=engine)


def test_uploaded_dataset_generates_expected_notifications() -> None:
    service = build_service()
    dataset = service.upload_dataset_to_supabase(sample_dataset())

    assert dataset.id is not None
    notifications = service.list_notifications()
    titles = {notification.title for notification in notifications}

    assert "Leeton Buffer Reservoir below low-water threshold" in titles
    assert "Downstream Level Sensor health is critical" in titles
    assert any(notification.severity == Severity.red for notification in notifications)
    assert any(
        notification.generated_from == "gate_schedule_rule" for notification in notifications
    )


def test_dashboard_location_severity_rolls_up_region_notifications() -> None:
    service = build_service()
    payload = sample_dataset()
    yellow_region = deepcopy(payload["regions"][0])
    yellow_region.update(
        {
            "slug": "yellow-only-region",
            "name": "Yellow Only Region",
            "map_x": 0.75,
            "map_y": 0.45,
        }
    )
    yellow_region["river_sections"][0].update(
        {
            "name": "Yellow Region Channel",
            "flow_rate_ml_per_day": 100,
            "target_flow_rate_ml_per_day": 100,
        }
    )
    yellow_region["gates"][0].update(
        {
            "name": "Yellow Region Gate",
            "planned_action": "Inspect actuator",
        }
    )
    yellow_region["sensors"] = []
    yellow_region["reservoirs"] = []
    payload["regions"].append(yellow_region)

    service.upload_dataset_to_supabase(payload)
    dashboard = service.get_dashboard()
    location = next(
        item for item in dashboard.locations if item.label == "Yellow Region Channel"
    )

    assert location.severity == Severity.yellow


def test_component_detail_returns_related_metrics() -> None:
    service = build_service()
    service.upload_dataset_to_supabase(sample_dataset())
    dashboard = service.get_dashboard()
    region = dashboard.regions[0]
    assert region.id is not None
    scene = service.get_region_scene(region.id)
    assert scene is not None
    gate = scene.gates[0]
    assert gate.id is not None

    detail = service.get_component_detail("gate", gate.id)

    assert detail is not None
    assert detail.component_type == "gate"
    assert detail.related_metrics["opening_percent"] == gate.opening_percent


def test_river_section_percent_filled_falls_back_to_water_level() -> None:
    service = build_service()
    service.upload_dataset_to_supabase(sample_dataset())
    dashboard = service.get_dashboard()
    region = dashboard.regions[0]
    assert region.id is not None

    scene = service.get_region_scene(region.id)
    assert scene is not None
    river = scene.river_sections[0]
    assert river.id is not None

    detail = service.get_component_detail("river_section", river.id)

    assert detail is not None
    assert detail.related_metrics["percent_filled"] == 85


def test_river_section_percent_filled_is_imported_when_present() -> None:
    service = build_service()
    payload = sample_dataset()
    payload["regions"][0]["river_sections"][0]["percent_filled"] = 42

    service.upload_dataset_to_supabase(payload)
    dashboard = service.get_dashboard()
    region = dashboard.regions[0]
    assert region.id is not None

    scene = service.get_region_scene(region.id)
    assert scene is not None
    river = scene.river_sections[0]

    assert river.percent_filled == 42
    assert river.id is not None
    detail = service.get_component_detail("river_section", river.id)
    assert detail is not None
    assert detail.related_metrics["percent_filled"] == 42
