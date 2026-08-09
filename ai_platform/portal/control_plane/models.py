from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
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


class BotRow(Base):
    __tablename__ = "portal_bots"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    spec_json: Mapped[str] = mapped_column(Text, nullable=False)
    desired_state: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_state: Mapped[str] = mapped_column(String(32), nullable=False)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    latest_authored_revision_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    desired_revision_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    desired_runtime_generation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    observed_runtime_generation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    state_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "current_revision > 0",
            name="ck_portal_bots_current_revision_positive",
        ),
        Index("ix_portal_bots_tenant", "tenant_id"),
    )


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
        CheckConstraint(
            "revision > 0",
            name="ck_portal_bot_config_revision_positive",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "bot_id"],
            ["portal_bots.tenant_id", "portal_bots.bot_id"],
            name="fk_portal_revision_bot",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "revision_id", name="uq_portal_revision_identity"),
        Index("ix_portal_revisions_tenant_bot", "tenant_id", "bot_id"),
    )


class RuntimeGenerationRow(Base):
    __tablename__ = "portal_runtime_generations"

    generation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    generation_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    config_revision_id: Mapped[str] = mapped_column(String(255), nullable=False)
    config_revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    config_revision_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_runtime_config_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_image_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy_artifact_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_artifact_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feature_schema_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_policy_version: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_policy_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    managed_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    managed_mode_request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    managed_mode_resolution_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    paper_authorization_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exchange_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange_connection_revision: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isolation_profile_version: Mapped[str] = mapped_column(String(255), nullable=False)
    isolation_profile_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    gateway_contract_version: Mapped[str] = mapped_column(String(255), nullable=False)
    generation_spec_version: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_spec_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "managed_mode IN ('shadow', 'paper')",
            name="ck_portal_runtime_generation_managed_mode",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "bot_id"],
            ["portal_bots.tenant_id", "portal_bots.bot_id"],
            name="fk_portal_runtime_generation_bot",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "bot_id",
            "generation_ordinal",
            name="uq_portal_runtime_generation_ordinal",
        ),
        Index("ix_portal_runtime_generation_bot", "tenant_id", "bot_id"),
    )


class BotRolloutRow(Base):
    __tablename__ = "portal_bot_rollouts"

    rollout_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    from_generation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    to_generation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "bot_id"],
            ["portal_bots.tenant_id", "portal_bots.bot_id"],
            name="fk_portal_rollout_bot",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["to_generation_id"],
            ["portal_runtime_generations.generation_id"],
            name="fk_portal_rollout_to_generation",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["from_generation_id"],
            ["portal_runtime_generations.generation_id"],
            name="fk_portal_rollout_from_generation",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "bot_id",
            "idempotency_key",
            name="uq_portal_rollout_idempotency",
        ),
        Index("ix_portal_rollout_bot", "tenant_id", "bot_id"),
    )


class RuntimeGenerationObservationRow(Base):
    __tablename__ = "portal_runtime_generation_observations"

    observation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    generation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    runtime_instance_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reconciliation_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    reconciliation_attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_state: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_generation_spec_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_image_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_config_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reconciled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    identity_status: Mapped[str] = mapped_column(String(32), nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(32), nullable=False)
    completeness_status: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["generation_id"],
            ["portal_runtime_generations.generation_id"],
            name="fk_portal_runtime_observation_generation",
            ondelete="RESTRICT",
        ),
        Index("ix_portal_runtime_observation_generation", "generation_id", "reconciled_at"),
    )


class CommandIdempotencyRow(Base):
    __tablename__ = "portal_command_idempotency"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    semantic_request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rollout_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "bot_id"],
            ["portal_bots.tenant_id", "portal_bots.bot_id"],
            name="fk_portal_command_idempotency_bot",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["generation_id"],
            ["portal_runtime_generations.generation_id"],
            name="fk_portal_command_idempotency_generation",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["rollout_id"],
            ["portal_bot_rollouts.rollout_id"],
            name="fk_portal_command_idempotency_rollout",
            ondelete="RESTRICT",
        ),
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
