from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class LifecycleCommandRow(Base):
    __tablename__ = "portal_lifecycle_commands"

    command_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    desired_state: Mapped[str] = mapped_column(String(32), nullable=False)
    generation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    expected_state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_current_state: Mapped[str] = mapped_column(String(32), nullable=False)
    accepted_state_version: Mapped[int] = mapped_column(Integer, nullable=False)
    semantic_request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "bot_id"],
            ["portal_bots.tenant_id", "portal_bots.bot_id"],
            name="fk_portal_lifecycle_command_bot",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["generation_id"],
            ["portal_runtime_generations.generation_id"],
            name="fk_portal_lifecycle_command_generation",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id", "bot_id", "idempotency_key", name="uq_portal_lifecycle_idempotency"
        ),
        Index("ix_portal_lifecycle_command_pending", "status", "updated_at"),
        Index("ix_portal_lifecycle_command_tenant_bot", "tenant_id", "bot_id"),
    )


class OutboxDeliveryRow(Base):
    __tablename__ = "portal_outbox_delivery"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["event_id"],
            ["portal_outbox_events.event_id"],
            name="fk_portal_outbox_delivery_event",
            ondelete="RESTRICT",
        ),
        Index("ix_portal_outbox_delivery_due", "dead_lettered_at", "next_attempt_at"),
    )
