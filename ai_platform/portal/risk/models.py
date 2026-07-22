from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class RiskPolicyRow(Base):
    __tablename__ = "portal_risk_policies"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    risk_policy_version_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    policy_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    definition_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_portal_risk_policy_tenant", "tenant_id"),)


class RiskKillSwitchRow(Base):
    __tablename__ = "portal_risk_kill_switches"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    environment: Mapped[str] = mapped_column(String(32), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TradeIntentRow(Base):
    __tablename__ = "portal_trade_intents"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    trade_intent_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    intent_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_portal_trade_intents_tenant_bot", "tenant_id", "bot_id", "created_at"),
    )


class RiskDecisionRow(Base):
    __tablename__ = "portal_risk_decisions"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    risk_decision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trade_intent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    decision_json: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "trade_intent_id"],
            ["portal_trade_intents.tenant_id", "portal_trade_intents.trade_intent_id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_portal_risk_decisions_tenant_intent",
            "tenant_id",
            "trade_intent_id",
            "occurred_at",
        ),
    )
