from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.bot_operations.service import (
    BotCommandService,
    BotCommandTransitionError,
)
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandConfirmationRequirement,
    CommandOutcomeStatus,
    CommandReasonCode,
    CommandTarget,
    LifecycleAction,
    OrderAction,
    OrderCommand,
    PositionAction,
    PositionCommand,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.control_plane.database import (
    Base,
    SessionFactory,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.execution.private_read import RuntimeReadFreshness


NOW = datetime(2026, 7, 27, 13, 0, tzinfo=UTC)
GENERATION_ID = "generation-3"


def _capabilities() -> tuple[BotManagementCapability, ...]:
    capabilities = (
        BotManagementCapability.BOT_START,
        BotManagementCapability.COMMAND_READ,
        BotManagementCapability.ORDER_CANCEL,
        BotManagementCapability.ORDER_REPLACE,
        BotManagementCapability.POSITION_CLOSE,
    )
    return tuple(sorted(capabilities, key=lambda capability: capability.value))


def _context() -> BotCommandContext:
    return BotCommandContext(
        tenant_id="tenant-a",
        actor=Actor(
            actor_id="actor-a",
            tenant_id="tenant-a",
            actor_type=ActorType.USER,
        ),
        environment=Environment.STAGING,
        capabilities=_capabilities(),
    )


def _target() -> CommandTarget:
    return CommandTarget(
        tenant_id="tenant-a",
        bot_id="bot-1",
        config_revision=3,
        runtime_generation_id=GENERATION_ID,
        runtime_id="runtime-1",
        runtime_revision=7,
    )


def _base_fields(
    context: BotCommandContext,
    *,
    command_id: str,
    idempotency_key: str,
    capability: BotManagementCapability,
) -> dict[str, Any]:
    return {
        "command_id": command_id,
        "tenant_id": context.tenant_id,
        "actor": context.actor,
        "environment": context.environment,
        "correlation": CorrelationContext(
            request_id=uuid4(),
            correlation_id=uuid4(),
        ),
        "idempotency_key": idempotency_key,
        "target": _target(),
        "capability": capability,
        "confirmation": CommandConfirmationRequirement(required=False),
        "submitted_at": NOW,
    }


def _lifecycle(
    context: BotCommandContext,
    *,
    command_id: str = "lifecycle-1",
    idempotency_key: str = "key-1",
) -> BotLifecycleCommand:
    return BotLifecycleCommand(
        **_base_fields(
            context,
            command_id=command_id,
            idempotency_key=idempotency_key,
            capability=BotManagementCapability.BOT_START,
        ),
        action=LifecycleAction.START,
    )


def _position(context: BotCommandContext) -> PositionCommand:
    return PositionCommand(
        **_base_fields(
            context,
            command_id="position-1",
            idempotency_key="position-key",
            capability=BotManagementCapability.POSITION_CLOSE,
        ),
        action=PositionAction.CLOSE_POSITION,
        position_id="position-runtime-1",
        position_revision=5,
    )


def _order(context: BotCommandContext) -> OrderCommand:
    return OrderCommand(
        **_base_fields(
            context,
            command_id="order-1",
            idempotency_key="order-key",
            capability=BotManagementCapability.ORDER_REPLACE,
        ),
        action=OrderAction.REPLACE_ORDER,
        order_id="order-runtime-1",
        order_revision=9,
        replacement_price=Decimal("101.25"),
    )


def _runtime() -> AuthoritativeBotRuntimeState:
    return AuthoritativeBotRuntimeState(
        tenant_id="tenant-a",
        bot_id="bot-1",
        config_revision=3,
        runtime_generation_id=GENERATION_ID,
        runtime_id="runtime-1",
        runtime_revision=7,
        environment=Environment.STAGING,
        freshness=RuntimeReadFreshness.CURRENT,
        kill_switch_active=False,
        observed_at=NOW,
    )


def _service_and_factory() -> tuple[BotCommandService, SessionFactory]:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    service = BotCommandService(session_factory, clock=lambda: NOW)
    return service, session_factory


def test_exact_idempotent_replay_does_not_append_history() -> None:
    service, _ = _service_and_factory()
    context = _context()
    command = _lifecycle(context)

    first = service.submit_lifecycle(context, command, _runtime())
    second = service.submit_lifecycle(context, command, _runtime())

    assert first == second
    assert first.status == CommandOutcomeStatus.ACCEPTED
    assert len(service.list_history(context, command.command_id)) == 1
    assert service.list_idempotency_conflicts(context) == ()


def test_conflicting_idempotency_key_is_rejected_and_recorded() -> None:
    service, _ = _service_and_factory()
    context = _context()
    original = _lifecycle(context)
    conflicting = _lifecycle(
        context,
        command_id="lifecycle-2",
        idempotency_key=original.idempotency_key,
    )

    service.submit_lifecycle(context, original, _runtime())
    outcome = service.submit_lifecycle(context, conflicting, _runtime())

    assert outcome.status == CommandOutcomeStatus.REJECTED
    assert outcome.reason_codes == (CommandReasonCode.DUPLICATE_IDEMPOTENCY_KEY,)
    conflicts = service.list_idempotency_conflicts(context, original.idempotency_key)
    assert len(conflicts) == 1
    assert conflicts[0].existing_command_id == original.command_id
    assert conflicts[0].attempted_command.command_id == conflicting.command_id


def test_all_command_families_persist_without_execution_evidence() -> None:
    service, _ = _service_and_factory()
    context = _context()
    commands = (_lifecycle(context), _position(context), _order(context))

    outcomes = (
        service.submit_lifecycle(context, commands[0], _runtime()),
        service.submit_position(context, commands[1], _runtime()),
        service.submit_order(context, commands[2], _runtime()),
    )

    assert all(outcome.status == CommandOutcomeStatus.ACCEPTED for outcome in outcomes)
    assert all(outcome.execution_attempt_ref is None for outcome in outcomes)
    assert all(outcome.reconciliation_ref is None for outcome in outcomes)
    for command in commands:
        history = service.list_history(context, command.command_id)
        assert history[0].command == command
        assert history[0].command.target.runtime_generation_id == GENERATION_ID


def test_pending_reconciliation_appends_history_without_success() -> None:
    service, session_factory = _service_and_factory()
    context = _context()
    command = _lifecycle(context)

    accepted = service.submit_lifecycle(context, command, _runtime())
    pending = service.mark_pending_reconciliation(
        context,
        command.command_id,
        "execution-attempt-1",
    )

    restarted = BotCommandService(session_factory, clock=lambda: NOW)
    history = restarted.list_history(context, command.command_id)
    assert [entry.sequence for entry in history] == [1, 2]
    assert [entry.outcome.status for entry in history] == [
        CommandOutcomeStatus.ACCEPTED,
        CommandOutcomeStatus.PENDING_RECONCILIATION,
    ]
    assert history[0].outcome == accepted
    assert history[0].outcome.execution_attempt_ref is None
    assert history[1].outcome == pending
    assert history[1].outcome.execution_attempt_ref == "execution-attempt-1"
    assert history[1].outcome.reconciliation_ref is None

    replayed = restarted.mark_pending_reconciliation(
        context,
        command.command_id,
        "execution-attempt-1",
    )
    assert replayed == pending
    assert len(restarted.list_history(context, command.command_id)) == 2

    with pytest.raises(BotCommandTransitionError):
        restarted.mark_pending_reconciliation(
            context,
            command.command_id,
            "execution-attempt-2",
        )
    assert len(restarted.list_history(context, command.command_id)) == 2
