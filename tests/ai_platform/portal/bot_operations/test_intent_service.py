from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from ai_platform.portal.bot_operations.intent_service import (
    LifecycleCommandIntentService,
    LifecycleIntentContext,
    LifecycleIntentRequest,
    SqlAlchemyIdempotentCommandLookup,
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
GENERATION_ID = "generation-3"


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
        capabilities=(BotManagementCapability.BOT_START,),
        correlation=CorrelationContext(
            request_id=UUID(
                "55555555-5555-4555-8555-555555555555"
                if retry
                else "22222222-2222-4222-8222-222222222222"
            ),
            correlation_id=UUID(
                "66666666-6666-4666-8666-666666666666"
                if retry
                else "33333333-3333-4333-8333-333333333333"
            ),
        ),
    )


def _runtime() -> AuthoritativeBotRuntimeState:
    return AuthoritativeBotRuntimeState(
        tenant_id="tenant-a",
        bot_id="bot-a",
        config_revision=3,
        runtime_generation_id=GENERATION_ID,
        runtime_id="runtime-a",
        runtime_revision=7,
        environment=Environment.TEST,
        freshness=RuntimeReadFreshness.CURRENT,
        kill_switch_active=False,
        observed_at=NOW,
    )


def _request(
    *,
    expected_config_revision: int = 3,
    expected_runtime_generation_id: str = GENERATION_ID,
    action: LifecycleAction = LifecycleAction.START,
) -> LifecycleIntentRequest:
    return LifecycleIntentRequest(
        bot_id="bot-a",
        action=action,
        expected_config_revision=expected_config_revision,
        expected_runtime_generation_id=expected_runtime_generation_id,
        idempotency_key="lifecycle-bot-a-r3",
    )


def _read_context() -> BotCommandContext:
    return BotCommandContext(
        tenant_id="tenant-a",
        actor=_context().actor,
        environment=Environment.TEST,
        capabilities=(BotManagementCapability.COMMAND_READ,),
    )


def test_unavailable_runtime_fails_closed_without_persisting_a_command() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    service = LifecycleCommandIntentService(
        commands,
        UnavailableBotRuntimeStateProvider(),
        idempotency_lookup=SqlAlchemyIdempotentCommandLookup(session_factory),
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
        idempotency_lookup=SqlAlchemyIdempotentCommandLookup(session_factory),
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )

    result = service.submit(_context(), _request())

    assert result.status == CommandOutcomeStatus.ACCEPTED
    assert result.command_id == str(COMMAND_ID)
    assert result.command_persisted is True
    assert result.execution_submission_performed is False
    history = commands.list_history(_read_context(), str(COMMAND_ID))
    assert len(history) == 1
    assert history[0].command.target.runtime_generation_id == GENERATION_ID
    assert history[0].outcome.status == CommandOutcomeStatus.ACCEPTED
    assert history[0].outcome.execution_attempt_ref is None
    assert history[0].outcome.reconciliation_ref is None


def test_stale_configuration_is_persisted_as_rejected_evidence() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    service = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        idempotency_lookup=SqlAlchemyIdempotentCommandLookup(session_factory),
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )

    result = service.submit(_context(), _request(expected_config_revision=2))

    assert result.status == CommandOutcomeStatus.REJECTED
    assert result.reason_codes == (CommandReasonCode.STALE_REVISION,)
    assert result.command_persisted is True
    assert result.execution_submission_performed is False


def test_stale_generation_is_persisted_as_rejected_evidence() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    service = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        idempotency_lookup=SqlAlchemyIdempotentCommandLookup(session_factory),
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )

    result = service.submit(
        _context(),
        _request(expected_runtime_generation_id="generation-stale"),
    )

    assert result.status == CommandOutcomeStatus.REJECTED
    assert result.reason_codes == (CommandReasonCode.STALE_GENERATION,)
    assert result.command_persisted is True
    history = commands.list_history(_read_context(), str(COMMAND_ID))
    assert history[-1].outcome.observed_runtime_generation_id == GENERATION_ID
    assert history[-1].outcome.execution_attempt_ref is None


def test_transport_retry_returns_existing_command_without_duplicate_history() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    lookup = SqlAlchemyIdempotentCommandLookup(session_factory)
    first = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        idempotency_lookup=lookup,
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )
    retry = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        idempotency_lookup=lookup,
        clock=lambda: NOW + timedelta(seconds=5),
        id_factory=lambda: RETRY_COMMAND_ID,
    )

    accepted = first.submit(_context(), _request())
    replay = retry.submit(_context(retry=True), _request())

    assert accepted.command_id == str(COMMAND_ID)
    assert replay.command_id == str(COMMAND_ID)
    assert replay.status == CommandOutcomeStatus.ACCEPTED
    assert replay.command_persisted is True
    assert len(commands.list_history(_read_context(), str(COMMAND_ID))) == 1


def test_same_idempotency_key_with_different_action_records_conflict_only() -> None:
    session_factory = _session_factory()
    commands = BotCommandService(session_factory, clock=lambda: NOW)
    lookup = SqlAlchemyIdempotentCommandLookup(session_factory)
    first = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        idempotency_lookup=lookup,
        clock=lambda: NOW,
        id_factory=lambda: COMMAND_ID,
    )
    conflicting = LifecycleCommandIntentService(
        commands,
        FixedRuntimeProvider(_runtime()),
        idempotency_lookup=lookup,
        clock=lambda: NOW + timedelta(seconds=5),
        id_factory=lambda: RETRY_COMMAND_ID,
    )

    first.submit(_context(), _request())
    result = conflicting.submit(
        _context(retry=True),
        _request(action=LifecycleAction.PAUSE_NEW_ENTRIES),
    )

    assert result.status == CommandOutcomeStatus.REJECTED
    assert result.reason_codes == (CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY,)
    assert result.command_id is None
    assert result.command_persisted is False
    assert result.execution_submission_performed is False
    conflicts = commands.list_idempotency_conflicts(_read_context())
    assert len(conflicts) == 1
