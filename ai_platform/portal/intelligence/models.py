from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class DecisionSnapshotRow(Base):
    __tablename__ = "portal_decision_snapshots"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_intent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    decision_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "trade_intent_id",
            name="uq_portal_decision_snapshot_tenant_intent",
        ),
        Index("ix_portal_decision_snapshots_tenant_bot", "tenant_id", "bot_id"),
        Index(
            "ix_portal_decision_snapshots_tenant_decision_at",
            "tenant_id",
            "decision_at",
        ),
    )


class TradeOutcomeRow(Base):
    __tablename__ = "portal_trade_outcomes"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_portal_trade_outcomes_tenant_trade", "tenant_id", "trade_id"),
        Index("ix_portal_trade_outcomes_tenant_bot", "tenant_id", "bot_id"),
        Index("ix_portal_trade_outcomes_tenant_closed_at", "tenant_id", "closed_at"),
    )


class TradeAnalysisRow(Base):
    __tablename__ = "portal_trade_analyses"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    outcome_id: Mapped[str] = mapped_column(String(36), nullable=False)
    diagnosis_code: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_portal_trade_analyses_tenant_snapshot", "tenant_id", "snapshot_id"),
        Index("ix_portal_trade_analyses_tenant_outcome", "tenant_id", "outcome_id"),
        Index("ix_portal_trade_analyses_tenant_diagnosis", "tenant_id", "diagnosis_code"),
        Index("ix_portal_trade_analyses_tenant_created_at", "tenant_id", "created_at"),
    )
