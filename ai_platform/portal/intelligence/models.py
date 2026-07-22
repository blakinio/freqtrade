from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class DecisionSnapshotRow(Base):
    __tablename__ = "portal_decision_snapshots"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), index=True)
    trade_intent_id: Mapped[str] = mapped_column(String(36), unique=True)
    decision_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    snapshot_json: Mapped[str] = mapped_column(Text)


class TradeOutcomeRow(Base):
    __tablename__ = "portal_trade_outcomes"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(255), index=True)
    bot_id: Mapped[str] = mapped_column(String(255), index=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    outcome_json: Mapped[str] = mapped_column(Text)


class TradeAnalysisRow(Base):
    __tablename__ = "portal_trade_analyses"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), index=True)
    outcome_id: Mapped[str] = mapped_column(String(36), index=True)
    diagnosis_code: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    analysis_json: Mapped[str] = mapped_column(Text)
