from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class BotRow(Base):
    __tablename__ = "portal_bots"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    spec_json: Mapped[str] = mapped_column(Text, nullable=False)
    desired_state: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_state: Mapped[str] = mapped_column(String(32), nullable=False)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (Index("ix_portal_bots_tenant", "tenant_id"),)


class BotConfigRevisionRow(Base):
    __tablename__ = "portal_bot_config_revisions"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision_id: Mapped[str] = mapped_column(String(255), nullable=False)
    revision_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "revision_id", name="uq_portal_revision_identity"),
        Index("ix_portal_revisions_tenant_bot", "tenant_id", "bot_id"),
    )


class AuditEventRow(Base):
    __tablename__ = "portal_audit_events"

    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_portal_audit_tenant_resource", "tenant_id", "resource_type", "resource_id"),
    )


class OutboxEventRow(Base):
    __tablename__ = "portal_outbox_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(255), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_json: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_portal_outbox_tenant_aggregate", "tenant_id", "aggregate_type", "aggregate_id"),
        Index("ix_portal_outbox_unpublished", "published_at"),
    )
