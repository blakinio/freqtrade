from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class ExecutionSubmissionRow(Base):
    __tablename__ = "portal_execution_submissions"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    command_id: Mapped[str] = mapped_column(String(255), nullable=False)
    execution_intent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    submission_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    submission_json: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_portal_execution_submission_idempotency",
        ),
        UniqueConstraint(
            "tenant_id",
            "command_id",
            name="uq_portal_execution_submission_command",
        ),
        UniqueConstraint(
            "tenant_id",
            "execution_intent_id",
            name="uq_portal_execution_submission_intent",
        ),
        Index(
            "ix_portal_execution_submissions_tenant_updated",
            "tenant_id",
            "updated_at",
        ),
    )
