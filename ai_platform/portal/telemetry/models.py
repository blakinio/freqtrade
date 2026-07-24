from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class InferenceTelemetryWindowRow(Base):
    __tablename__ = "portal_inference_telemetry_windows"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    telemetry_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    model_version_id: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_schema_version_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_config_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    bot_config_revision_id: Mapped[str] = mapped_column(String(255), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    window_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    telemetry_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "ix_portal_inference_windows_tenant_model_role",
            "tenant_id",
            "model_version_id",
            "role",
            "window_end_at",
        ),
        Index(
            "ix_portal_inference_windows_tenant_runtime",
            "tenant_id",
            "runtime_id",
            "bot_config_revision_id",
            "window_end_at",
        ),
    )


class InferenceTelemetrySourceStatusRow(Base):
    __tablename__ = "portal_inference_telemetry_source_status"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    model_version_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    feature_schema_version_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_config_revision_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    runtime_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    availability: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(255), nullable=False)
    status_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "ix_portal_inference_source_status_tenant_model",
            "tenant_id",
            "model_version_id",
            "checked_at",
        ),
    )


class InferenceDriftAssessmentRow(Base):
    __tablename__ = "portal_inference_drift_assessments"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_version_id: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_schema_version_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_config_revision_id: Mapped[str] = mapped_column(String(255), nullable=False)
    runtime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_telemetry_id: Mapped[str] = mapped_column(String(36), nullable=False)
    observation_telemetry_id: Mapped[str] = mapped_column(String(36), nullable=False)
    observation_window_end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    assessment_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "ix_portal_inference_assessments_tenant_model",
            "tenant_id",
            "model_version_id",
            "observation_window_end_at",
        ),
        Index(
            "ix_portal_inference_assessments_tenant_runtime",
            "tenant_id",
            "runtime_id",
            "bot_config_revision_id",
            "observation_window_end_at",
        ),
    )
