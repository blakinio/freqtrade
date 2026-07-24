from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.telemetry.models import (
    InferenceDriftAssessmentRow,
    InferenceTelemetrySourceStatusRow,
    InferenceTelemetryWindowRow,
)
from ai_platform.portal.telemetry.schema import (
    DriftAssessment,
    InferenceTelemetryEnvelope,
    InferenceTelemetryScope,
    InferenceTelemetrySourceStatus,
)


class InferenceTelemetryRepository:
    def get_window(
        self,
        session: Session,
        tenant_id: str,
        telemetry_id: str,
    ) -> InferenceTelemetryEnvelope | None:
        row = session.get(InferenceTelemetryWindowRow, (tenant_id, telemetry_id))
        if row is None:
            return None
        return InferenceTelemetryEnvelope.model_validate_json(row.telemetry_json)

    def add_window(self, session: Session, envelope: InferenceTelemetryEnvelope) -> None:
        scope = envelope.scope
        session.add(
            InferenceTelemetryWindowRow(
                tenant_id=scope.tenant_id,
                telemetry_id=str(envelope.telemetry_id),
                model_version_id=scope.model_version_id,
                feature_schema_version_id=scope.feature_schema_version_id,
                bot_id=scope.bot_id,
                bot_config_revision=scope.bot_config_revision,
                bot_config_revision_id=scope.bot_config_revision_id,
                runtime_id=scope.runtime_id,
                source_id=scope.source_id,
                role=envelope.role.value,
                window_start_at=envelope.window.start_at,
                window_end_at=envelope.window.end_at,
                generated_at=envelope.generated_at,
                telemetry_json=envelope.canonical_json(),
            )
        )

    def list_windows(
        self,
        session: Session,
        tenant_id: str,
        model_version_id: str | None = None,
    ) -> tuple[InferenceTelemetryEnvelope, ...]:
        statement = select(InferenceTelemetryWindowRow).where(
            InferenceTelemetryWindowRow.tenant_id == tenant_id
        )
        if model_version_id is not None:
            statement = statement.where(
                InferenceTelemetryWindowRow.model_version_id == model_version_id
            )
        rows = session.scalars(
            statement.order_by(
                InferenceTelemetryWindowRow.model_version_id,
                InferenceTelemetryWindowRow.window_end_at,
                InferenceTelemetryWindowRow.telemetry_id,
            )
        ).all()
        return tuple(
            InferenceTelemetryEnvelope.model_validate_json(row.telemetry_json) for row in rows
        )

    def get_source_status(
        self,
        session: Session,
        scope: InferenceTelemetryScope,
    ) -> InferenceTelemetrySourceStatus | None:
        row = session.get(
            InferenceTelemetrySourceStatusRow,
            (
                scope.tenant_id,
                scope.model_version_id,
                scope.feature_schema_version_id,
                scope.bot_id,
                scope.bot_config_revision_id,
                scope.runtime_id,
                scope.source_id,
            ),
        )
        if row is None:
            return None
        return InferenceTelemetrySourceStatus.model_validate_json(row.status_json)

    def upsert_source_status(
        self,
        session: Session,
        status: InferenceTelemetrySourceStatus,
    ) -> None:
        scope = status.scope
        row = session.get(
            InferenceTelemetrySourceStatusRow,
            (
                scope.tenant_id,
                scope.model_version_id,
                scope.feature_schema_version_id,
                scope.bot_id,
                scope.bot_config_revision_id,
                scope.runtime_id,
                scope.source_id,
            ),
        )
        if row is None:
            session.add(
                InferenceTelemetrySourceStatusRow(
                    tenant_id=scope.tenant_id,
                    model_version_id=scope.model_version_id,
                    feature_schema_version_id=scope.feature_schema_version_id,
                    bot_id=scope.bot_id,
                    bot_config_revision_id=scope.bot_config_revision_id,
                    runtime_id=scope.runtime_id,
                    source_id=scope.source_id,
                    checked_at=status.checked_at,
                    availability=status.availability.value,
                    reason_code=status.reason_code,
                    status_json=status.canonical_json(),
                )
            )
            return
        current = InferenceTelemetrySourceStatus.model_validate_json(row.status_json)
        if status.checked_at < current.checked_at:
            return
        row.checked_at = status.checked_at
        row.availability = status.availability.value
        row.reason_code = status.reason_code
        row.status_json = status.canonical_json()

    def get_assessment(
        self,
        session: Session,
        tenant_id: str,
        assessment_id: str,
    ) -> DriftAssessment | None:
        row = session.get(InferenceDriftAssessmentRow, (tenant_id, assessment_id))
        if row is None:
            return None
        return DriftAssessment.model_validate_json(row.assessment_json)

    def add_assessment(
        self,
        session: Session,
        assessment: DriftAssessment,
        observation: InferenceTelemetryEnvelope,
    ) -> None:
        scope = assessment.scope
        session.add(
            InferenceDriftAssessmentRow(
                tenant_id=scope.tenant_id,
                assessment_id=assessment.assessment_id,
                model_version_id=scope.model_version_id,
                feature_schema_version_id=scope.feature_schema_version_id,
                bot_id=scope.bot_id,
                bot_config_revision_id=scope.bot_config_revision_id,
                runtime_id=scope.runtime_id,
                source_id=scope.source_id,
                reference_telemetry_id=str(assessment.reference_telemetry_id),
                observation_telemetry_id=str(assessment.observation_telemetry_id),
                observation_window_end_at=observation.window.end_at,
                assessed_at=assessment.assessed_at,
                status=assessment.status.value,
                assessment_json=assessment.canonical_json(),
            )
        )

    def latest_assessment(
        self,
        session: Session,
        scope: InferenceTelemetryScope,
    ) -> DriftAssessment | None:
        row = session.scalar(
            select(InferenceDriftAssessmentRow)
            .where(
                InferenceDriftAssessmentRow.tenant_id == scope.tenant_id,
                InferenceDriftAssessmentRow.model_version_id == scope.model_version_id,
                InferenceDriftAssessmentRow.feature_schema_version_id
                == scope.feature_schema_version_id,
                InferenceDriftAssessmentRow.bot_id == scope.bot_id,
                InferenceDriftAssessmentRow.bot_config_revision_id == scope.bot_config_revision_id,
                InferenceDriftAssessmentRow.runtime_id == scope.runtime_id,
                InferenceDriftAssessmentRow.source_id == scope.source_id,
            )
            .order_by(
                InferenceDriftAssessmentRow.observation_window_end_at.desc(),
                InferenceDriftAssessmentRow.assessment_id.desc(),
            )
            .limit(1)
        )
        if row is None:
            return None
        return DriftAssessment.model_validate_json(row.assessment_json)
