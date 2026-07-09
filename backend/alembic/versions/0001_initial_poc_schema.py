"""initial poc schema

Revision ID: 0001
Revises:
Create Date: 2026-07-09 08:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "demo_dataset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_demo_dataset_is_active", "demo_dataset", ["is_active"])

    op.create_table(
        "region",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("map_x", sa.Float(), nullable=False),
        sa.Column("map_y", sa.Float(), nullable=False),
        sa.Column("gps_lat", sa.Float(), nullable=True),
        sa.Column("gps_lng", sa.Float(), nullable=True),
        sa.Column("display", sa.JSON(), nullable=False),
    )
    op.create_index("ix_region_dataset_id", "region", ["dataset_id"])
    op.create_index("ix_region_slug", "region", ["slug"])

    op.create_table(
        "river_section",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("region.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_x", sa.Float(), nullable=False),
        sa.Column("start_y", sa.Float(), nullable=False),
        sa.Column("end_x", sa.Float(), nullable=False),
        sa.Column("end_y", sa.Float(), nullable=False),
        sa.Column("flow_rate_ml_per_day", sa.Float(), nullable=False),
        sa.Column("target_flow_rate_ml_per_day", sa.Float(), nullable=False),
        sa.Column("water_level_m", sa.Float(), nullable=False),
        sa.Column("absorption_rate_percent", sa.Float(), nullable=False),
        sa.Column("evaporation_rate_mm_per_day", sa.Float(), nullable=False),
        sa.Column("display", sa.JSON(), nullable=False),
    )
    op.create_index("ix_river_section_dataset_id", "river_section", ["dataset_id"])
    op.create_index("ix_river_section_region_id", "river_section", ["region_id"])

    op.create_table(
        "gate",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("region.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("opening_percent", sa.Float(), nullable=False),
        sa.Column("planned_action", sa.String(), nullable=True),
        sa.Column("planned_for", sa.DateTime(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("next_inspection_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_gate_asset_id", "gate", ["asset_id"])
    op.create_index("ix_gate_dataset_id", "gate", ["dataset_id"])
    op.create_index("ix_gate_region_id", "gate", ["region_id"])

    op.create_table(
        "sensor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("region.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sensor_id", sa.String(), nullable=False),
        sa.Column("sensor_type", sa.String(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("reading", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("health", sa.String(), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(), nullable=False),
        sa.Column("calibration_due_at", sa.DateTime(), nullable=True),
        sa.Column("next_inspection_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_sensor_dataset_id", "sensor", ["dataset_id"])
    op.create_index("ix_sensor_region_id", "sensor", ["region_id"])
    op.create_index("ix_sensor_sensor_id", "sensor", ["sensor_id"])

    op.create_table(
        "reservoir",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("region.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("capacity_ml", sa.Float(), nullable=False),
        sa.Column("current_amount_ml", sa.Float(), nullable=False),
        sa.Column("percent_filled", sa.Float(), nullable=False),
        sa.Column("low_threshold_percent", sa.Float(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_reservoir_dataset_id", "reservoir", ["dataset_id"])
    op.create_index("ix_reservoir_region_id", "reservoir", ["region_id"])

    op.create_table(
        "vegetation_zone",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("region.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("last_inspection_at", sa.DateTime(), nullable=True),
        sa.Column("next_inspection_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(), nullable=False),
    )
    op.create_index("ix_vegetation_zone_dataset_id", "vegetation_zone", ["dataset_id"])
    op.create_index("ix_vegetation_zone_region_id", "vegetation_zone", ["region_id"])

    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("demo_dataset.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("region.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("contents", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("generated_from", sa.String(), nullable=False),
        sa.Column("source_entity_type", sa.String(), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=True),
        sa.Column("map_x", sa.Float(), nullable=False),
        sa.Column("map_y", sa.Float(), nullable=False),
        sa.Column("prediction_horizon", sa.String(), nullable=True),
        sa.Column("prediction_method", sa.String(), nullable=True),
        sa.Column("predicted_for", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notification_dataset_id", "notification", ["dataset_id"])
    op.create_index("ix_notification_region_id", "notification", ["region_id"])
    op.create_index("ix_notification_severity", "notification", ["severity"])
    op.create_index("ix_notification_status", "notification", ["status"])


def downgrade() -> None:
    op.drop_table("notification")
    op.drop_table("vegetation_zone")
    op.drop_table("reservoir")
    op.drop_table("sensor")
    op.drop_table("gate")
    op.drop_table("river_section")
    op.drop_table("region")
    op.drop_table("demo_dataset")
