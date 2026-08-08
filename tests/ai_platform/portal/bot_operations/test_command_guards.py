from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandConfirmationRequirement,
    CommandOutcomeStatus,
    CommandReasonCode,
    CommandTarget,
    LifecycleAction,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.control_plane.database import (
    Base,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.execution.private_read import RuntimeReadFreshness


NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
GENERATION_ID = "generation-1"


def _capabilities(
    *values: BotManagementCapability,
) -> tuple[BotManagementCapability, ...]:
    return tuple(sorted(values, key=lambda capability: capability.value))


def _context(
    tenant_id: str = "tenant-a",
    *,
    actor_id: str = "actor-a",
    capabilities: tuple[BotManagementCapability, ...] | None = None,
) -> BotCommandContext:
    selected_capabilities = capabilities or _capabilities(
        BotManagementCapability.BOT_START,
        BotManagementCapability.BOT_STOP,
        BotManagementCapability.COMMAND_READ,
    )
    return BotCommandContext(
        tenant_id=tenant_id,
        actor=Actor(
            actor_id=actor_id,
            tenant_id=tenant_id,
            actor_type=ActorType.USER,
        ),
        environment=Environment.STAGING,
        capabilities=selected_capabilities,
    )


def _command(
    context: BotCommandContext,
    *,
    command_id: str = "command-1",
    idempotency_key: str = "idempotency-1",
    tenant_id: str | None = None,
    actor: Actor | None = None,
    action: LifecycleAction = LifecycleAction.START,
    capability: BotManagementCapability = BotManagementCapability.BOT_START,
    config_revision: int = 1,
    runtime_generation_id: str = GENERATION_ID,
    runtime_id: str = "runtime-1",
    runtime_revision: int = 1,
) -> BotLifecycleCommand:
    command_tenant = tenant_id or context.tenant_id
    command_actor = actor or Actor(
        actor_id=context.actor.actor_id,
        tenant_id=command_tenant,
        actor_type=context.actor.actor_type,
    )
    return BotLifecycleCommand(
        command_id=command_id,
        tenant_id=command_tenant,
        actor=command_actor,
        environment=context.environment,
        correlation=CorrelationContext(
            request_id=uuid4(),
            correlation_id=uuid4(),
        ),
        idempotency_key=idempotency_key,
        target=CommandTarget(
            tenant_id=command_tenant,
            bot_id="bot-1",
            config_revision=config_revision,
            runtime_generation_id=runtime_generation_id,
            runtime_id=runtime_id,
            runtime_revision=runtime_revision,
        ),
        capability=capability,
        confirmation=CommandConfirmationRequirement(required=False),
        submitted_at=NOW,
        action=action,
    )


def _runtime(
    *,
    tenant_id: str = "tenant-a",
    config_revision: int = 1,
    runtime_generation_id: str = GENERATION_ID,
    runtime_id: str = "runtime-1",
    runtime_revision: int = 1,
    freshness: RuntimeReadFreshness = RuntimeReadFreshness.CURRENT,
    kill_switch_active: bool = False,
) -> AuthoritativeBotRuntimeState:
    return AuthoritativeBotRuntimeState(
        tenant_id=tenant_id,
        bot_id="bot-1",
        config_revision=config_revision,
        runtime_generation_id=runtime_generation_id,
        runtime_id=runtime_id,
        runtime_revision=runtime_revision,
        environment=Environment.STAGING,
        freshness=freshness,
        kill_switch_active=kill_switch_active,
        observed_at=NOW,
    )


@pytest.fixture
def service() -> BotCommandService:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return BotCommandService(build_session_factory(engine), clock=lambda: NOW)


def test_cross_tenant_command_is_rejected_and_scoped_to_request_tenant(
    service: BotCommandService,
) -> None:
    context = _context()
    foreign_actor = Actor(
        actor_id="actor-b",
        tenant_id="tenant-b",
        actor_type=ActorType.USER,
    )
    command = _command(
        context,
        tenant_id="tenant-b",
        actor=foreign_actor,
    )

    outcome = service.submit_lifecycle(
        context,
        command,
        _runtime(tenant_id="tenant-b"),
    )

    assert outcome.status == CommandOutcomeStatus.REJECTED
    assert outcome.reason_codes == (CommandReasonCode.TENANT_MISMATCH,)
    history = service.list_history(context, command.command_id)
    assert len(history) == 1
    assert history[0].audit.scope_tenant_id == "tenant-a"
    assert history[0].audit.attempted_tenant_id == "tenant-b"


def test_missing_capability_is_rejected(service: BotCommandService) -> None:
    capabilities = _capabilities(BotManagementCapability.COMMAND_READ)
    context = _context(capabilities=capabilities)
    command = _command(context)

    outcome = service.submit_lifecycle(context, command, _runtime())

    assert outcome.status == CommandOutcomeStatus.REJECTED
    assert outcome.reason_codes == (CommandReasonCode.CAPABILITY_MISSING,)


def test_revision_mismatch_is_rejected_with_observed_revision(
    service: BotCommandService,
) -> None:
    context = _context()
    command = _command(context, config_revision=1)

    outcome = service.submit_lifecycle(
        context,
        command,
        _runtime(config_revision=2),
    )

    assert outcome.status == CommandOutcomeStatus.REJECTED
    assert outcome.reason_codes == (CommandReasonCode.STALE_REVISION,)
    assert outcome.observed_config_revision == 2


def test_generation_mismatch_is_rejected_with_observed_generation(
    service: BotCommandService,
) -> None:
    context = _context()
    command = _command(context, runtime_generation_id="generation-old")

    outcome = service.submit_lifecycle(context, command, _runtime())

    assert outcome.status == CommandOutcomeStatus.REJECTED
    assert outcome.reason_codes == (CommandReasonCode.STALE_GENERATION,)
    assert outcome.observed_runtime_generation_id == GENERATION_ID


def test_stale_runtime_blocks_command(service: BotCommandService) -> None:
    context = _context()
    command = _command(context)

    outcome = service.submit_lifecycle(
        context,
        command,
        _runtime(freshness=RuntimeReadFreshness.STALE),
    )

    assert outcome.status == CommandOutcomeStatus.BLOCKED
    assert outcome.reason_codes == (CommandReasonCode.RUNTIME_UNAVAILABLE,)


def test_kill_switch_blocks_start_but_allows_stop(service: BotCommandService) -> None:
    context = _context()
    start = _command(
        context,
        command_id="start-command",
        idempotency_key="start-key",
    )
    stop = _command(
        context,
        command_id="stop-command",
        idempotency_key="stop-key",
        action=LifecycleAction.STOP_KEEP_POSITIONS,
        capability=BotManagementCapability.BOT_STOP,
    )
    runtime = _runtime(kill_switch_active=True)

    start_outcome = service.submit_lifecycle(context, start, runtime)
    stop_outcome = service.submit_lifecycle(context, stop, runtime)

    assert start_outcome.status == CommandOutcomeStatus.BLOCKED
    assert start_outcome.reason_codes == (CommandReasonCode.KILL_SWITCH_ACTIVE,)
    assert stop_outcome.status == CommandOutcomeStatus.ACCEPTED
    assert stop_outcome.reason_codes == ()
    assert stop_outcome.execution_attempt_ref is None
    assert stop_outcome.reconciliation_ref is None
