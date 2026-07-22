from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai_platform.portal.contracts.audit import AuditAction
from ai_platform.portal.contracts.bots import BotDesiredState, BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.events import EventType
from ai_platform.portal.contracts.identity import ActorType, Permission
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


def test_create_bot_persists_initial_revision_audit_and_outbox_atomically(
    session_factory: SessionFactory,
) -> None:
    context = _context("tenant-a", Permission.BOT_CREATE)
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    repository = BotRepository()

    bot = service.create_bot(context, "bot-1", "Test bot", _spec("tenant-a"))

    assert bot.desired_state is BotDesiredState.CREATED
    assert bot.observed_state.value == "CREATED"
    with session_factory() as session:
        revisions = repository.list_revisions(session, "tenant-a", "bot-1")
        audits = repository.list_audit_events(session, "tenant-a", "bot", "bot-1")
        outbox = repository.list_outbox_events(session, "tenant-a", "bot", "bot-1")

    assert [revision.revision for revision in revisions] == [1]
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


def test_revisions_append_without_mutating_previous_revision(
    session_factory: SessionFactory,
) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    repository = BotRepository()
    context = _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_READ)
    service.create_bot(context, "bot-1", "Revision bot", _spec("tenant-a", 1))

    revision_two_spec = _spec("tenant-a", 2).model_copy(update={"model_version": "model-v2"})
    updated = service.revise_bot(context, "bot-1", revision_two_spec)

    with session_factory() as session:
        revisions = repository.list_revisions(session, "tenant-a", "bot-1")
        audits = repository.list_audit_events(session, "tenant-a", "bot", "bot-1")
        outbox = repository.list_outbox_events(session, "tenant-a", "bot", "bot-1")

    assert [revision.revision for revision in revisions] == [1, 2]
    assert revisions[0].model_version == "model-v1"
    assert revisions[1].model_version == "model-v2"
    assert updated.spec.config_revision == 2
    assert updated.spec.model_version == "model-v2"
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


def test_desired_state_command_does_not_change_observed_state(
    session_factory: SessionFactory,
) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
    repository = BotRepository()
    context = _context("tenant-a", Permission.BOT_CREATE, Permission.BOT_START)
    created = service.create_bot(context, "bot-1", "State bot", _spec("tenant-a"))

    updated = service.set_desired_state(context, "bot-1", BotDesiredState.RUNNING)

    assert created.observed_state == updated.observed_state
    assert updated.desired_state is BotDesiredState.RUNNING
    with session_factory() as session:
        audits = repository.list_audit_events(session, "tenant-a", "bot", "bot-1")
        outbox = repository.list_outbox_events(session, "tenant-a", "bot", "bot-1")
    assert {audit.action for audit in audits} == {
        AuditAction.BOT_CREATED,
        AuditAction.BOT_START_REQUESTED,
    }
    assert {event.event_type for event in outbox} == {
        EventType.BOT_CREATED,
        EventType.BOT_START_REQUESTED,
    }


@pytest.mark.parametrize(
    ("desired_state", "required_permission"),
    [
        (BotDesiredState.RUNNING, Permission.BOT_START),
        (BotDesiredState.PAUSED, Permission.BOT_PAUSE),
        (BotDesiredState.STOPPED, Permission.BOT_STOP),
    ],
)
def test_desired_state_commands_require_explicit_permission(
    session_factory: SessionFactory,
    desired_state: BotDesiredState,
    required_permission: Permission,
) -> None:
    service = ControlPlaneService(session_factory, clock=lambda: NOW)
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
    def add_outbox_event(self, session, event) -> None:  # type: ignore[no-untyped-def]
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
