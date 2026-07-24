from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.models import ModelLifecycleState, ModelVersion, TrainingWindow
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.model_control.service import ModelControlService
from ai_platform.portal.security.authorization import PermissionDeniedError
from ai_platform.portal.telemetry.schema import (
    DistributionAggregate,
    DistributionBucket,
    DriftHealthStatus,
    FeatureQualityAggregate,
    InferenceTelemetryEnvelope,
    InferenceTelemetryScope,
    InferenceTelemetrySourceStatus,
    ReasonCount,
    TelemetrySourceAvailability,
    TelemetryWindow,
    TelemetryWindowRole,
)
from ai_platform.portal.telemetry.service import (
    InferenceTelemetryService,
    TelemetryAttributionError,
    TelemetryConflictError,
)


NOW = datetime(2026, 7, 24, 8, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(
    tenant_id: str,
    *permissions: Permission,
    actor_type: ActorType = ActorType.USER,
) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"{actor_type.value}-{tenant_id}",
        actor_type=actor_type,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _prepare_scope(session_factory: SessionFactory, tenant_id: str = "tenant-a") -> InferenceTelemetryScope:
    model_control = ModelControlService(session_factory, clock=lambda: NOW)
    model_control.register_model(
        _context(tenant_id, Permission.MODEL_TRAIN),
        ModelVersion(
            model_version_id="model-v1",
            tenant_id=tenant_id,
            model_family_id="family-v1",
            artifact_id="artifact-v1",
            artifact_sha256="1" * 64,
            feature_schema_version_id="features-v1",
            dataset_version_id="dataset-v1",
            training_window=TrainingWindow(
                start_at=NOW - timedelta(days=90),
                end_at=NOW - timedelta(days=30),
            ),
            training_pipeline_version_id="pipeline-v1",
            parameters=(),
            git_revision="revision-v1",
            created_at=NOW - timedelta(days=3),
            lifecycle_state=ModelLifecycleState.DRY_RUN,
        ),
    )
    ControlPlaneService(session_factory, clock=lambda: NOW).create_bot(
        _context(tenant_id, Permission.BOT_CREATE),
        "bot-1",
        "Telemetry bot",
        BotSpec(
            tenant_id=tenant_id,
            strategy_version="ai-directional-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-opaque-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency="USDT",
            runtime_version="freqtrade-2026.7",
            config_revision=1,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
    )
    with session_factory() as session:
        revision = BotRepository().get_revision(session, tenant_id, "bot-1", 1)
    assert revision is not None
    return InferenceTelemetryScope(
        tenant_id=tenant_id,
        model_version_id="model-v1",
        feature_schema_version_id="features-v1",
        bot_id="bot-1",
        bot_config_revision=1,
        bot_config_revision_id=revision.revision_id,
        runtime_id="runtime-bot-1-r1",
        source_id="freqai-runtime-aggregate-v1",
    )


def _distribution(distribution_id: str, low: int, high: int) -> DistributionAggregate:
    return DistributionAggregate(
        distribution_id=distribution_id,
        buckets=(
            DistributionBucket(bucket_id="low", count=low),
            DistributionBucket(bucket_id="high", count=high),
        ),
    )


def _envelope(
    scope: InferenceTelemetryScope,
    *,
    telemetry_id: str,
    role: TelemetryWindowRole,
    window_id: str,
    start_at: datetime,
    end_at: datetime,
    accepted: int = 180,
    rejected: int = 20,
    prediction_counts: tuple[int, int] = (100, 100),
    feature_counts: tuple[int, int] = (100, 100),
    missing: int = 0,
    invalid: int = 0,
) -> InferenceTelemetryEnvelope:
    present = accepted + rejected - missing - invalid
    assert sum(feature_counts) == present
    return InferenceTelemetryEnvelope(
        telemetry_id=UUID(telemetry_id),
        scope=scope,
        role=role,
        window=TelemetryWindow(
            window_id=window_id,
            start_at=start_at,
            end_at=end_at,
        ),
        generated_at=end_at + timedelta(minutes=1),
        accepted_predictions=accepted,
        rejected_predictions=rejected,
        rejection_reasons=(ReasonCount(reason_code="DO_PREDICT_FALSE", count=rejected),),
        feature_quality=(
            FeatureQualityAggregate(
                feature_name="rsi_14",
                present_count=present,
                missing_count=missing,
                invalid_count=invalid,
                distribution=_distribution("feature-rsi-bins-v1", *feature_counts),
            ),
        ),
        prediction_distribution=_distribution(
            "prediction-score-bins-v1",
            *prediction_counts,
        ),
        sampling_rate=Decimal("1"),
    )


def _source_status(
    scope: InferenceTelemetryScope,
    availability: TelemetrySourceAvailability = TelemetrySourceAvailability.AVAILABLE,
    reason_code: str = "SOURCE_HEALTHY",
) -> InferenceTelemetrySourceStatus:
    return InferenceTelemetrySourceStatus(
        scope=scope,
        availability=availability,
        checked_at=NOW + timedelta(hours=3),
        reason_code=reason_code,
    )


def _ingest_pair(
    service: InferenceTelemetryService,
    scope: InferenceTelemetryScope,
    *,
    observation_missing: int = 0,
    observation_feature_counts: tuple[int, int] = (98, 102),
) -> tuple[InferenceTelemetryEnvelope, InferenceTelemetryEnvelope]:
    context = _context(
        scope.tenant_id,
        Permission.MODEL_TRAIN,
        actor_type=ActorType.SERVICE,
    )
    reference = _envelope(
        scope,
        telemetry_id="11111111-1111-4111-8111-111111111111",
        role=TelemetryWindowRole.REFERENCE,
        window_id="reference-2026-07",
        start_at=NOW,
        end_at=NOW + timedelta(hours=1),
    )
    observation = _envelope(
        scope,
        telemetry_id="22222222-2222-4222-8222-222222222222",
        role=TelemetryWindowRole.OBSERVATION,
        window_id="observation-2026-07-24",
        start_at=NOW + timedelta(hours=1),
        end_at=NOW + timedelta(hours=2),
        feature_counts=observation_feature_counts,
        missing=observation_missing,
    )
    service.ingest_window(context, reference)
    service.ingest_window(context, observation)
    service.record_source_status(context, _source_status(scope))
    return reference, observation


def test_healthy_assessment_is_reproducible_and_does_not_mutate_model_control(
    session_factory: SessionFactory,
) -> None:
    scope = _prepare_scope(session_factory)
    service = InferenceTelemetryService(session_factory, clock=lambda: NOW + timedelta(hours=4))
    _ingest_pair(service, scope)
    read_context = _context("tenant-a", Permission.MODEL_READ)

    first = service.model_health(read_context)
    second = service.model_health(read_context)

    assert first == second
    assert len(first) == 1
    health = first[0]
    assert health.drift_status is DriftHealthStatus.HEALTHY
    assert health.drift_reason == "PSI_V1_WITHIN_LIMITS"
    assert health.policy_version == "psi-v1"
    assert health.reference_window_id == "reference-2026-07"
    assert health.observation_window_id == "observation-2026-07-24"
    assert health.runtime_id == "runtime-bot-1-r1"
    assert health.bot_config_revision_id == scope.bot_config_revision_id
    assert health.prediction_drift_score is not None

    model_control = ModelControlService(session_factory)
    model = model_control.get_model(read_context, "model-v1")
    assert model.lifecycle_state is ModelLifecycleState.DRY_RUN
    assert model_control.get_promotion_slot(read_context, "family-v1", Environment.TEST) is None


def test_insufficient_samples_feature_quality_and_source_outage_never_report_healthy(
    session_factory: SessionFactory,
) -> None:
    scope = _prepare_scope(session_factory)
    service = InferenceTelemetryService(session_factory, clock=lambda: NOW + timedelta(hours=4))
    ingest_context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        actor_type=ActorType.SERVICE,
    )
    reference = _envelope(
        scope,
        telemetry_id="33333333-3333-4333-8333-333333333333",
        role=TelemetryWindowRole.REFERENCE,
        window_id="reference-small",
        start_at=NOW,
        end_at=NOW + timedelta(hours=1),
        accepted=40,
        rejected=10,
        prediction_counts=(25, 25),
        feature_counts=(25, 25),
    )
    observation = _envelope(
        scope,
        telemetry_id="44444444-4444-4444-8444-444444444444",
        role=TelemetryWindowRole.OBSERVATION,
        window_id="observation-small",
        start_at=NOW + timedelta(hours=1),
        end_at=NOW + timedelta(hours=2),
        accepted=40,
        rejected=10,
        prediction_counts=(25, 25),
        feature_counts=(25, 25),
    )
    service.ingest_window(ingest_context, reference)
    service.ingest_window(ingest_context, observation)
    service.record_source_status(ingest_context, _source_status(scope))

    health = service.model_health(_context("tenant-a", Permission.MODEL_READ))[0]
    assert health.drift_status is DriftHealthStatus.INSUFFICIENT_EVIDENCE
    assert health.drift_reason == "MINIMUM_SAMPLE_COUNT_NOT_MET"

    service.record_source_status(
        ingest_context,
        _source_status(
            scope,
            TelemetrySourceAvailability.UNAVAILABLE,
            "RUNTIME_TELEMETRY_TIMEOUT",
        ),
    )
    unavailable = service.model_health(_context("tenant-a", Permission.MODEL_READ))[0]
    assert unavailable.drift_status is DriftHealthStatus.UNAVAILABLE
    assert unavailable.drift_reason == "RUNTIME_TELEMETRY_TIMEOUT"


def test_feature_quality_degradation_is_explicit(session_factory: SessionFactory) -> None:
    scope = _prepare_scope(session_factory)
    service = InferenceTelemetryService(session_factory, clock=lambda: NOW + timedelta(hours=4))
    _ingest_pair(
        service,
        scope,
        observation_missing=20,
        observation_feature_counts=(90, 90),
    )

    health = service.model_health(_context("tenant-a", Permission.MODEL_READ))[0]
    assert health.drift_status is DriftHealthStatus.DEGRADED
    assert health.drift_reason == "FEATURE_QUALITY_DEGRADED"
    assert health.max_feature_quality_issue_rate == Decimal("0.100000")


def test_ingestion_is_service_only_tenant_scoped_attributed_and_idempotent(
    session_factory: SessionFactory,
) -> None:
    scope = _prepare_scope(session_factory)
    service = InferenceTelemetryService(session_factory)
    envelope = _envelope(
        scope,
        telemetry_id="55555555-5555-4555-8555-555555555555",
        role=TelemetryWindowRole.REFERENCE,
        window_id="reference-idempotent",
        start_at=NOW,
        end_at=NOW + timedelta(hours=1),
    )

    with pytest.raises(PermissionDeniedError):
        service.ingest_window(_context("tenant-a", Permission.MODEL_TRAIN), envelope)
    with pytest.raises(PermissionDeniedError):
        service.ingest_window(
            _context("tenant-b", Permission.MODEL_TRAIN, actor_type=ActorType.SERVICE),
            envelope,
        )

    ingest_context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        actor_type=ActorType.SERVICE,
    )
    assert service.ingest_window(ingest_context, envelope) == envelope
    assert service.ingest_window(ingest_context, envelope) == envelope
    assert service.list_windows(_context("tenant-a", Permission.MODEL_READ)) == (envelope,)
    assert service.list_windows(_context("tenant-b", Permission.MODEL_READ)) == ()

    conflicting = envelope.model_copy(update={"sampling_rate": Decimal("0.5")})
    with pytest.raises(TelemetryConflictError):
        service.ingest_window(ingest_context, conflicting)

    mismatched_scope = scope.model_copy(update={"feature_schema_version_id": "features-other"})
    mismatched = envelope.model_copy(
        update={
            "telemetry_id": UUID("66666666-6666-4666-8666-666666666666"),
            "scope": mismatched_scope,
        }
    )
    with pytest.raises(TelemetryAttributionError):
        service.ingest_window(ingest_context, mismatched)


def test_api_exposes_only_aggregate_telemetry_and_measured_health(
    session_factory: SessionFactory,
) -> None:
    scope = _prepare_scope(session_factory)
    telemetry = InferenceTelemetryService(
        session_factory,
        clock=lambda: NOW + timedelta(hours=4),
    )
    holder = {
        "context": _context(
            "tenant-a",
            Permission.MODEL_TRAIN,
            actor_type=ActorType.SERVICE,
        )
    }
    client = TestClient(
        create_app(
            session_factory,
            lambda: holder["context"],
            inference_telemetry_service=telemetry,
        )
    )
    reference, observation = _ingest_pair(telemetry, scope)

    duplicate = client.post(
        "/v1/inference-telemetry/windows",
        json=reference.model_dump(mode="json"),
    )
    assert duplicate.status_code == 201
    status = client.post(
        "/v1/inference-telemetry/source-status",
        json=_source_status(scope).model_dump(mode="json"),
    )
    assert status.status_code == 200

    holder["context"] = _context("tenant-a", Permission.MODEL_READ)
    windows = client.get("/v1/inference-telemetry/windows")
    assert windows.status_code == 200
    assert {item["telemetry_id"] for item in windows.json()} == {
        str(reference.telemetry_id),
        str(observation.telemetry_id),
    }
    health = client.get("/v1/model-health")
    assert health.status_code == 200
    assert health.json()[0]["drift_status"] == "HEALTHY"
    serialized = str({"windows": windows.json(), "health": health.json()}).lower()
    for forbidden in (
        "raw_feature_value",
        "individual_prediction",
        "api_key",
        "api_secret",
        "private_endpoint",
        "authorization",
    ):
        assert forbidden not in serialized


def test_envelope_rejects_raw_or_protected_holdout_claims(
    session_factory: SessionFactory,
) -> None:
    scope = _prepare_scope(session_factory)
    valid = _envelope(
        scope,
        telemetry_id="77777777-7777-4777-8777-777777777777",
        role=TelemetryWindowRole.REFERENCE,
        window_id="reference-validation",
        start_at=NOW,
        end_at=NOW + timedelta(hours=1),
    )
    with pytest.raises(ValueError, match="aggregate-only"):
        InferenceTelemetryEnvelope.model_validate(
            {**valid.model_dump(mode="json"), "aggregate_only": False}
        )
    with pytest.raises(ValueError, match="protected final holdout"):
        InferenceTelemetryEnvelope.model_validate(
            {**valid.model_dump(mode="json"), "protected_holdout_included": True}
        )


def test_migration_declares_all_durable_pi03_tables() -> None:
    migration = Path(
        "ai_platform/portal/telemetry/migrations/0001_inference_drift_telemetry.sql"
    ).read_text(encoding="utf-8")
    assert "CREATE TABLE portal_inference_telemetry_windows" in migration
    assert "CREATE TABLE portal_inference_telemetry_source_status" in migration
    assert "CREATE TABLE portal_inference_drift_assessments" in migration
    assert "telemetry_json TEXT NOT NULL" in migration
    assert "assessment_json TEXT NOT NULL" in migration
