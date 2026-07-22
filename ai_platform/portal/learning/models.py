from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_platform.portal.control_plane.database import Base


class LearningHypothesisRow(Base):
    __tablename__ = "portal_learning_hypotheses"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_insight_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    hypothesis_json: Mapped[str] = mapped_column(Text)


class LearningExperimentRow(Base):
    __tablename__ = "portal_learning_experiments"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(String(36), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    experiment_json: Mapped[str] = mapped_column(Text)


class LearningCandidateRow(Base):
    __tablename__ = "portal_learning_candidates"

    tenant_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(36), index=True)
    candidate_model_version_id: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    candidate_json: Mapped[str] = mapped_column(Text)
