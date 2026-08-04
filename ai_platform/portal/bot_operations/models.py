from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class BotCommandRow(Base):
    __tablename__ = "portal_bot_commands"

    scope_tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    command_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    command_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    command_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    command_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "scope_tenant_id",
            "idempotency_key",
            name="uq_portal_bot_command_idempotency",
        ),
        Index("ix_portal_bot_commands_tenant_created", "scope_tenant_id", "created_at"),
    )


class BotCommandHistoryRow(Base):
    __tablename__ = "portal_bot_command_history"

    history_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope_tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    command_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_json: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["scope_tenant_id", "command_id"],
            ["portal_bot_commands.scope_tenant_id", "portal_bot_commands.command_id"],
            name="fk_portal_bot_command_history_command",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "scope_tenant_id",
            "command_id",
            "sequence",
            name="uq_portal_bot_command_history_sequence",
        ),
        Index(
            "ix_portal_bot_command_history_tenant_command",
            "scope_tenant_id",
            "command_id",
            "sequence",
        ),
    )


class BotCommandIdempotencyConflictRow(Base):
    __tablename__ = "portal_bot_command_idempotency_conflicts"

    conflict_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope_tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    existing_command_id: Mapped[str] = mapped_column(String(255), nullable=False)
    attempted_command_id: Mapped[str] = mapped_column(String(255), nullable=False)
    conflict_json: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["scope_tenant_id", "existing_command_id"],
            ["portal_bot_commands.scope_tenant_id", "portal_bot_commands.command_id"],
            name="fk_portal_bot_command_conflict_existing_command",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_portal_bot_command_conflicts_tenant_key",
            "scope_tenant_id",
            "idempotency_key",
            "recorded_at",
        ),
    )
