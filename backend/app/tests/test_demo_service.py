from sqlmodel import SQLModel, create_engine

from app.models import Severity
from app.services import DemoService


def build_service() -> DemoService:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return DemoService(engine=engine)


def test_seed_dataset_generates_expected_notifications() -> None:
    service = build_service()
    dataset = service.import_template_dataset()

    assert dataset.id is not None
    notifications = service.list_notifications()
    titles = {notification.title for notification in notifications}

    assert "Leeton Buffer Reservoir below low-water threshold" in titles
    assert "Downstream Level Sensor health is critical" in titles
    assert any(notification.severity == Severity.red for notification in notifications)
    assert any(
        notification.generated_from == "gate_schedule_rule" for notification in notifications
    )


def test_component_detail_returns_related_metrics() -> None:
    service = build_service()
    service.import_template_dataset()
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
