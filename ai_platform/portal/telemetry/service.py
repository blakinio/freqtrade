from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.models import ModelVersion
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.model_control.repository import ModelControlRepository
from ai_platform.portal.security.authorization import PermissionDeniedError, require_permission
from ai_platform.portal.telemetry.drift import PSI_V1, assess_drift
from ai_platform.portal.telemetry.repository import InferenceTelemetryRepository
from ai_platform.portal.telemetry.schema import (
    DriftAssessment,
    DriftHealthStatus,
    InferenceTelemetryEnvelope,
    InferenceTelemetryScope,
    InferenceTelemetrySourceStatus,
    ModelHealthRecord,
    TelemetrySourceAvailability,
    TelemetryWindowRole,
)


Clock = Callable[[], datetime]
ScopeKey = tuple[str, str, str, str, str, str, str]


class TelemetryConflictError(RuntimeError):
    pass


class TelemetryAttributionError(ValueError):
    pass


class InferenceTelemetryService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: InferenceTelemetryRepository | None = None,
        model_repository: ModelControlRepository | None = None,
        bot_repository: BotRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or InferenceTelemetryRepository()
        self._model_repository = model_repository or ModelControlRepository()
        self._bot_repository = bot_repository or BotRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def ingest_window(
        self,
        context: RequestContext,
        envelope: InferenceTelemetryEnvelope,
    ) -> InferenceTelemetryEnvelope:
        self._require_ingest_authority(context)
        self._require_tenant(context, envelope.scope.tenant_id)
        with self._session_factory() as session, session.begin():
            self._validate_scope(session, envelope.scope)
            existing = self._repository.get_window(
                session,
                context.tenant_id,
                str(envelope.telemetry_id),
            )
            if existing is not None:
                if existing.canonical_json() != envelope.canonical_json():
                    raise TelemetryConflictError(
                        "telemetry identity already exists with different canonical payload"
                    )
                return existing
            self._repository.add_window(session, envelope)
            self._refresh_assessment(session, envelope.scope)
        return envelope

    def record_source_status(
        self,
        context: RequestContext,
        status: InferenceTelemetrySourceStatus,
    ) -> InferenceTelemetrySourceStatus:
        self._require_ingest_authority(context)
        self._require_tenant(context, status.scope.tenant_id)
        with self._session_factory() as session, session.begin():
            self._validate_scope(session, status.scope)
            self._repository.upsert_source_status(session, status)
        return status

    def list_windows(
        self,
        context: RequestContext,
        model_version_id: str | None = None,
    ) -> tuple[InferenceTelemetryEnvelope, ...]:
        require_permission(context.permissions, Permission.MODEL_READ)
        with self._session_factory() as session:
            return self._repository.list_windows(
                session,
                context.tenant_id,
                model_version_id,
            )

    def model_health(self, context: RequestContext) -> tuple[ModelHealthRecord, ...]:
        require_permission(context.permissions, Permission.MODEL_READ)
        now = self._clock()
        records: list[ModelHealthRecord] = []
        with self._session_factory() as session:
            models = self._model_repository.list_models(session, context.tenant_id)
            windows = self._repository.list_windows(session, context.tenant_id)
            windows_by_model = self._group_windows_by_model(windows)
            for model in models:
                groups = windows_by_model.get(model.model_version_id, {})
                if not groups:
                    records.append(self._unavailable_model_record(model, now))
                    continue
                for grouped_windows in groups.values():
                    records.append(
                        self._health_for_scope(
                            session,
                            model,
                            grouped_windows,
                            now,
                        )
                    )
        records.sort(key=lambda record: record.health_record_id)
        return tuple(records)

    def _refresh_assessment(
        self,
        session: Session,
        scope: InferenceTelemetryScope,
    ) -> DriftAssessment | None:
        windows = tuple(
            window
            for window in self._repository.list_windows(
                session,
                scope.tenant_id,
                scope.model_version_id,
            )
            if self._scope_key(window.scope) == self._scope_key(scope)
        )
        reference = self._latest_window(windows, TelemetryWindowRole.REFERENCE)
        observation = self._latest_window(windows, TelemetryWindowRole.OBSERVATION)
        if reference is None or observation is None:
            return None
        assessment = assess_drift(
            reference,
            observation,
            assessed_at=self._clock(),
            policy=PSI_V1,
        )
        existing = self._repository.get_assessment(
            session,
            scope.tenant_id,
            assessment.assessment_id,
        )
        if existing is not None:
            return existing
        self._repository.add_assessment(session, assessment, observation)
        return assessment

    def _health_for_scope(
        self,
        session: Session,
        model: ModelVersion,
        windows: tuple[InferenceTelemetryEnvelope, ...],
        now: datetime,
    ) -> ModelHealthRecord:
        scope = windows[0].scope
        reference = self._latest_window(windows, TelemetryWindowRole.REFERENCE)
        observation = self._latest_window(windows, TelemetryWindowRole.OBSERVATION)
        source_status = self._repository.get_source_status(session, scope)
        base = self._health_base(model, scope, now)

        if source_status is None:
            return ModelHealthRecord(
                **base,
                drift_status=DriftHealthStatus.UNAVAILABLE,
                drift_reason="INFERENCE_TELEMETRY_SOURCE_STATUS_NOT_RECORDED",
            )
        if source_status.availability is TelemetrySourceAvailability.UNAVAILABLE:
            return ModelHealthRecord(
                **base,
                drift_status=DriftHealthStatus.UNAVAILABLE,
                drift_reason=source_status.reason_code,
                source_availability=source_status.availability,
                source_checked_at=source_status.checked_at,
            )
        if observation is None:
            return ModelHealthRecord(
                **base,
                drift_status=DriftHealthStatus.UNAVAILABLE,
                drift_reason="OBSERVATION_WINDOW_UNAVAILABLE",
                source_availability=source_status.availability,
                source_checked_at=source_status.checked_at,
            )
        if source_status.checked_at < observation.generated_at:
            return ModelHealthRecord(
                **base,
                drift_status=DriftHealthStatus.UNAVAILABLE,
                drift_reason="INFERENCE_TELEMETRY_SOURCE_STATUS_STALE",
                observation_window_id=observation.window.window_id,
                observation_sample_count=observation.prediction_count,
                accepted_predictions=observation.accepted_predictions,
                rejected_predictions=observation.rejected_predictions,
                rejection_reasons=observation.rejection_reasons,
                source_availability=source_status.availability,
                source_checked_at=source_status.checked_at,
            )
        if reference is None:
            return ModelHealthRecord(
                **base,
                drift_status=DriftHealthStatus.UNAVAILABLE,
                drift_reason="REFERENCE_WINDOW_UNAVAILABLE",
                observation_window_id=observation.window.window_id,
                observation_sample_count=observation.prediction_count,
                accepted_predictions=observation.accepted_predictions,
                rejected_predictions=observation.rejected_predictions,
                rejection_reasons=observation.rejection_reasons,
                source_availability=source_status.availability,
                source_checked_at=source_status.checked_at,
            )

        assessment = self._repository.latest_assessment(session, scope)
        if assessment is None or assessment.observation_telemetry_id != observation.telemetry_id:
            return ModelHealthRecord(
                **base,
                drift_status=DriftHealthStatus.UNAVAILABLE,
                drift_reason="DRIFT_ASSESSMENT_UNAVAILABLE",
                reference_window_id=reference.window.window_id,
                observation_window_id=observation.window.window_id,
                reference_sample_count=reference.prediction_count,
                observation_sample_count=observation.prediction_count,
                accepted_predictions=observation.accepted_predictions,
                rejected_predictions=observation.rejected_predictions,
                rejection_reasons=observation.rejection_reasons,
                source_availability=source_status.availability,
                source_checked_at=source_status.checked_at,
            )

        return ModelHealthRecord(
            **base,
            drift_status=assessment.status,
            drift_reason=assessment.reason_code,
            policy_version=assessment.policy.policy_version,
            reference_window_id=assessment.reference_window_id,
            observation_window_id=assessment.observation_window_id,
            reference_sample_count=assessment.reference_sample_count,
            observation_sample_count=assessment.observation_sample_count,
            accepted_predictions=assessment.accepted_predictions,
            rejected_predictions=assessment.rejected_predictions,
            rejection_reasons=assessment.rejection_reasons,
            prediction_drift_score=assessment.prediction_drift_score,
            max_feature_drift_score=assessment.max_feature_drift_score,
            worst_feature_name=assessment.worst_feature_name,
            max_feature_quality_issue_rate=assessment.max_feature_quality_issue_rate,
            source_availability=source_status.availability,
            source_checked_at=source_status.checked_at,
        )

    @staticmethod
    def _health_base(
        model: ModelVersion,
        scope: InferenceTelemetryScope,
        now: datetime,
    ) -> dict[str, object]:
        return {
            "health_record_id": ":".join(
                (
                    model.model_version_id,
                    scope.bot_id,
                    scope.runtime_id,
                    scope.bot_config_revision_id,
                    scope.source_id,
                )
            ),
            "model_version_id": model.model_version_id,
            "tenant_id": model.tenant_id,
            "model_family_id": model.model_family_id,
            "lifecycle_state": model.lifecycle_state.value,
            "created_at": model.created_at,
            "training_window_end": model.training_window.end_at,
            "metadata_age_days": max((now - model.created_at).days, 0),
            "feature_schema_version_id": scope.feature_schema_version_id,
            "bot_id": scope.bot_id,
            "bot_config_revision_id": scope.bot_config_revision_id,
            "runtime_id": scope.runtime_id,
            "source_id": scope.source_id,
        }

    @staticmethod
    def _unavailable_model_record(model: ModelVersion, now: datetime) -> ModelHealthRecord:
        return ModelHealthRecord(
            health_record_id=f"{model.model_version_id}:unavailable",
            model_version_id=model.model_version_id,
            tenant_id=model.tenant_id,
            model_family_id=model.model_family_id,
            lifecycle_state=model.lifecycle_state.value,
            created_at=model.created_at,
            training_window_end=model.training_window.end_at,
            metadata_age_days=max((now - model.created_at).days, 0),
            drift_status=DriftHealthStatus.UNAVAILABLE,
            drift_reason="CANONICAL_INFERENCE_TELEMETRY_SOURCE_NOT_CONFIGURED",
        )

    def _validate_scope(self, session: Session, scope: InferenceTelemetryScope) -> None:
        model = self._model_repository.get_model(
            session,
            scope.tenant_id,
            scope.model_version_id,
        )
        if model is None:
            raise TelemetryAttributionError("telemetry model version does not exist")
        if model.feature_schema_version_id != scope.feature_schema_version_id:
            raise TelemetryAttributionError("telemetry feature schema does not match model")

        bot = self._bot_repository.get_bot(session, scope.tenant_id, scope.bot_id)
        if bot is None:
            raise TelemetryAttributionError("telemetry bot does not exist")
        revision = self._bot_repository.get_revision(
            session,
            scope.tenant_id,
            scope.bot_id,
            scope.bot_config_revision,
        )
        if revision is None:
            raise TelemetryAttributionError("telemetry bot config revision does not exist")
        if revision.revision_id != scope.bot_config_revision_id:
            raise TelemetryAttributionError("telemetry bot config revision identity mismatch")
        if revision.model_version != scope.model_version_id:
            raise TelemetryAttributionError("telemetry model does not match bot config revision")

    @staticmethod
    def _require_ingest_authority(context: RequestContext) -> None:
        require_permission(context.permissions, Permission.MODEL_TRAIN)
        if context.actor_type not in {ActorType.SERVICE, ActorType.SYSTEM}:
            raise PermissionDeniedError("inference telemetry ingestion requires service identity")

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if context.tenant_id != tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")

    @classmethod
    def _group_windows_by_model(
        cls,
        windows: tuple[InferenceTelemetryEnvelope, ...],
    ) -> dict[str, dict[ScopeKey, tuple[InferenceTelemetryEnvelope, ...]]]:
        grouped: dict[str, dict[ScopeKey, list[InferenceTelemetryEnvelope]]] = {}
        for window in windows:
            model_groups = grouped.setdefault(window.scope.model_version_id, {})
            model_groups.setdefault(cls._scope_key(window.scope), []).append(window)
        return {
            model_version_id: {
                key: tuple(group) for key, group in model_groups.items()
            }
            for model_version_id, model_groups in grouped.items()
        }

    @staticmethod
    def _scope_key(scope: InferenceTelemetryScope) -> ScopeKey:
        return (
            scope.tenant_id,
            scope.model_version_id,
            scope.feature_schema_version_id,
            scope.bot_id,
            scope.bot_config_revision_id,
            scope.runtime_id,
            scope.source_id,
        )

    @staticmethod
    def _latest_window(
        windows: tuple[InferenceTelemetryEnvelope, ...],
        role: TelemetryWindowRole,
    ) -> InferenceTelemetryEnvelope | None:
        matching = [window for window in windows if window.role is role]
        if not matching:
            return None
        return max(
            matching,
            key=lambda window: (
                window.window.end_at,
                window.generated_at,
                str(window.telemetry_id),
            ),
        )
