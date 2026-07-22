from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai_platform.portal.contracts.audit import AuditAction
from ai_platform.portal.contracts.bots import BotConfigRevision
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.events import EventType
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.models import (
    ModelLifecycleState,
    ModelParameter,
    ModelVersion,
    TrainingWindow,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.model_control.database import create_model_control_schema
from ai_platform.portal.model_control.repository import ModelControlRepository
from ai_platform.portal.model_control.schema import ModelPromotionAction
from ai_platform.portal.model_control.service import (
    ModelControlConflictError,
    ModelControlService,
    ModelNotAssignableError,
    ModelNotFoundError,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


NOW = datetime(2026, 7, 22, 18, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_model_control_schema(engine)
    return build_session_factory(engine)


def _context(
    tenant_id: str,
    *permissions: Permission,
    correlation_id: UUID | None = None,
) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.USER,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=correlation_id or uuid4(),
        causation_id=uuid4(),
    )


def _model(
    tenant_id: str,
    model_version_id: str,
    *,
    family: str = "family-1",
    lifecycle_state: ModelLifecycleState = ModelLifecycleState.VALIDATED,
    artifact_sha256: str = HASH_A,
) -> ModelVersion:
    return ModelVersion(
        model_version_id=model_version_id,
        tenant_id=tenant_id,
        model_family_id=family,
        artifact_id=f"artifact-{model_version_id}",
        artifact_sha256=artifact_sha256,
        feature_schema_version_id="features-v1",
        dataset_version_id="dataset-v1",
        training_window=TrainingWindow(
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            end_at=datetime(2026, 2, 1, tzinfo=UTC),
        ),
        training_pipeline_version_id="pipeline-v1",
        parameters=(ModelParameter(name="learning_rate", value_json="0.05"),),
        git_revision="abcdef123456",
        created_at=NOW,
        lifecycle_state=lifecycle_state,
    )


def _revision(
    tenant_id: str,
    model_version_id: str,
    *,
    environment: Environment = Environment.TEST,
) -> BotConfigRevision:
    return BotConfigRevision(
        revision_id=str(uuid4()),
        tenant_id=tenant_id,
        bot_id="bot-1",
        revision=1,
        strategy_version="strategy-v1",
        model_version=model_version_id,
        risk_policy_version="risk-v1",
        exchange_connection_ref="exchange-1",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1000",
        capital_currency="USDT",
        runtime_version="freqtrade-2026.7",
        environment=environment,
        execution_mode=ExecutionMode.DRY_RUN,
        created_by_actor_id=f"actor-{tenant_id}",
        created_at=NOW,
    )


def test_registration_persists_immutable_model_audit_and_outbox_without_activation(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.MODEL_TRAIN, Permission.MODEL_READ)
    service = ModelControlService(session_factory, clock=lambda: NOW)
    model_repository = ModelControlRepository()
    evidence_repository = BotRepository()
    model = _model("tenant-a", "model-v1")

    registered = service.register_model(context, model)

    assert registered == model
    assert service.get_promotion_slot(context, "family-1", Environment.TEST) is None
    with session_factory() as session:
        persisted = model_repository.get_model(session, "tenant-a", "model-v1")
        audits = evidence_repository.list_audit_events(session, "tenant-a", "model", "model-v1")
        outbox = evidence_repository.list_outbox_events(session, "tenant-a", "model", "model-v1")

    assert persisted == model
    assert persisted is not model
    assert [event.action for event in audits] == [AuditAction.MODEL_REGISTERED]
    assert [event.event_type for event in outbox] == [EventType.MODEL_REGISTERED]
    assert audits[0].correlation_id == context.correlation_id
    assert outbox[0].correlation_id == context.correlation_id


def test_duplicate_model_identity_cannot_overwrite_immutable_metadata(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.MODEL_TRAIN, Permission.MODEL_READ)
    service = ModelControlService(session_factory, clock=lambda: NOW)
    original = _model("tenant-a", "model-v1", artifact_sha256=HASH_A)
    conflicting = _model("tenant-a", "model-v1", artifact_sha256=HASH_B)
    service.register_model(context, original)

    with pytest.raises(ModelControlConflictError, match="already exists"):
        service.register_model(context, conflicting)

    assert service.get_model(context, "model-v1").artifact_sha256 == HASH_A


def test_model_reads_are_tenant_scoped(session_factory: SessionFactory) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    tenant_a = _context("tenant-a", Permission.MODEL_TRAIN, Permission.MODEL_READ)
    tenant_b = _context("tenant-b", Permission.MODEL_READ, Permission.MODEL_PROMOTE)
    service.register_model(tenant_a, _model("tenant-a", "shared-id"))

    with pytest.raises(ModelNotFoundError):
        service.get_model(tenant_b, "shared-id")
    with pytest.raises(ModelNotFoundError):
        service.promote_model(tenant_b, "shared-id", Environment.TEST)
    assert service.list_models(tenant_b) == ()


def test_model_permissions_fail_closed(session_factory: SessionFactory) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    no_permissions = _context("tenant-a")

    with pytest.raises(PermissionDeniedError):
        service.register_model(no_permissions, _model("tenant-a", "model-v1"))
    with pytest.raises(PermissionDeniedError):
        service.list_models(no_permissions)


@pytest.mark.parametrize(
    "state",
    [
        ModelLifecycleState.EXPERIMENTAL,
        ModelLifecycleState.CANDIDATE,
        ModelLifecycleState.LIVE_SMALL,
        ModelLifecycleState.PRODUCTION,
        ModelLifecycleState.DEPRECATED,
        ModelLifecycleState.REJECTED,
    ],
)
def test_nonassignable_lifecycle_states_cannot_be_promoted(
    session_factory: SessionFactory,
    state: ModelLifecycleState,
) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.MODEL_TRAIN, Permission.MODEL_PROMOTE)
    model_id = f"model-{state.value.lower()}"
    service.register_model(context, _model("tenant-a", model_id, lifecycle_state=state))

    with pytest.raises(ModelNotAssignableError, match="not assignable"):
        service.promote_model(context, model_id, Environment.TEST)


def test_promotion_is_explicit_audited_and_does_not_mutate_model_metadata(
    session_factory: SessionFactory,
) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    repository = ModelControlRepository()
    evidence_repository = BotRepository()
    context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        Permission.MODEL_PROMOTE,
        Permission.MODEL_READ,
    )
    model = _model("tenant-a", "model-v1")
    service.register_model(context, model)

    slot = service.promote_model(context, "model-v1", Environment.TEST)

    assert slot.model_version_id == "model-v1"
    assert service.get_model(context, "model-v1") == model
    with session_factory() as session:
        history = repository.list_transitions(session, "tenant-a", "family-1", Environment.TEST)
        audits = evidence_repository.list_audit_events(session, "tenant-a", "model", "model-v1")
        outbox = evidence_repository.list_outbox_events(session, "tenant-a", "model", "model-v1")

    assert [transition.action for transition in history] == [ModelPromotionAction.PROMOTE]
    assert history[0].from_model_version_id is None
    assert history[0].to_model_version_id == "model-v1"
    assert {event.action for event in audits} == {
        AuditAction.MODEL_REGISTERED,
        AuditAction.MODEL_PROMOTED,
    }
    assert {event.event_type for event in outbox} == {
        EventType.MODEL_REGISTERED,
        EventType.MODEL_PROMOTED,
    }


def test_registering_another_candidate_does_not_replace_promoted_slot(
    session_factory: SessionFactory,
) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        Permission.MODEL_PROMOTE,
        Permission.MODEL_READ,
    )
    service.register_model(context, _model("tenant-a", "model-v1"))
    service.promote_model(context, "model-v1", Environment.TEST)
    service.register_model(
        context,
        _model(
            "tenant-a",
            "model-v2",
            lifecycle_state=ModelLifecycleState.CANDIDATE,
            artifact_sha256=HASH_B,
        ),
    )

    slot = service.get_promotion_slot(context, "family-1", Environment.TEST)
    assert slot is not None
    assert slot.model_version_id == "model-v1"


def test_rollback_selects_previously_promoted_immutable_version(
    session_factory: SessionFactory,
) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    repository = ModelControlRepository()
    evidence_repository = BotRepository()
    context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        Permission.MODEL_PROMOTE,
        Permission.MODEL_READ,
    )
    service.register_model(context, _model("tenant-a", "model-v1"))
    service.register_model(context, _model("tenant-a", "model-v2", artifact_sha256=HASH_B))
    service.promote_model(context, "model-v1", Environment.TEST)
    service.promote_model(context, "model-v2", Environment.TEST)

    slot = service.rollback_model(context, "family-1", Environment.TEST, "model-v1")

    assert slot.model_version_id == "model-v1"
    with session_factory() as session:
        history = repository.list_transitions(session, "tenant-a", "family-1", Environment.TEST)
        audits = evidence_repository.list_audit_events(session, "tenant-a", "model", "model-v1")
        outbox = evidence_repository.list_outbox_events(session, "tenant-a", "model", "model-v1")

    assert [transition.action for transition in history] == [
        ModelPromotionAction.PROMOTE,
        ModelPromotionAction.PROMOTE,
        ModelPromotionAction.ROLLBACK,
    ]
    assert history[-1].from_model_version_id == "model-v2"
    assert history[-1].to_model_version_id == "model-v1"
    assert AuditAction.MODEL_ROLLED_BACK in {event.action for event in audits}
    assert EventType.MODEL_ROLLED_BACK in {event.event_type for event in outbox}


def test_rollback_rejects_never_promoted_or_different_family_target(
    session_factory: SessionFactory,
) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.MODEL_TRAIN, Permission.MODEL_PROMOTE)
    service.register_model(context, _model("tenant-a", "model-v1"))
    service.register_model(context, _model("tenant-a", "model-v2", artifact_sha256=HASH_B))
    service.register_model(context, _model("tenant-a", "other-v1", family="family-2"))
    service.promote_model(context, "model-v1", Environment.TEST)

    with pytest.raises(ModelControlConflictError, match="not previously promoted"):
        service.rollback_model(context, "family-1", Environment.TEST, "model-v2")
    with pytest.raises(ModelControlConflictError, match="different model family"):
        service.rollback_model(context, "family-1", Environment.TEST, "other-v1")


def test_new_assignment_guard_accepts_only_current_promoted_model_without_mutation(
    session_factory: SessionFactory,
) -> None:
    service = ModelControlService(session_factory, clock=lambda: NOW)
    context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        Permission.MODEL_PROMOTE,
        Permission.MODEL_READ,
    )
    model = _model("tenant-a", "model-v1")
    service.register_model(context, model)
    service.register_model(context, _model("tenant-a", "model-v2", artifact_sha256=HASH_B))
    service.promote_model(context, "model-v1", Environment.TEST)
    revision = _revision("tenant-a", "model-v1")
    revision_json = revision.canonical_json()

    assert service.validate_new_assignment(context, revision) == model
    assert revision.canonical_json() == revision_json

    with pytest.raises(ModelNotAssignableError, match="not the promoted model"):
        service.validate_new_assignment(context, _revision("tenant-a", "model-v2"))
    with pytest.raises(PermissionDeniedError, match="tenant scope mismatch"):
        service.validate_new_assignment(context, _revision("tenant-b", "model-v1"))


class _FailingOutboxRepository(ModelControlRepository):
    def add_outbox_event(self, session, event) -> None:
        raise RuntimeError("simulated outbox failure")


def test_registration_rolls_back_when_outbox_write_fails(
    session_factory: SessionFactory,
) -> None:
    repository = _FailingOutboxRepository()
    service = ModelControlService(session_factory, repository=repository, clock=lambda: NOW)
    context = _context("tenant-a", Permission.MODEL_TRAIN)
    evidence_repository = BotRepository()

    with pytest.raises(RuntimeError, match="simulated outbox failure"):
        service.register_model(context, _model("tenant-a", "model-v1"))

    with session_factory() as session:
        assert repository.get_model(session, "tenant-a", "model-v1") is None
        assert evidence_repository.list_audit_events(session, "tenant-a") == ()
        assert evidence_repository.list_outbox_events(session, "tenant-a") == ()


def test_promotion_slot_and_history_roll_back_when_outbox_write_fails(
    session_factory: SessionFactory,
) -> None:
    normal_service = ModelControlService(session_factory, clock=lambda: NOW)
    normal_repository = ModelControlRepository()
    context = _context(
        "tenant-a",
        Permission.MODEL_TRAIN,
        Permission.MODEL_PROMOTE,
        Permission.MODEL_READ,
    )
    normal_service.register_model(context, _model("tenant-a", "model-v1"))
    normal_service.register_model(context, _model("tenant-a", "model-v2", artifact_sha256=HASH_B))
    normal_service.promote_model(context, "model-v1", Environment.TEST)

    failing_service = ModelControlService(
        session_factory,
        repository=_FailingOutboxRepository(),
        clock=lambda: NOW,
    )
    with pytest.raises(RuntimeError, match="simulated outbox failure"):
        failing_service.promote_model(context, "model-v2", Environment.TEST)

    with session_factory() as session:
        slot = normal_repository.get_slot(session, "tenant-a", "family-1", Environment.TEST)
        history = normal_repository.list_transitions(
            session,
            "tenant-a",
            "family-1",
            Environment.TEST,
        )

    assert slot is not None
    assert slot.model_version_id == "model-v1"
    assert [transition.to_model_version_id for transition in history] == ["model-v1"]
