from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class ModelVersionRow(Base):
    __tablename__ = "portal_model_versions"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    model_version_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    model_family_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_json: Mapped[str] = mapped_column(Text, nullable=False)
    registered_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_portal_model_versions_tenant_family", "tenant_id", "model_family_id"),
    )


class ModelPromotionSlotRow(Base):
    __tablename__ = "portal_model_promotion_slots"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    model_family_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    environment: Mapped[str] = mapped_column(String(32), primary_key=True)
    current_model_version_id: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "current_model_version_id"],
            ["portal_model_versions.tenant_id", "portal_model_versions.model_version_id"],
            ondelete="RESTRICT",
        ),
        Index("ix_portal_model_slots_tenant_model", "tenant_id", "current_model_version_id"),
    )


class ModelPromotionHistoryRow(Base):
    __tablename__ = "portal_model_promotion_history"

    transition_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_family_id: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False)
    from_model_version_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_model_version_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_portal_model_promotion_history_slot",
            "tenant_id",
            "model_family_id",
            "environment",
            "occurred_at",
        ),
        Index(
            "ix_portal_model_promotion_history_target",
            "tenant_id",
            "to_model_version_id",
        ),
    )
