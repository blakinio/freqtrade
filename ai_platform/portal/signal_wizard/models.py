from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class SignalWizardPreviewRow(Base):
    __tablename__ = "portal_signal_wizard_previews"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_portal_signal_wizard_preview_tenant_idempotency",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    preview_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    command_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_json: Mapped[str] = mapped_column(Text, nullable=False)


class SignalWizardSubmissionRow(Base):
    __tablename__ = "portal_signal_wizard_submissions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_portal_signal_wizard_submit_tenant_idempotency",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    preview_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    command_json: Mapped[str] = mapped_column(Text, nullable=False)
    submission_json: Mapped[str] = mapped_column(Text, nullable=False)
