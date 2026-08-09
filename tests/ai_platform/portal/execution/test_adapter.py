from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
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
from ai_platform.portal.contracts.execution import ExecutionAdapter, RuntimeHealthState
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


def _safe_config() -> dict[str, object]:
    return {
        "exchange": {"name": "binance", "pair_whitelist": ["BTC/USDT"]},
        "dry_run": True,
        "dry_run_wallet": 1000.0,
        "stake_currency": "USDT",
        "timeframe": "5m",
        "db_url": "sqlite:////runtime/state/tradesv3.dryrun.sqlite",
        "api_server": {"enabled": False},
        "telegram": {"enabled": False},
    }


def _config_digest(config: dict[str, object]) -> str:
    canonical = json.dumps(
        config,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _material(
    *,
    tenant_id: str = "tenant-a",
    bot_id: str = "bot-1",
    generation_id: str = "generation-1",
    generation_ordinal: int = 1,
    revision: int = 1,
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
    image_digest: str = "2" * 64,
    config: dict[str, object] | None = None,
) -> ResolvedRuntimeArtifacts:
    runtime_config = config or _safe_config()
    return ResolvedRuntimeArtifacts(
        tenant_id=tenant_id,
        bot_id=bot_id,
        generation_id=generation_id,
        generation_ordinal=generation_ordinal,
        config_revision_id=f"revision-{revision}",
        config_revision=revision,
        config_revision_digest=str(revision % 10) * 64,
        generation_spec_digest=hashlib.sha256(f"spec:{generation_id}".encode()).hexdigest(),
        normalized_runtime_config_digest=_config_digest(runtime_config),
        runtime_image_digest=image_digest,
        strategy_artifact_digest="3" * 64,
        model_artifact_digest="4" * 64,
        execution_mode=execution_mode,
        image=f"freqtradeorg/freqtrade@sha256:{image_digest}",
        strategy_name="PortalStrategy",
        runtime_config=runtime_config,
    )


class _Resolver:
    def __init__(self) -> None:
        self.materials: dict[tuple[str, str, str], ResolvedRuntimeArtifacts] = {}

    def register(self, material: ResolvedRuntimeArtifacts) -> None:
        self.materials[(material.tenant_id, material.bot_id, material.generation_id)] = material

    def resolve(
        self,
        tenant_id: str,
        bot_id: str,
        generation_id: str,
    ) -> ResolvedRuntimeArtifacts:
        return self.materials[(tenant_id, bot_id, generation_id)]


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
    generation_id: str | None = "generation-1",
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
        desired_runtime_generation_id=generation_id,
    )


def _context() -> CorrelationContext:
    return CorrelationContext(
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _adapter(
    tmp_path: Path,
) -> tuple[ExecutionAdapter, _FakeDriver, _Resolver, RuntimeWorkspaceStore]:
    driver = _FakeDriver()
    resolver = _Resolver()
    resolver.register(_material())
    store = RuntimeWorkspaceStore(tmp_path)
    adapter = FreqtradeExecutionAdapter(driver, resolver, store, clock=lambda: NOW)
    protocol_adapter: ExecutionAdapter = adapter
    return protocol_adapter, driver, resolver, store


def test_provisioning_is_generation_scoped_isolated_and_correlation_labeled(
    tmp_path: Path,
) -> None:
    adapter, driver, resolver, store = _adapter(tmp_path)
    context = _context()

    first = adapter.provision_bot(_bot(), context)
    second = adapter.provision_bot(_bot(), context)
    resolver.register(_material(tenant_id="tenant-b"))
    other_tenant = adapter.provision_bot(_bot(tenant_id="tenant-b"), context)

    assert first.runtime_id == second.runtime_id
    assert first.runtime_id != other_tenant.runtime_id
    assert first.observed_state is BotObservedState.CREATED
    spec = driver.provision_specs[0]
    assert spec.config_path == store.config_path_for(first.runtime_id)
    assert spec.state_path == store.state_path_for(first.runtime_id)
    assert spec.config_path.parent != spec.state_path
    assert store.record_path_for(first.runtime_id).parent != spec.config_path.parent
    assert store.record_path_for(first.runtime_id).parent != spec.state_path
    assert spec.labels["ai.portal.correlation_id"] == str(context.correlation_id)
    assert "tenant-a" not in spec.labels.values()
    assert "bot-1" not in spec.labels.values()
    assert "generation-1" not in spec.labels.values()

    config_path = store.config_path_for(first.runtime_id)
    assert json.loads(config_path.read_text(encoding="utf-8")) == _safe_config()
    assert config_path.stat().st_mode & 0o222 == 0

    current = store.read_current_record("tenant-a", "bot-1")
    assert current is not None
    assert current.generation_id == "generation-1"
    assert current.generation_ordinal == 1
    assert current.runtime_id == first.runtime_id
    assert current.generation_spec_digest == _material().generation_spec_digest


def test_provisioning_requires_control_plane_runtime_generation(tmp_path: Path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)

    with pytest.raises(RuntimeNotProvisionedError, match="desired RuntimeGeneration"):
        adapter.provision_bot(_bot(generation_id=None), _context())


def test_resolver_cross_tenant_or_generation_identity_is_rejected(tmp_path: Path) -> None:
    adapter, _driver, resolver, _store = _adapter(tmp_path)
    resolver.materials[("tenant-a", "bot-1", "generation-1")] = _material(tenant_id="tenant-b")

    with pytest.raises(
        RuntimeRevisionConflictError,
        match="requested RuntimeGeneration identity",
    ):
        adapter.provision_bot(_bot(), _context())


def test_runtime_operations_are_tenant_scoped(tmp_path: Path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    adapter.provision_bot(_bot(), _context())

    with pytest.raises(RuntimeNotProvisionedError):
        adapter.pause_bot("tenant-b", "bot-1", _context())


def test_non_dry_run_generation_is_rejected_even_if_projection_is_dry_run(
    tmp_path: Path,
) -> None:
    adapter, _driver, resolver, _store = _adapter(tmp_path)
    resolver.register(_material(execution_mode=ExecutionMode.SIMULATED))

    with pytest.raises(UnsupportedExecutionModeError, match="dry_run"):
        adapter.provision_bot(_bot(), _context())


def test_latest_authored_projection_cannot_redefine_existing_generation(
    tmp_path: Path,
) -> None:
    adapter, _driver, _resolver, store = _adapter(tmp_path)
    first = adapter.provision_bot(_bot(revision=1), _context())

    second = adapter.provision_bot(_bot(revision=99), _context())

    assert second.runtime_id == first.runtime_id
    record = store.read_current_record("tenant-a", "bot-1")
    assert record is not None
    assert record.config_revision == 1
    assert record.config_revision_id == "revision-1"


def test_config_digest_mismatch_with_generation_fails_closed(tmp_path: Path) -> None:
    adapter, _driver, resolver, _store = _adapter(tmp_path)
    material = _material()
    resolver.register(
        ResolvedRuntimeArtifacts(
            **{
                **material.__dict__,
                "normalized_runtime_config_digest": "f" * 64,
            }
        )
    )

    with pytest.raises(RuntimeRevisionConflictError, match="config digest"):
        adapter.provision_bot(_bot(), _context())


def test_image_must_be_pinned_to_generation_digest(tmp_path: Path) -> None:
    adapter, _driver, resolver, _store = _adapter(tmp_path)
    material = _material()
    resolver.register(
        ResolvedRuntimeArtifacts(
            **{
                **material.__dict__,
                "image": "freqtradeorg/freqtrade:stable",
            }
        )
    )

    with pytest.raises(RuntimeRevisionConflictError, match="image digest"):
        adapter.provision_bot(_bot(), _context())


def test_replacement_requires_old_running_generation_to_stop_and_preserves_state(
    tmp_path: Path,
) -> None:
    adapter, _driver, resolver, store = _adapter(tmp_path)
    first_bot = _bot()
    first = adapter.provision_bot(first_bot, _context())
    adapter.start_bot(first_bot, _context())
    first_state = store.state_path_for(first.runtime_id)
    (first_state / "tradesv3.dryrun.sqlite").write_text(
        "generation-one",
        encoding="utf-8",
    )

    replacement = _bot(revision=2, generation_id="generation-2")
    resolver.register(
        _material(
            generation_id="generation-2",
            generation_ordinal=2,
            revision=2,
        )
    )
    with pytest.raises(RuntimeRevisionConflictError, match="must be stopped"):
        adapter.provision_bot(replacement, _context())

    adapter.stop_bot(first_bot.tenant_id, first_bot.bot_id, _context())
    second = adapter.provision_bot(replacement, _context())

    assert second.runtime_id != first.runtime_id
    assert (first_state / "tradesv3.dryrun.sqlite").read_text(encoding="utf-8") == (
        "generation-one"
    )
    assert store.state_path_for(second.runtime_id) != first_state
    assert store.state_path_for(second.runtime_id).is_dir()

    old_record = store.read_record(first.runtime_id)
    current = store.read_current_record(first_bot.tenant_id, first_bot.bot_id)
    assert old_record is not None
    assert old_record.generation_id == "generation-1"
    assert current is not None
    assert current.generation_id == "generation-2"
    assert current.generation_ordinal == 2
    assert current.runtime_id == second.runtime_id

    with pytest.raises(RuntimeRevisionConflictError, match="desired RuntimeGeneration"):
        adapter.start_bot(first_bot, _context())


def test_same_generation_recovery_reuses_durable_state(tmp_path: Path) -> None:
    adapter, _driver, _resolver, store = _adapter(tmp_path)
    bot = _bot()
    first = adapter.provision_bot(bot, _context())
    state_file = store.state_path_for(first.runtime_id) / "checkpoint.txt"
    state_file.write_text("persisted", encoding="utf-8")

    second = adapter.provision_bot(bot, _context())

    assert second.runtime_id == first.runtime_id
    assert state_file.read_text(encoding="utf-8") == "persisted"


def test_material_change_cannot_mutate_existing_generation(tmp_path: Path) -> None:
    adapter, _driver, resolver, store = _adapter(tmp_path)
    bot = _bot()
    status = adapter.provision_bot(bot, _context())
    config_path = store.config_path_for(status.runtime_id)
    original = config_path.read_text(encoding="utf-8")
    resolver.register(_material(image_digest="a" * 64))

    with pytest.raises(RuntimeRevisionConflictError, match="material changed"):
        adapter.provision_bot(bot, _context())

    assert config_path.read_text(encoding="utf-8") == original


def test_lower_generation_ordinal_is_rejected_before_provision_side_effect(
    tmp_path: Path,
) -> None:
    adapter, driver, resolver, store = _adapter(tmp_path)
    first_bot = _bot()
    adapter.provision_bot(first_bot, _context())
    adapter.stop_bot(first_bot.tenant_id, first_bot.bot_id, _context())

    resolver.register(
        _material(
            generation_id="generation-2",
            generation_ordinal=2,
            revision=2,
        )
    )
    second_bot = _bot(generation_id="generation-2", revision=2)
    second = adapter.provision_bot(second_bot, _context())
    adapter.stop_bot(second_bot.tenant_id, second_bot.bot_id, _context())
    provision_count = len(driver.provision_specs)

    resolver.register(
        _material(
            generation_id="generation-3",
            generation_ordinal=1,
            revision=3,
        )
    )
    with pytest.raises(RuntimeRevisionConflictError, match="ordinal"):
        adapter.provision_bot(_bot(generation_id="generation-3", revision=3), _context())

    assert len(driver.provision_specs) == provision_count
    rejected_runtime = store.runtime_id_for("tenant-a", "bot-1", "generation-3")
    assert store.read_record(rejected_runtime) is None
    assert not store.state_path_for(rejected_runtime).exists()
    current = store.read_current_record("tenant-a", "bot-1")
    assert current is not None
    assert current.runtime_id == second.runtime_id


def test_lifecycle_operations_are_idempotent_and_truthful(tmp_path: Path) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    bot = _bot()
    adapter.provision_bot(bot, _context())

    assert adapter.start_bot(bot, _context()).observed_state is BotObservedState.RUNNING
    assert adapter.start_bot(bot, _context()).observed_state is BotObservedState.RUNNING
    first_pause = adapter.pause_bot(bot.tenant_id, bot.bot_id, _context())
    second_pause = adapter.pause_bot(bot.tenant_id, bot.bot_id, _context())
    first_stop = adapter.stop_bot(bot.tenant_id, bot.bot_id, _context())
    second_stop = adapter.stop_bot(bot.tenant_id, bot.bot_id, _context())
    assert first_pause.observed_state is BotObservedState.PAUSED
    assert second_pause.observed_state is BotObservedState.PAUSED
    assert first_stop.observed_state is BotObservedState.STOPPED
    assert second_stop.observed_state is BotObservedState.STOPPED


def test_driver_failure_returns_error_and_persists_unhealthy_reason(
    tmp_path: Path,
) -> None:
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
    recovered_health = adapter.get_health(bot.tenant_id, bot.bot_id, _context())
    assert recovered.observed_state is BotObservedState.CREATED
    assert recovered_health.reason_code == "RUNTIME_NOT_READY"


def test_submission_and_unprovisioned_private_reads_fail_closed(
    tmp_path: Path,
) -> None:
    adapter, _driver, _resolver, _store = _adapter(tmp_path)
    context = _context()
    intent = cast(ApprovedExecutionIntent, object())

    with pytest.raises(UnsupportedExecutionOperationError) as submit_error:
        adapter.submit_approved_intent(intent, context)
    with pytest.raises(RuntimeNotProvisionedError):
        adapter.get_open_positions("tenant-a", "bot-1", context)
    with pytest.raises(RuntimeNotProvisionedError):
        adapter.get_orders("tenant-a", "bot-1", context)
    with pytest.raises(RuntimeNotProvisionedError):
        adapter.get_trades("tenant-a", "bot-1", context)

    assert submit_error.value.reason_code == "ORDER_SUBMISSION_NOT_IMPLEMENTED"
