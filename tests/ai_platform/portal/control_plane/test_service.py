from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai_platform.portal.contracts.audit import AuditAction
from ai_platform.portal.contracts.bots import (
    BotConfigRevisionState,
    BotDesiredState,
    BotSpec,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.events import EventType
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.runtime_generation import RuntimeGenerationMaterial
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import (
    BotNotFoundError,
    ControlPlaneConflictError,
    ControlPlaneService,
    RuntimeGenerationMaterialUnavailableError,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
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


def _spec(tenant_id: str, revision: int = 1) -> BotSpec:
    return BotSpec(
        tenant_id=tenant_id,
        strategy_version="strategy-v1",
        model_version="model-v1",
        risk_policy_version="risk-v1",
        exchange_connection_ref="exchange-connection-1",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1000",
        capital_currency="USDT",
        runtime_version="freqtrade-2026.7",
        config_revision=revision,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
    )


def _generation_material(*_args: object) -> RuntimeGenerationMaterial:
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest="1" * 64,
        runtime_image_digest="2" * 64,
        strategy_artifact_digest="3" * 64,
        model_artifact_digest="4" * 64,
        feature_schema_version="features-v1",
        risk_policy_digest="5" * 64,
        exchange_mode="dry-run-public-market-data",
        exchange_connection_revision="exchange-revision-1",
        isolation_profile_version="isolation-v1",
        isolation_profile_digest="6" * 64,
        gateway_contract_version="gateway-v1",
    )


def _service(session_factory: SessionFactory) -> ControlPlaneService:
    return ControlPlaneService(
        session_factory,
        clock=lambda: NOW,
        generation_material_resolver=_generation_material,
    )


def test_create_bot_persists_initial_revision_audit_and_outbox_atomically(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.BOT_CREATE)
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    repository = BotRepository()

    bot = service.create_bot(context, "bot-1", "Test bot", _spec("tenant-a"))

    assert bot.desired_state is BotDesiredState.CREATED
    assert bot.observed_state.value == "CREATED"
    assert bot.latest_authored_revision_id is not None
    assert bot.desired_revision_id is None
    assert bot.desired_runtime_generation_id is None
    assert bot.observed_runtime_generation_id is None
    assert bot.state_version == 1
    with session_factory() as session:
        revisions = repository.list_revisions(session, "tenant-a", "bot-1")
        audits = repository.list_audit_events(session, "tenant-a", "bot", "bot-1")
        outbox = repository.list_outbox_events(session, "tenant-a", "bot", "bot-1")

    assert [revision.revision for revision in revisions] == [1]
    assert revisions[0].state is BotConfigRevisionState.DRAFT
    assert audits[0].action is AuditAction.BOT_CREATED
    assert outbox[0].event_type is EventType.BOT_CREATED
    assert audits[0].correlation_id == context.correlation_id
    assert outbox[0].correlation_id == context.correlation_id


def test_repository_and_service_reads_are_tenant_scoped(session_factory: SessionFactory) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    repository = BotRepository()
    tenant_a = _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_READ)
    tenant_b = _context("tenant-b", Permission.BOT_READ)
    service.create_bot(tenant_a, "bot-1", "Tenant A bot", _spec("tenant-a"))

    with session_factory() as session:
        assert repository.get_bot(session, "tenant-b", "bot-1") is None
        assert repository.list_bots(session, "tenant-b") == ()

    with pytest.raises(BotNotFoundError):
        service.get_bot(tenant_b, "bot-1")
    assert service.list_bots(tenant_b) == ()


def test_create_and_read_permissions_fail_closed(session_factory: SessionFactory) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    no_permissions = _context("tenant-a")

    with pytest.raises(PermissionDeniedError):
        service.create_bot(no_permissions, "bot-1", "Denied bot", _spec("tenant-a"))
    with pytest.raises(PermissionDeniedError):
        service.list_bots(no_permissions)


def test_cross_tenant_spec_is_rejected_even_with_create_permission(
    session_factory: SessionFactory,
) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.BOT_CREATE)

    with pytest.raises(PermissionDeniedError, match="tenant scope mismatch"):
        service.create_bot(context, "bot-1", "Wrong tenant", _spec("tenant-b"))


def test_save_draft_changes_latest_authored_but_not_desired_or_observed_generation(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    repository = BotRepository()
    context = _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_READ)
    created = service.create_bot(context, "bot-1", "Revision bot", _spec("tenant-a", 1))
    first_revision_id = created.latest_authored_revision_id

    revision_two_spec = _spec("tenant-a", 2).model_copy(update={"model_version": "model-v2"})
    updated = service.revise_bot(context, "bot-1", revision_two_spec)

    with session_factory() as session:
        revisions = repository.list_revisions(session, "tenant-a", "bot-1")
        audits = repository.list_audit_events(session, "tenant-a", "bot", "bot-1")
        outbox = repository.list_outbox_events(session, "tenant-a", "bot", "bot-1")

    assert [revision.revision for revision in revisions] == [1, 2]
    assert revisions[0].model_version == "model-v1"
    assert revisions[1].model_version == "model-v2"
    assert revisions[1].state is BotConfigRevisionState.DRAFT
    assert updated.spec.config_revision == 2
    assert updated.spec.model_version == "model-v2"
    assert updated.latest_authored_revision_id != first_revision_id
    assert updated.desired_revision_id is None
    assert updated.desired_runtime_generation_id is None
    assert updated.observed_runtime_generation_id is None
    assert {audit.action for audit in audits} == {
        AuditAction.BOT_CREATED,
        AuditAction.BOT_CONFIG_REVISED,
    }
    assert {event.event_type for event in outbox} == {
        EventType.BOT_CREATED,
        EventType.BOT_CONFIG_REVISED,
    }


def test_revision_number_must_be_monotonic(session_factory: SessionFactory) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.BOT_CREATE)
    service.create_bot(context, "bot-1", "Revision bot", _spec("tenant-a", 1))

    with pytest.raises(ControlPlaneConflictError, match="next immutable revision: 2"):
        service.revise_bot(context, "bot-1", _spec("tenant-a", 3))


def test_apply_draft_fails_closed(session_factory: SessionFactory) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Draft bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None

    with pytest.raises(ControlPlaneConflictError, match="only PROMOTED"):
        service.apply_revision(
            context,
            "bot-1",
            created.latest_authored_revision_id,
            created.state_version,
            "apply-draft",
        )


def test_apply_without_trusted_generation_material_fails_closed(
    session_factory: SessionFactory,
) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Material bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    promoted = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        created.state_version,
    )

    with pytest.raises(RuntimeGenerationMaterialUnavailableError, match="resolver"):
        service.apply_revision(
            context,
            "bot-1",
            promoted.revision_id,
            2,
            "apply-no-material",
        )


def test_explicit_apply_is_idempotent_and_updates_only_desired_generation(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Apply bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    promoted = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        created.state_version,
    )

    first = service.apply_revision(context, "bot-1", promoted.revision_id, 2, "apply-r1")
    retry = service.apply_revision(context, "bot-1", promoted.revision_id, 2, "apply-r1")

    first_bot, first_generation, first_rollout = first
    retry_bot, retry_generation, retry_rollout = retry
    assert first_generation.generation_id == retry_generation.generation_id
    assert first_rollout.rollout_id == retry_rollout.rollout_id
    assert first_bot.desired_revision_id == promoted.revision_id
    assert first_bot.desired_runtime_generation_id == first_generation.generation_id
    assert first_bot.observed_runtime_generation_id is None
    assert retry_bot.state_version == first_bot.state_version == 3


def test_same_idempotency_key_with_different_semantic_request_conflicts(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Idempotency bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    r1 = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        1,
    )
    service.apply_revision(context, "bot-1", r1.revision_id, 2, "same-key")
    revised = service.revise_bot(context, "bot-1", _spec("tenant-a", 2))
    assert revised.latest_authored_revision_id is not None
    r2 = service.promote_revision(
        context,
        "bot-1",
        revised.latest_authored_revision_id,
        revised.state_version,
    )

    with pytest.raises(ControlPlaneConflictError, match="different semantic request"):
        service.apply_revision(context, "bot-1", r2.revision_id, 5, "same-key")


def test_stale_expected_state_version_conflicts(session_factory: SessionFactory) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Version bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    promoted = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        1,
    )

    with pytest.raises(ControlPlaneConflictError, match="stale expected_state_version"):
        service.apply_revision(context, "bot-1", promoted.revision_id, 1, "stale-apply")


def test_explicit_restart_same_revision_creates_new_generation(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_START)
    created = service.create_bot(context, "bot-1", "Restart bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    promoted = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        1,
    )
    _, generation_one, _ = service.apply_revision(
        context, "bot-1", promoted.revision_id, 2, "apply-r1"
    )

    restarted, generation_two, _ = service.restart_with_revision(
        context,
        "bot-1",
        promoted.revision_id,
        3,
        "restart-r1",
    )

    assert generation_two.generation_id != generation_one.generation_id
    assert generation_two.generation_ordinal == generation_one.generation_ordinal + 1
    assert generation_two.config_revision_id == generation_one.config_revision_id
    assert restarted.desired_runtime_generation_id == generation_two.generation_id
    assert restarted.observed_runtime_generation_id is None


def test_rollback_to_promoted_revision_creates_new_generation(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Rollback bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    r1 = service.promote_revision(context, "bot-1", created.latest_authored_revision_id, 1)
    _, g1, _ = service.apply_revision(context, "bot-1", r1.revision_id, 2, "apply-r1")

    revised = service.revise_bot(context, "bot-1", _spec("tenant-a", 2))
    assert revised.latest_authored_revision_id is not None
    r2 = service.promote_revision(
        context,
        "bot-1",
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    _, g2, _ = service.apply_revision(context, "bot-1", r2.revision_id, 5, "apply-r2")

    rolled_back, g3, _ = service.rollback_to_revision(
        context,
        "bot-1",
        r1.revision_id,
        6,
        "rollback-r1",
    )

    assert g3.generation_id not in {g1.generation_id, g2.generation_id}
    assert g3.generation_ordinal == 3
    assert g3.config_revision_id == r1.revision_id
    assert rolled_back.desired_runtime_generation_id == g3.generation_id


def test_deprecated_revision_cannot_be_promoted_or_rolled_back(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE)
    created = service.create_bot(context, "bot-1", "Deprecated bot", _spec("tenant-a"))
    assert created.latest_authored_revision_id is not None
    r1 = service.promote_revision(context, "bot-1", created.latest_authored_revision_id, 1)
    service.apply_revision(context, "bot-1", r1.revision_id, 2, "apply-r1")
    deprecated = service.deprecate_revision(context, "bot-1", r1.revision_id, 3)
    assert deprecated.state is BotConfigRevisionState.DEPRECATED

    with pytest.raises(ControlPlaneConflictError, match="deprecated revision cannot be promoted"):
        service.promote_revision(context, "bot-1", r1.revision_id, 4)
    with pytest.raises(ControlPlaneConflictError, match="only PROMOTED"):
        service.rollback_to_revision(context, "bot-1", r1.revision_id, 4, "rollback-deprecated")


def test_running_intent_requires_explicit_desired_generation(
    session_factory: SessionFactory,
) -> None:
    service = _service(session_factory)
    context = _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_START)
    created = service.create_bot(context, "bot-1", "State bot", _spec("tenant-a"))

    with pytest.raises(ControlPlaneConflictError, match="no desired RuntimeGeneration"):
        service.set_desired_state(context, "bot-1", BotDesiredState.RUNNING)

    assert created.latest_authored_revision_id is not None
    promoted = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        created.state_version,
    )
    applied, _, _ = service.apply_revision(
        context,
        "bot-1",
        promoted.revision_id,
        2,
        "apply-for-start",
    )
    updated = service.set_desired_state(context, "bot-1", BotDesiredState.RUNNING)

    assert updated.desired_state is BotDesiredState.RUNNING
    assert updated.observed_state == created.observed_state
    assert updated.observed_runtime_generation_id is None
    assert updated.desired_runtime_generation_id == applied.desired_runtime_generation_id


@pytest.mark.parametrize(
    ("desired_state", "required_permission"),
    [
        (BotDesiredState.PAUSED, Permission.BOT_PAUSE),
        (BotDesiredState.STOPPED, Permission.BOT_STOP),
    ],
)
def test_non_running_desired_state_commands_require_explicit_permission(
    session_factory: SessionFactory,
    desired_state: BotDesiredState,
    required_permission: Permission,
) -> None:
    service = _service(session_factory)
    creator = _context("tenant-a", Permission.BOT_CREATE)
    service.create_bot(creator, "bot-1", "State bot", _spec("tenant-a"))

    with pytest.raises(PermissionDeniedError):
        service.set_desired_state(creator, "bot-1", desired_state)

    authorized = _context("tenant-a", required_permission)
    updated = service.set_desired_state(authorized, "bot-1", desired_state)
    assert updated.desired_state is desired_state


def test_created_is_not_a_valid_desired_state_command(session_factory: SessionFactory) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    context = _context("tenant-a", Permission.BOT_CREATE)
    service.create_bot(context, "bot-1", "State bot", _spec("tenant-a"))

    with pytest.raises(ValueError, match="RUNNING, PAUSED or STOPPED"):
        service.set_desired_state(context, "bot-1", BotDesiredState.CREATED)


class _FailingOutboxRepository(BotRepository):
    def add_outbox_event(self, session, event) -> None:
        raise RuntimeError("simulated outbox failure")


def test_domain_state_rolls_back_when_outbox_write_fails(session_factory: SessionFactory) -> None:
    repository = _FailingOutboxRepository()
    service = ControlPlaneService(session_factory, repository=repository, clock=lambda: NOW)
    context = _context("tenant-a", Permission.BOT_CREATE)

    with pytest.raises(RuntimeError, match="simulated outbox failure"):
        service.create_bot(context, "bot-1", "Rollback bot", _spec("tenant-a"))

    with session_factory() as session:
        assert repository.get_bot(session, "tenant-a", "bot-1") is None
        assert repository.list_revisions(session, "tenant-a", "bot-1") == ()
        assert repository.list_audit_events(session, "tenant-a") == ()
        assert repository.list_outbox_events(session, "tenant-a") == ()
