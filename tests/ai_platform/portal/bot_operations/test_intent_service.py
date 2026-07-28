from __future__ import annotations

from datetime import UTC, datetime
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


def _context() -> LifecycleIntentContext:
    return LifecycleIntentContext(
        tenant_id="tenant-a",
        actor=Actor(
            actor_id="actor-a",
            tenant_id="tenant-a",
            actor_type=ActorType.USER,
        ),
        capabilities=(BotManagementCapability.BOT_START,),
        correlation=CorrelationContext(
            request_id=UUID("22222222-2222-4222-8222-222222222222"),
            correlation_id=UUID("33333333-3333-4333-8333-333333333333"),
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


def _request(expected_config_revision: int = 3) -> LifecycleIntentRequest:
    return LifecycleIntentRequest(
        bot_id="bot-a",
        action=LifecycleAction.START,
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
