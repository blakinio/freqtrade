from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class OperationalOrderRow(Base):
    __tablename__ = "portal_operational_orders"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_runtime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_portal_operational_orders_tenant_bot", "tenant_id", "bot_id", "created_at"),
    )


class OperationalPositionRow(Base):
    __tablename__ = "portal_operational_positions"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    position_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_runtime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    position_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "ix_portal_operational_positions_tenant_bot",
            "tenant_id",
            "bot_id",
            "opened_at",
        ),
    )
