from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from ai_platform.portal.bot_operations.intent_service import (
    LifecycleCommandIntentService,
    LifecycleIntentContext,
    LifecycleIntentRequest,
    UnavailableBotRuntimeStateProvider,
)
from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    CommandOutcomeStatus,
    CommandReasonCode,
    LifecycleAction,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.execution.private_read import RuntimeReadFreshness


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
COMMAND_ID = UUID("11111111-1111-4111-8111-111111111111")
RETRY_COMMAND_ID = UUID("44444444-4444-4444-8444-444444444444")


class FixedRuntimeProvider:
    def __init__(self, state: AuthoritativeBotRuntimeState) -> None:
        self._state = state

    def resolve(
        self,
        *,
        tenant_id: str,
        bot_id: str,
    ) -> AuthoritativeBotRuntimeState | None:
        if tenant_id != self._state.tenant_id or bot_id != self._state.bot_id:
            return None
        return self._state


def _session_factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(*, retry: bool = False) -> LifecycleIntentContext:
    return LifecycleIntentContext(
        tenant_id="tenant-a",
        actor=Actor(
            actor_id="actor-a",
            tenant_id="tenant-a",
            actor_type=ActorType.USER,
        ),
        capabilities=tuple(
            sorted(
                (
                    BotManagementCapability.BOT_PAUSE,
                    BotManagementCapability.BOT_START,
                ),
                key=lambda item: item.value,
            )
        ),
        correlation=CorrelationContext(
            request_id=(
                UUID("55555555-5555-4555-8555-555555555555")
                if retry
                else UUID("22222222-2222-4222-8222-222222222222")
            ),
            correlation_id=(
                UUID("66666666-6666-4666-8666-666666666666")
                if retry
                else UUID("33333333-3333-4333-8333-333333333333")
            ),
        ),
    )


def _runtime() -> AuthoritativeBotRuntimeState:
    return AuthoritativeBotRuntimeState(
        tenant_id="tenant-a",
        bot_id="bot-a",
        config_revision=3,
        runtime_id="runtime-a",
        runtime_revision=7,
        environment=Environment.TEST,
        freshness=RuntimeReadFreshness.CURRENT,
        kill_switch_active=False,
        observed_at=NOW,
    )


def _request(
    expected_config_revision: int = 3,
    *,
    action: LifecycleAction = LifecycleAction.START,
) -> LifecycleIntentRequest:
    return LifecycleIntentRequest(
        bot_id="bot-a",
        action=action,
        expected_config_revision=expected_config_revision,
        idempotency_key="lifecycle-start-bot-a-r3",
    )


def test_unavailable_runtime_fails_closed_without_persisting_a_command() -> None:
    commands = BotCommandService(_session_factory(), clock=lambda: NOW)
    service = LifecycleCommandIntentService(
        commands,
        UnavailableBotRuntimeStateProvider(),
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )

    result = service.submit(_context(), _request())

    assert result.status == CommandOutcomeStatus.BLOCKED
    assert result.reason_codes == (CommandReasonCode.RUNTIME_UNAVAILABLE,)
    assert result.command_id is None
    assert result.command_persisted is False
    assert result.execution_submission_performed is False


def test_current_runtime_persists_accepted_intent_without_execution_submission() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    service = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )

    result = service.submit(_context(), _request())

    assert result.status == CommandOutcomeStatus.ACCEPTED
    assert result.command_id == str(COMMAND_ID)
    assert result.command_persisted is True
    assert result.execution_submission_performed is False
    history = commands.list_history(
        BotCommandContext(
            tenant_id="tenant-a",
            actor=_context().actor,
            environment=Environment.TEST,
            capabilities=(BotManagementCapability.COMMAND_READ,),
        ),
        str(COMMAND_ID),
    )
    assert len(history) == 1
    assert history[0].outcome.status == CommandOutcomeStatus.ACCEPTED
    assert history[0].outcome.execution_attempt_ref is None
    assert history[0].outcome.reconciliation_ref is None


def test_stale_configuration_is_persisted_as_rejected_evidence() -> None:
    commands = BotCommandService(_session_factory(), clock=lambda: NOW)
    service = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )

    result = service.submit(_context(), _request(expected_config_revision=2))

    assert result.status == CommandOutcomeStatus.REJECTED
    assert result.reason_codes == (CommandReasonCode.STALE_REVISION,)
    assert result.command_persisted is True
    assert result.execution_submission_performed is False


def test_transport_variant_retry_returns_existing_command_without_duplicate_history() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    ids = iter((COMMAND_ID, RETRY_COMMAND_ID))
    times = iter((NOW, NOW + timedelta(seconds=5)))
    service = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        clock=lambda: next(times),
        id_factory=lambda: next(ids),
    )

    first = service.submit(_context(), _request())
    retry = service.submit(_context(retry=True), _request())

    assert first.status == CommandOutcomeStatus.ACCEPTED
    assert retry.status == CommandOutcomeStatus.ACCEPTED
    assert retry.command_id == first.command_id == str(COMMAND_ID)
    assert retry.command_persisted is True
    history = commands.list_history(
        BotCommandContext(
            tenant_id="tenant-a",
            actor=_context().actor,
            environment=Environment.TEST,
            capabilities=(BotManagementCapability.COMMAND_READ,),
        ),
        str(COMMAND_ID),
    )
    assert len(history) == 1


def test_same_idempotency_key_with_different_business_action_is_rejected() -> None:
    commands = BotCommandService(_session_factory(), clock=lambda: NOW)
    ids = iter((COMMAND_ID, RETRY_COMMAND_ID))
    service = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        clock=lambda: NOW,
        id_factory=lambda: next(ids),
    )

    first = service.submit(_context(), _request())
    conflict = service.submit(
        _context(retry=True),
        _request(action=LifecycleAction.PAUSE_NEW_ENTRIES),
    )

    assert first.status == CommandOutcomeStatus.ACCEPTED
    assert conflict.status == CommandOutcomeStatus.REJECTED
    assert conflict.reason_codes == (CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY,)
    assert conflict.command_id is None
    assert conflict.command_persisted is False
    assert conflict.execution_submission_performed is False
