from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Severity(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class NotificationStatus(str, Enum):
    active = "active"
    dismissed = "dismissed"


class GateState(str, Enum):
    open = "open"
    closed = "closed"
    partial = "partial"
    scheduled = "scheduled"
    maintenance = "maintenance"


class SensorHealth(str, Enum):
    normal = "normal"
    warning = "warning"
    critical = "critical"
    offline = "offline"


class DemoDataset(SQLModel, table=True):
    __tablename__ = "demo_dataset"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    version: str
    description: str | None = None
    raw_json: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    is_active: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    activated_at: datetime | None = Field(default=None, nullable=True)


class Region(SQLModel, table=True):
    __tablename__ = "region"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    slug: str = Field(index=True)
    name: str
    summary: str
    map_x: float
    map_y: float
    gps_lat: float | None = None
    gps_lng: float | None = None
    display: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class RiverSection(SQLModel, table=True):
    __tablename__ = "river_section"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    region_id: int = Field(foreign_key="region.id", index=True)
    name: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    flow_rate_ml_per_day: float
    target_flow_rate_ml_per_day: float
    water_level_m: float
    absorption_rate_percent: float
    evaporation_rate_mm_per_day: float
    display: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class Gate(SQLModel, table=True):
    __tablename__ = "gate"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    region_id: int = Field(foreign_key="region.id", index=True)
    name: str
    asset_id: str = Field(index=True)
    x: float
    y: float
    state: GateState = Field(default=GateState.partial)
    opening_percent: float
    planned_action: str | None = None
    planned_for: datetime | None = None
    model: str | None = None
    next_inspection_at: datetime | None = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )


class Sensor(SQLModel, table=True):
    __tablename__ = "sensor"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    region_id: int = Field(foreign_key="region.id", index=True)
    name: str
    sensor_id: str = Field(index=True)
    sensor_type: str
    x: float
    y: float
    reading: float
    unit: str
    health: SensorHealth = Field(default=SensorHealth.normal)
    last_updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    calibration_due_at: datetime | None = None
    next_inspection_at: datetime | None = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )


class Reservoir(SQLModel, table=True):
    __tablename__ = "reservoir"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    region_id: int = Field(foreign_key="region.id", index=True)
    name: str
    x: float
    y: float
    capacity_ml: float
    current_amount_ml: float
    percent_filled: float
    low_threshold_percent: float = 25.0
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )


class VegetationZone(SQLModel, table=True):
    __tablename__ = "vegetation_zone"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    region_id: int = Field(foreign_key="region.id", index=True)
    name: str
    x: float
    y: float
    risk_level: Severity = Field(default=Severity.green)
    last_inspection_at: datetime | None = None
    next_inspection_at: datetime | None = None
    notes: str = ""


class Notification(SQLModel, table=True):
    __tablename__ = "notification"

    id: int | None = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="demo_dataset.id", index=True)
    region_id: int | None = Field(default=None, foreign_key="region.id", index=True)
    title: str
    contents: str
    severity: Severity = Field(index=True)
    status: NotificationStatus = Field(default=NotificationStatus.active, index=True)
    generated_from: str
    source_entity_type: str
    source_entity_id: int | None = None
    map_x: float
    map_y: float
    prediction_horizon: str | None = None
    prediction_method: str | None = None
    predicted_for: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)


class HealthzResponse(SQLModel):
    status: str


class VersionResponse(SQLModel):
    name: str
    version: str


class DemoDatasetUpload(SQLModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    data: dict[str, Any]


class DashboardSummary(SQLModel):
    active_dataset_id: int | None
    region_count: int
    notification_count: int
    red_count: int
    yellow_count: int
    green_count: int


class DashboardPayload(SQLModel):
    dataset: DemoDataset | None
    summary: DashboardSummary
    regions: list[Region]
    notifications: list[Notification]


class ScenePayload(SQLModel):
    region: Region
    notifications: list[Notification]
    river_sections: list[RiverSection]
    gates: list[Gate]
    sensors: list[Sensor]
    reservoirs: list[Reservoir]
    vegetation_zones: list[VegetationZone]


class ComponentDetail(SQLModel):
    component_type: str
    component: dict[str, Any]
    notifications: list[Notification]
    related_metrics: dict[str, Any]
