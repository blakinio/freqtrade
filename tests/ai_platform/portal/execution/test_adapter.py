from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.bots import (
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import (
    ExecutionAdapter,
    RuntimeHealthState,
)
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent
from ai_platform.portal.execution.adapter import FreqtradeExecutionAdapter
from ai_platform.portal.execution.errors import (
    RuntimeDriverError,
    RuntimeNotProvisionedError,
    RuntimeRevisionConflictError,
    UnsupportedExecutionModeError,
    UnsupportedExecutionOperationError,
)
from ai_platform.portal.execution.runtime import (
    DriverRuntimeState,
    ResolvedRuntimeArtifacts,
    RuntimeContainerSpec,
)
from ai_platform.portal.execution.workspace import RuntimeWorkspaceStore


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


class _Resolver:
    def __init__(self) -> None:
        self.artifacts = ResolvedRuntimeArtifacts(
            image="freqtradeorg/freqtrade:stable",
            strategy_name="PortalStrategy",
            base_config={"exchange": {"name": "binance"}},
        )

    def resolve(self, bot: BotInstance) -> ResolvedRuntimeArtifacts:
        del bot
        return self.artifacts


class _FakeDriver:
    def __init__(self) -> None:
        self.states: dict[str, DriverRuntimeState] = {}
        self.provision_specs: list[RuntimeContainerSpec] = []
        self.failures: dict[str, str] = {}

    def fail_next(self, operation: str, reason_code: str) -> None:
        self.failures[operation] = reason_code

    def provision(self, spec: RuntimeContainerSpec) -> DriverRuntimeState:
        self._maybe_fail("provision")
        self.provision_specs.append(spec)
        return self.states.setdefault(spec.runtime_id, DriverRuntimeState.CREATED)

    def start(self, runtime_id: str) -> DriverRuntimeState:
        self._maybe_fail("start")
        if runtime_id not in self.states:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime is missing")
        self.states[runtime_id] = DriverRuntimeState.RUNNING
        return self.states[runtime_id]

    def pause(self, runtime_id: str) -> DriverRuntimeState:
        self._maybe_fail("pause")
        if runtime_id not in self.states:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime is missing")
        if self.states[runtime_id] is DriverRuntimeState.RUNNING:
            self.states[runtime_id] = DriverRuntimeState.PAUSED
        return self.states[runtime_id]

    def stop(self, runtime_id: str) -> DriverRuntimeState:
        self._maybe_fail("stop")
        if runtime_id not in self.states:
            raise RuntimeDriverError("RUNTIME_MISSING", "runtime is missing")
        if self.states[runtime_id] in {
            DriverRuntimeState.RUNNING,
            DriverRuntimeState.PAUSED,
        }:
            self.states[runtime_id] = DriverRuntimeState.STOPPED
        return self.states[runtime_id]

    def inspect(self, runtime_id: str) -> DriverRuntimeState:
        self._maybe_fail("inspect")
        return self.states.get(runtime_id, DriverRuntimeState.MISSING)

    def _maybe_fail(self, operation: str) -> None:
        reason_code = self.failures.pop(operation, None)
        if reason_code is not None:
            raise RuntimeDriverError(reason_code, reason_code)


def _bot(
    tenant_id: str = "tenant-a",
    bot_id: str = "bot-1",
    revision: int = 1,
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
) -> BotInstance:
    return BotInstance(
        bot_id=bot_id,
        tenant_id=tenant_id,
        name="Test bot",
        spec=BotSpec(
            tenant_id=tenant_id,
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency="USDT",
            runtime_version="runtime-v1",
            config_revision=revision,
            environment=Environment.TEST,
            execution_mode=execution_mode,
        ),
        desired_state=BotDesiredState.CREATED,
        observed_state=BotObservedState.CREATED,
    )


def _context() -> CorrelationContext:
    return CorrelationContext(
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _adapter(tmp_path):  # type: ignore[no-untyped-def]
    driver = _FakeDriver()
    resolver = _Resolver()
    store = RuntimeWorkspaceStore(tmp_path)
    adapter = FreqtradeExecutionAdapter(driver, resolver, store, clock=lambda: NOW)
    protocol_adapter: ExecutionAdapter = adapter
    return protocol_adapter, driver, resolver, store


def test_provisioning_is_deterministic_isolated_and_correlation_labeled(tmp_path) -> None:
    adapter, driver, _resolver, store = _adapter(tmp_path)
    context = _context()

    first = adapter.provision_bot(_bot(), context)
    second = adapter.provision_bot(_bot(), context)
    other_tenant = adapter.provision_bot(_bot(tenant_id="tenant-b"), context)

    assert first.runtime_id == second.runtime_id
    assert first.runtime_id != other_tenant.runtime_id
    assert first.observed_state is BotObservedState.CREATED
    assert driver.provision_specs[0].workspace == store.workspace_for(first.runtime_id)
    assert driver.provision_specs[0].labels["ai.portal.correlation_id"] == str(
        context.correlation_id
    )
    assert "tenant-a" not in driver.provision_specs[0].labels.values()
    assert "bot-1" not in driver.provision_specs[0].labels.values()

    config = json.loads(store.config_path_for(first.runtime_id).read_text(encoding="utf-8"))
    assert config["dry_run"] is True
    assert config["api_server"] == {"enabled": False}


def test_runtime_operations_are_tenant_scoped(tmp_path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    adapter.provision_bot(_bot(tenant_id="tenant-a", bot_id="shared"), _context())

    with pytest.raises(RuntimeNotProvisionedError):
        adapter.pause_bot("tenant-b", "shared", _context())


def test_simulated_mode_is_rejected_by_p3(tmp_path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)

    with pytest.raises(UnsupportedExecutionModeError, match="dry_run"):
        adapter.provision_bot(_bot(execution_mode=ExecutionMode.SIMULATED), _context())


def test_config_revision_change_requires_explicit_reprovision_boundary(tmp_path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    adapter.provision_bot(_bot(revision=1), _context())

    with pytest.raises(RuntimeRevisionConflictError, match="config revision"):
        adapter.provision_bot(_bot(revision=2), _context())


def test_artifact_change_cannot_mutate_existing_revision_config(tmp_path) -> None:
    adapter, _driver, resolver, store = _adapter(tmp_path)
    bot = _bot(revision=1)
    status = adapter.provision_bot(bot, _context())
    config_path = store.config_path_for(status.runtime_id)
    original = config_path.read_text(encoding="utf-8")
    resolver.artifacts = ResolvedRuntimeArtifacts(
        image="freqtradeorg/freqtrade:next",
        strategy_name="PortalStrategy",
        base_config={"exchange": {"name": "binance"}},
    )

    with pytest.raises(RuntimeRevisionConflictError, match="artifacts changed"):
        adapter.provision_bot(bot, _context())

    assert config_path.read_text(encoding="utf-8") == original


def test_lifecycle_operations_are_idempotent_and_truthful(tmp_path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    bot = _bot()
    adapter.provision_bot(bot, _context())

    assert adapter.start_bot(bot, _context()).observed_state is BotObservedState.RUNNING
    assert adapter.start_bot(bot, _context()).observed_state is BotObservedState.RUNNING
    assert adapter.pause_bot(bot.tenant_id, bot.bot_id, _context()).observed_state is BotObservedState.PAUSED
    assert adapter.pause_bot(bot.tenant_id, bot.bot_id, _context()).observed_state is BotObservedState.PAUSED
    assert adapter.stop_bot(bot.tenant_id, bot.bot_id, _context()).observed_state is BotObservedState.STOPPED
    assert adapter.stop_bot(bot.tenant_id, bot.bot_id, _context()).observed_state is BotObservedState.STOPPED


def test_driver_failure_returns_error_and_persists_unhealthy_reason(tmp_path) -> None:
    adapter, driver, _resolver, store = _adapter(tmp_path)
    bot = _bot()
    provisioned = adapter.provision_bot(bot, _context())
    driver.fail_next("start", "DOCKER_START_FAILED")

    failed = adapter.start_bot(bot, _context())
    health = adapter.get_health(bot.tenant_id, bot.bot_id, _context())
    record = store.read_record(provisioned.runtime_id)

    assert failed.observed_state is BotObservedState.ERROR
    assert health.health is RuntimeHealthState.UNHEALTHY
    assert health.reason_code == "DOCKER_START_FAILED"
    assert record is not None
    assert record.last_error_code == "DOCKER_START_FAILED"

    recovered = adapter.get_runtime_status(bot.tenant_id, bot.bot_id, _context())
    assert recovered.observed_state is BotObservedState.CREATED
    assert adapter.get_health(bot.tenant_id, bot.bot_id, _context()).reason_code == "RUNTIME_NOT_READY"


def test_trade_and_portfolio_methods_fail_closed_until_private_transport_exists(tmp_path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    context = _context()
    intent = cast(ApprovedExecutionIntent, object())

    with pytest.raises(UnsupportedExecutionOperationError) as submit_error:
        adapter.submit_approved_intent(intent, context)
    with pytest.raises(UnsupportedExecutionOperationError):
        adapter.get_open_positions("tenant-a", "bot-1", context)
    with pytest.raises(UnsupportedExecutionOperationError):
        adapter.get_orders("tenant-a", "bot-1", context)
    with pytest.raises(UnsupportedExecutionOperationError):
        adapter.get_trades("tenant-a", "bot-1", context)

    assert submit_error.value.reason_code == "ORDER_SUBMISSION_NOT_IMPLEMENTED"
