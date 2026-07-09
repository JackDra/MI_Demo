from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, col, select

from app.models import (
    ComponentDetail,
    DashboardLocation,
    DashboardPayload,
    DashboardSummary,
    DemoDataset,
    Gate,
    Notification,
    NotificationStatus,
    Region,
    Reservoir,
    RiverSection,
    ScenePayload,
    Sensor,
    SensorHealth,
    Severity,
    VegetationZone,
)


def parse_datetime(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise ValueError(f"Unsupported datetime value: {value!r}")


def now_utc() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class DemoService:
    engine: Engine

    def ensure_schema(self) -> None:
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(self.engine)
        self._ensure_optional_columns()

    def check_database(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("select 1"))

    def upload_dataset_to_supabase(self, payload: dict[str, Any]) -> DemoDataset:
        name = str(payload.get("name") or "Uploaded Demo Dataset")
        version = str(payload.get("version") or "0.1")
        description = payload.get("description")
        regions = payload.get("regions")
        if not isinstance(regions, list) or not regions:
            raise ValueError("Dataset must contain a non-empty 'regions' list")

        with Session(self.engine) as session:
            for dataset in session.exec(select(DemoDataset).where(DemoDataset.is_active)).all():
                dataset.is_active = False
                session.add(dataset)

            dataset = DemoDataset(
                name=name,
                version=version,
                description=str(description) if description is not None else None,
                raw_json=payload,
                is_active=True,
                activated_at=now_utc(),
            )
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            if dataset.id is None:
                raise RuntimeError("Dataset id was not generated")
            self._upload_data_model_instances(session, dataset.id, payload)
            session.commit()
            self._regenerate_notifications(session, dataset.id)
            session.commit()
            session.refresh(dataset)
            return dataset

    def activate_dataset(self, dataset_id: int) -> DemoDataset | None:
        with Session(self.engine) as session:
            target = session.get(DemoDataset, dataset_id)
            if target is None:
                return None
            for dataset in session.exec(select(DemoDataset).where(DemoDataset.is_active)).all():
                dataset.is_active = False
                session.add(dataset)
            target.is_active = True
            target.activated_at = now_utc()
            session.add(target)
            self._regenerate_notifications(session, dataset_id)
            session.commit()
            session.refresh(target)
            return target

    def get_active_dataset(self, session: Session) -> DemoDataset | None:
        return session.exec(select(DemoDataset).where(DemoDataset.is_active)).first()

    def get_dashboard(self) -> DashboardPayload:
        with Session(self.engine) as session:
            dataset = self.get_active_dataset(session)
            if dataset is None or dataset.id is None:
                return DashboardPayload(
                    dataset=None,
                    summary=DashboardSummary(
                        active_dataset_id=None,
                        region_count=0,
                        location_count=0,
                        notification_count=0,
                        red_count=0,
                        yellow_count=0,
                        green_count=0,
                    ),
                    regions=[],
                    locations=[],
                    notifications=[],
                )

            regions = list(
                session.exec(select(Region).where(Region.dataset_id == dataset.id)).all()
            )
            notifications = self._list_notifications(session, dataset.id)
            locations = self._dashboard_locations(session, dataset.id, regions, notifications)
            summary = DashboardSummary(
                active_dataset_id=dataset.id,
                region_count=len(regions),
                location_count=len(locations),
                notification_count=len(notifications),
                red_count=sum(1 for item in notifications if item.severity == Severity.red),
                yellow_count=sum(1 for item in notifications if item.severity == Severity.yellow),
                green_count=sum(1 for item in notifications if item.severity == Severity.green),
            )
            return DashboardPayload(
                dataset=dataset,
                summary=summary,
                regions=regions,
                locations=locations,
                notifications=notifications,
            )

    def get_region(self, region_id: int) -> Region | None:
        with Session(self.engine) as session:
            return session.get(Region, region_id)

    def get_region_scene(self, region_id: int) -> ScenePayload | None:
        with Session(self.engine) as session:
            region = session.get(Region, region_id)
            if region is None:
                return None
            notifications = list(
                session.exec(
                    select(Notification)
                    .where(Notification.region_id == region_id)
                    .where(Notification.status == NotificationStatus.active)
                    .order_by(col(Notification.created_at).desc())
                ).all()
            )
            return ScenePayload(
                region=region,
                notifications=notifications,
                river_sections=list(
                    session.exec(
                        select(RiverSection).where(RiverSection.region_id == region_id)
                    ).all()
                ),
                gates=list(session.exec(select(Gate).where(Gate.region_id == region_id)).all()),
                sensors=list(
                    session.exec(select(Sensor).where(Sensor.region_id == region_id)).all()
                ),
                reservoirs=list(
                    session.exec(select(Reservoir).where(Reservoir.region_id == region_id)).all()
                ),
                vegetation_zones=list(
                    session.exec(
                        select(VegetationZone).where(VegetationZone.region_id == region_id)
                    ).all()
                ),
            )

    def list_notifications(
        self,
        severity: Severity | None = None,
        source_entity_type: str | None = None,
    ) -> list[Notification]:
        with Session(self.engine) as session:
            dataset = self.get_active_dataset(session)
            if dataset is None or dataset.id is None:
                return []
            statement = (
                select(Notification)
                .where(Notification.dataset_id == dataset.id)
                .where(Notification.status == NotificationStatus.active)
            )
            if severity is not None:
                statement = statement.where(Notification.severity == severity)
            if source_entity_type:
                statement = statement.where(Notification.source_entity_type == source_entity_type)
            statement = statement.order_by(col(Notification.created_at).desc())
            return list(session.exec(statement).all())

    def get_component_detail(
        self,
        component_type: str,
        component_id: int,
    ) -> ComponentDetail | None:
        component_type = component_type.lower()
        model_by_type = {
            "river": RiverSection,
            "river_section": RiverSection,
            "water": RiverSection,
            "gate": Gate,
            "sensor": Sensor,
            "reservoir": Reservoir,
            "vegetation": VegetationZone,
            "vegetation_zone": VegetationZone,
        }
        model = model_by_type.get(component_type)
        if model is None:
            return None
        with Session(self.engine) as session:
            component = session.get(model, component_id)
            if component is None:
                return None
            canonical_type = (
                "river_section" if model is RiverSection else str(model.__tablename__)
            )
            notifications = list(
                session.exec(
                    select(Notification)
                    .where(Notification.source_entity_type == canonical_type)
                    .where(Notification.source_entity_id == component_id)
                    .where(Notification.status == NotificationStatus.active)
                ).all()
            )
            return ComponentDetail(
                component_type=canonical_type,
                component=component.model_dump(mode="json"),
                notifications=notifications,
                related_metrics=self._component_metrics(canonical_type, component),
            )

    def _upload_data_model_instances(
        self,
        session: Session,
        dataset_id: int,
        payload: dict[str, Any],
    ) -> None:
        """Convert imported JSON into SQLModel instances and persist them.

        The configured SQLAlchemy engine points at Supabase Postgres when
        DATABASE_URL or SUPABASE_DB_URL is set to the Supabase DSN. Local
        SQLite uses the same method for development.
        """
        for region_payload in payload["regions"]:
            region = Region(
                dataset_id=dataset_id,
                slug=str(region_payload["slug"]),
                name=str(region_payload["name"]),
                summary=str(region_payload.get("summary", "")),
                map_x=float(region_payload["map_x"]),
                map_y=float(region_payload["map_y"]),
                gps_lat=region_payload.get("gps_lat"),
                gps_lng=region_payload.get("gps_lng"),
                display=dict(region_payload.get("display") or {}),
            )
            session.add(region)
            session.commit()
            session.refresh(region)
            if region.id is None:
                raise RuntimeError("Region id was not generated")

            for item in region_payload.get("river_sections", []):
                session.add(
                    RiverSection(
                        dataset_id=dataset_id,
                        region_id=region.id,
                        name=str(item["name"]),
                        start_x=float(item["start_x"]),
                        start_y=float(item["start_y"]),
                        end_x=float(item["end_x"]),
                        end_y=float(item["end_y"]),
                        flow_rate_ml_per_day=float(item["flow_rate_ml_per_day"]),
                        target_flow_rate_ml_per_day=float(item["target_flow_rate_ml_per_day"]),
                        water_level_m=float(item["water_level_m"]),
                        percent_filled=(
                            float(item["percent_filled"])
                            if item.get("percent_filled") is not None
                            else None
                        ),
                        absorption_rate_percent=float(item["absorption_rate_percent"]),
                        evaporation_rate_mm_per_day=float(item["evaporation_rate_mm_per_day"]),
                        display=dict(item.get("display") or {}),
                    )
                )
            for item in region_payload.get("gates", []):
                session.add(
                    Gate(
                        dataset_id=dataset_id,
                        region_id=region.id,
                        name=str(item["name"]),
                        asset_id=str(item["asset_id"]),
                        x=float(item["x"]),
                        y=float(item["y"]),
                        state=item.get("state", "partial"),
                        opening_percent=float(item["opening_percent"]),
                        planned_action=item.get("planned_action"),
                        planned_for=parse_datetime(item.get("planned_for")),
                        model=item.get("model"),
                        next_inspection_at=parse_datetime(item.get("next_inspection_at")),
                        metadata_json=dict(item.get("metadata_json") or {}),
                    )
                )
            for item in region_payload.get("sensors", []):
                session.add(
                    Sensor(
                        dataset_id=dataset_id,
                        region_id=region.id,
                        name=str(item["name"]),
                        sensor_id=str(item["sensor_id"]),
                        sensor_type=str(item["sensor_type"]),
                        x=float(item["x"]),
                        y=float(item["y"]),
                        reading=float(item["reading"]),
                        unit=str(item["unit"]),
                        health=item.get("health", "normal"),
                        last_updated_at=parse_datetime(item.get("last_updated_at")) or now_utc(),
                        calibration_due_at=parse_datetime(item.get("calibration_due_at")),
                        next_inspection_at=parse_datetime(item.get("next_inspection_at")),
                        metadata_json=dict(item.get("metadata_json") or {}),
                    )
                )
            for item in region_payload.get("reservoirs", []):
                session.add(
                    Reservoir(
                        dataset_id=dataset_id,
                        region_id=region.id,
                        name=str(item["name"]),
                        x=float(item["x"]),
                        y=float(item["y"]),
                        capacity_ml=float(item["capacity_ml"]),
                        current_amount_ml=float(item["current_amount_ml"]),
                        percent_filled=float(item["percent_filled"]),
                        low_threshold_percent=float(item.get("low_threshold_percent", 25)),
                        metadata_json=dict(item.get("metadata_json") or {}),
                    )
                )
            for item in region_payload.get("vegetation_zones", []):
                session.add(
                    VegetationZone(
                        dataset_id=dataset_id,
                        region_id=region.id,
                        name=str(item["name"]),
                        x=float(item["x"]),
                        y=float(item["y"]),
                        risk_level=item.get("risk_level", "green"),
                        last_inspection_at=parse_datetime(item.get("last_inspection_at")),
                        next_inspection_at=parse_datetime(item.get("next_inspection_at")),
                        notes=str(item.get("notes", "")),
                    )
                )

    def _regenerate_notifications(self, session: Session, dataset_id: int) -> None:
        session.execute(delete(Notification).where(col(Notification.dataset_id) == dataset_id))
        session.flush()
        regions = {
            region.id: region
            for region in session.exec(select(Region).where(Region.dataset_id == dataset_id)).all()
        }

        for reservoir in session.exec(
            select(Reservoir).where(Reservoir.dataset_id == dataset_id)
        ).all():
            region = regions.get(reservoir.region_id)
            if region and reservoir.percent_filled < reservoir.low_threshold_percent:
                session.add(
                    self._notification(
                        dataset_id,
                        region,
                        Severity.red,
                        f"{reservoir.name} below low-water threshold",
                        (
                            f"{reservoir.name} is {reservoir.percent_filled:.1f}% full, below "
                            f"the {reservoir.low_threshold_percent:.0f}% threshold."
                        ),
                        "reservoir_level_rule",
                        "reservoir",
                        reservoir.id,
                        reservoir.x,
                        reservoir.y,
                    )
                )

        for sensor in session.exec(select(Sensor).where(Sensor.dataset_id == dataset_id)).all():
            region = regions.get(sensor.region_id)
            if region and sensor.health != SensorHealth.normal:
                severity = (
                    Severity.red
                    if sensor.health in {SensorHealth.critical, SensorHealth.offline}
                    else Severity.yellow
                )
                session.add(
                    self._notification(
                        dataset_id,
                        region,
                        severity,
                        f"{sensor.name} health is {sensor.health.value}",
                        (
                            f"{sensor.sensor_type.title()} sensor reports "
                            f"{sensor.reading:g} {sensor.unit}."
                        ),
                        "sensor_health_rule",
                        "sensor",
                        sensor.id,
                        sensor.x,
                        sensor.y,
                    )
                )

        for river in session.exec(
            select(RiverSection).where(RiverSection.dataset_id == dataset_id)
        ).all():
            region = regions.get(river.region_id)
            if region is None:
                continue
            if river.target_flow_rate_ml_per_day <= 0:
                continue
            variance = (
                river.flow_rate_ml_per_day - river.target_flow_rate_ml_per_day
            ) / river.target_flow_rate_ml_per_day
            if abs(variance) >= 0.2:
                severity = Severity.red if abs(variance) >= 0.3 else Severity.yellow
                direction = "above" if variance > 0 else "below"
                session.add(
                    self._notification(
                        dataset_id,
                        region,
                        severity,
                        f"{river.name} flow {direction} target",
                        (
                            f"Current flow is {river.flow_rate_ml_per_day:.0f} ML/day versus "
                            f"target {river.target_flow_rate_ml_per_day:.0f} ML/day."
                        ),
                        "flow_variance_rule",
                        "river_section",
                        river.id,
                        (river.start_x + river.end_x) / 2,
                        (river.start_y + river.end_y) / 2,
                    )
                )

        for gate in session.exec(select(Gate).where(Gate.dataset_id == dataset_id)).all():
            region = regions.get(gate.region_id)
            if region and gate.planned_action:
                session.add(
                    self._notification(
                        dataset_id,
                        region,
                        Severity.yellow,
                        f"{gate.name} action scheduled",
                        gate.planned_action,
                        "gate_schedule_rule",
                        "gate",
                        gate.id,
                        gate.x,
                        gate.y,
                        predicted_for=gate.planned_for,
                    )
                )

        for vegetation in session.exec(
            select(VegetationZone).where(VegetationZone.dataset_id == dataset_id)
        ).all():
            region = regions.get(vegetation.region_id)
            if region and vegetation.risk_level != Severity.green:
                session.add(
                    self._notification(
                        dataset_id,
                        region,
                        vegetation.risk_level,
                        f"{vegetation.name} inspection attention",
                        vegetation.notes or "Vegetation zone requires operator attention.",
                        "vegetation_risk_rule",
                        "vegetation_zone",
                        vegetation.id,
                        vegetation.x,
                        vegetation.y,
                        predicted_for=vegetation.next_inspection_at,
                    )
                )

    def _notification(
        self,
        dataset_id: int,
        region: Region,
        severity: Severity,
        title: str,
        contents: str,
        generated_from: str,
        source_entity_type: str,
        source_entity_id: int | None,
        local_x: float,
        local_y: float,
        predicted_for: datetime | None = None,
    ) -> Notification:
        map_x, map_y = self._map_point(region, local_x, local_y)
        return Notification(
            dataset_id=dataset_id,
            region_id=region.id,
            title=title,
            contents=contents,
            severity=severity,
            generated_from=generated_from,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            map_x=map_x,
            map_y=map_y,
            prediction_horizon="current-state",
            prediction_method="deterministic-demo-rule",
            predicted_for=predicted_for,
        )

    def _list_notifications(self, session: Session, dataset_id: int) -> list[Notification]:
        return list(
            session.exec(
                select(Notification)
                .where(Notification.dataset_id == dataset_id)
                .where(Notification.status == NotificationStatus.active)
                .order_by(col(Notification.created_at).desc())
            ).all()
        )

    def _dashboard_locations(
        self,
        session: Session,
        dataset_id: int,
        regions: list[Region],
        notifications: list[Notification],
    ) -> list[DashboardLocation]:
        regions_by_id = {region.id: region for region in regions if region.id is not None}
        locations: list[DashboardLocation] = []

        for river in session.exec(
            select(RiverSection).where(RiverSection.dataset_id == dataset_id)
        ).all():
            region = regions_by_id.get(river.region_id)
            if region is None or river.id is None or region.id is None:
                continue
            map_x, map_y = self._map_point(
                region,
                (river.start_x + river.end_x) / 2,
                (river.start_y + river.end_y) / 2,
            )
            locations.append(
                DashboardLocation(
                    type="river_section",
                    id=river.id,
                    region_id=region.id,
                    label=river.name,
                    summary=(
                        f"{river.flow_rate_ml_per_day:.0f} ML/day flow, "
                        f"target {river.target_flow_rate_ml_per_day:.0f}"
                    ),
                    map_x=map_x,
                    map_y=map_y,
                    severity=self._dashboard_location_severity(
                        "river_section",
                        river.id,
                        region.id,
                        notifications,
                    ),
                )
            )

        for reservoir in session.exec(
            select(Reservoir).where(Reservoir.dataset_id == dataset_id)
        ).all():
            region = regions_by_id.get(reservoir.region_id)
            if region is None or reservoir.id is None or region.id is None:
                continue
            map_x, map_y = self._map_point(region, reservoir.x, reservoir.y)
            locations.append(
                DashboardLocation(
                    type="reservoir",
                    id=reservoir.id,
                    region_id=region.id,
                    label=reservoir.name,
                    summary=(
                        f"{reservoir.percent_filled:.1f}% full, "
                        f"{reservoir.current_amount_ml:.0f} ML stored"
                    ),
                    map_x=map_x,
                    map_y=map_y,
                    severity=self._dashboard_location_severity(
                        "reservoir",
                        reservoir.id,
                        region.id,
                        notifications,
                    ),
                )
            )

        return sorted(locations, key=lambda location: (location.map_y, location.map_x))

    def _dashboard_location_severity(
        self,
        source_entity_type: str,
        source_entity_id: int,
        region_id: int,
        notifications: list[Notification],
    ) -> Severity:
        severity = Severity.green
        rank = {Severity.green: 0, Severity.yellow: 1, Severity.red: 2}
        for notification in notifications:
            matches_entity = (
                notification.source_entity_type == source_entity_type
                and notification.source_entity_id == source_entity_id
            )
            if (
                (matches_entity or notification.region_id == region_id)
                and rank[notification.severity] > rank[severity]
            ):
                severity = notification.severity
        return severity

    def _map_point(self, region: Region, local_x: float, local_y: float) -> tuple[float, float]:
        return (
            min(0.96, max(0.04, region.map_x + local_x * 0.012)),
            min(0.96, max(0.04, region.map_y - local_y * 0.012)),
        )

    def _component_metrics(self, component_type: str, component: Any) -> dict[str, Any]:
        if component_type == "river_section":
            return {
                "flow_rate_ml_per_day": component.flow_rate_ml_per_day,
                "target_flow_rate_ml_per_day": component.target_flow_rate_ml_per_day,
                "water_level_m": component.water_level_m,
                "percent_filled": self._river_fill_percent(component),
                "absorption_rate_percent": component.absorption_rate_percent,
                "evaporation_rate_mm_per_day": component.evaporation_rate_mm_per_day,
            }
        if component_type == "gate":
            return {
                "state": component.state,
                "opening_percent": component.opening_percent,
                "planned_action": component.planned_action,
                "next_inspection_at": component.next_inspection_at,
            }
        if component_type == "sensor":
            return {
                "reading": component.reading,
                "unit": component.unit,
                "health": component.health,
                "last_updated_at": component.last_updated_at,
            }
        if component_type == "reservoir":
            return {
                "capacity_ml": component.capacity_ml,
                "current_amount_ml": component.current_amount_ml,
                "percent_filled": component.percent_filled,
            }
        return {"risk_level": getattr(component, "risk_level", None)}

    def _ensure_optional_columns(self) -> None:
        inspector = inspect(self.engine)
        if not inspector.has_table("river_section"):
            return
        column_names = {
            column["name"] for column in inspector.get_columns("river_section")
        }
        if "percent_filled" in column_names:
            return
        with self.engine.begin() as connection:
            connection.execute(text("alter table river_section add column percent_filled float"))

    def _river_fill_percent(self, river: RiverSection) -> float:
        if river.percent_filled is not None:
            return min(100.0, max(0.0, river.percent_filled))

        display_fill_percent = river.display.get("percent_filled") or river.display.get(
            "fill_percent"
        )
        if isinstance(display_fill_percent, int | float):
            return min(100.0, max(0.0, float(display_fill_percent)))

        max_water_level = river.display.get("max_water_level_m", 2)
        if not isinstance(max_water_level, int | float) or max_water_level <= 0:
            return 0.0
        return min(100.0, max(0.0, river.water_level_m / float(max_water_level) * 100))
