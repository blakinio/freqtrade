from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class SignalEventRow(Base):
    __tablename__ = "portal_signal_events"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    signal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signal_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_portal_signal_events_tenant_time", "tenant_id", "occurred_at", "signal_id"),
        Index("ix_portal_signal_events_tenant_bot", "tenant_id", "bot_id", "occurred_at"),
    )


class GridBotConfigRow(Base):
    __tablename__ = "portal_grid_bot_configs"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    grid_config_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_portal_grid_bot_configs_tenant_bot", "tenant_id", "bot_id", "created_at"),
    )


class NotificationPreferenceRow(Base):
    __tablename__ = "portal_notification_preferences"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    signal_events: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_events: Mapped[bool] = mapped_column(Boolean, nullable=False)
    execution_events: Mapped[bool] = mapped_column(Boolean, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    preference_json: Mapped[str] = mapped_column(Text, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
