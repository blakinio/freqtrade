from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from strategy_engine.domain.models import (
    Action,
    FeatureRecord,
    Provenance,
    ShadowDecisionEvidence,
    Side,
    SignalEvent,
)

from ai_platform.portal.contracts.bots import (
    BotDesiredState,
    BotInstance,
    BotObservedState,
    BotSpec,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import (
    ExecutionHealth,
    OpenPosition,
    OrderRecord,
    RuntimeHealthState,
    RuntimeStatus,
    TradeRecord,
)
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent
from ai_platform.portal.execution.errors import UnsupportedExecutionOperationError
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
from ai_platform.research.strategy_engine.ase03_integration import (
    Ase03AuditStore,
    Ase03Mode,
    Ase03PaperShadowController,
    Ase03Status,
)

NOW = datetime(2026, 7, 29, 20, 0, tzinfo=UTC)
DATA_HASH = "1" * 64
CONFIG_HASH = "2" * 64
CODE_HASH = "3" * 64


class _Engine:
    def __init__(self, evidence: ShadowDecisionEvidence) -> None:
        self.evidence = evidence
        self.calls = 0

    def run(self, **kwargs: Any) -> ShadowDecisionEvidence:
        del kwargs
        self.calls += 1
        return self.evidence


class _Adapter:
    def __init__(self) -> None:
        self.runtime_id = "runtime-paper-1"
        self.state = BotObservedState.CREATED
        self.provision_calls = 0
        self.start_calls = 0
        self.stop_calls = 0
        self.submit_calls = 0

    def provision_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus:
        del context
        self.provision_calls += 1
        assert bot.spec.execution_mode is ExecutionMode.DRY_RUN
        self.state = BotObservedState.CREATED
        return self._status(bot.tenant_id, bot.bot_id)

    def start_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus:
        del context
        self.start_calls += 1
        self.state = BotObservedState.RUNNING
        return self._status(bot.tenant_id, bot.bot_id)

    def pause_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        del context
        self.state = BotObservedState.PAUSED
        return self._status(tenant_id, bot_id)

    def stop_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        del context
        self.stop_calls += 1
        self.state = BotObservedState.STOPPED
        return self._status(tenant_id, bot_id)

    def get_health(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> ExecutionHealth:
        del context
        return ExecutionHealth(
            tenant_id=tenant_id,
            bot_id=bot_id,
            runtime_id=self.runtime_id,
            health=RuntimeHealthState.HEALTHY,
            observed_at=NOW,
            reason_code=None,
        )

    def get_runtime_status(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        del context
        return self._status(tenant_id, bot_id)

    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord:
        del intent, context
        self.submit_calls += 1
        raise UnsupportedExecutionOperationError("ORDER_SUBMISSION_NOT_IMPLEMENTED")

    def get_open_positions(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[OpenPosition, ...]:
        del tenant_id, bot_id, context
        return ()

    def get_orders(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[OrderRecord, ...]:
        del tenant_id, bot_id, context
        return ()

    def get_trades(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[TradeRecord, ...]:
        del tenant_id, bot_id, context
        return ()

    def _status(self, tenant_id: str, bot_id: str) -> RuntimeStatus:
        return RuntimeStatus(
            tenant_id=tenant_id,
            bot_id=bot_id,
            runtime_id=self.runtime_id,
            observed_state=self.state,
            observed_at=NOW,
        )


def _context() -> CorrelationContext:
    return CorrelationContext(
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _bot(environment: Environment = Environment.TEST) -> BotInstance:
    return BotInstance(
        bot_id="bot-paper-1",
        tenant_id="tenant-a",
        name="ASE-03 paper bot",
        spec=BotSpec(
            tenant_id="tenant-a",
            strategy_version="strategy-v1",
            model_version="model-v1",
            risk_policy_version="risk-v1",
            exchange_connection_ref="exchange-dry-run-1",
            pair_universe=("BTC/USDT",),
            timeframe="5m",
            capital_allocation=Decimal("1000"),
            capital_currency="USDT",
            runtime_version="runtime-v1",
            config_revision=1,
            environment=environment,
            execution_mode=ExecutionMode.DRY_RUN,
        ),
        desired_state=BotDesiredState.CREATED,
        observed_state=BotObservedState.CREATED,
    )


def _limits() -> RiskPolicyLimits:
    return RiskPolicyLimits(
        max_order_notional=Decimal("1000"),
        max_projected_gross_exposure=Decimal("5000"),
        max_projected_open_positions=3,
        max_daily_loss=Decimal("500"),
        max_drawdown=Decimal("0.20"),
        require_healthy_runtime=True,
    )


def _snapshot() -> RiskEvaluationSnapshot:
    return RiskEvaluationSnapshot(
        intent_notional=Decimal("100"),
        projected_gross_exposure=Decimal("100"),
        projected_open_positions=1,
        daily_loss=Decimal("0"),
        current_drawdown=Decimal("0"),
        runtime_health=RuntimeHealthState.HEALTHY,
    )


def _evidence(
    *,
    action: Action = Action.ENTER,
    risk_outcome: Literal["approved", "rejected", "no_signal"] = "approved",
) -> ShadowDecisionEvidence:
    provenance = Provenance(
        producer="ase03-test",
        source_event_id="synthetic:ase03",
        details={"execution_adapter_used": False},
    )
    feature = FeatureRecord(
        feature_id="roc.v1",
        feature_version="1.0.0",
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        event_time=NOW,
        detected_at=NOW,
        available_at=NOW,
        value={"value": 1.0},
        source="synthetic",
        is_confirmed=True,
        idempotency_key="feature:ase03",
        code_version=CODE_HASH,
        data_version=DATA_HASH,
        configuration_hash=CONFIG_HASH,
        parameters={"period": 12},
        provenance=provenance,
    )
    signal = SignalEvent(
        signal_id="signal-ase03",
        signal_version="1.0.0",
        strategy_id="strategy-v1",
        strategy_version="1.0.0",
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        side=Side.LONG,
        action=action,
        event_time=NOW,
        detected_at=NOW,
        available_at=NOW,
        source="ase03-test",
        is_confirmed=True,
        idempotency_key=f"signal:ase03:{action.value}",
        code_version=CODE_HASH,
        data_version=DATA_HASH,
        configuration_hash=CONFIG_HASH,
        reason_codes=("SYNTHETIC_SIGNAL",),
        feature_snapshot={"roc.v1": 1.0},
        provenance=provenance,
        execution_policy={"execution_authority": False},
    )
    return ShadowDecisionEvidence.create(
        evidence_version="1.0.0",
        decision_time=NOW,
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        strategy_id="strategy-v1",
        strategy_version="1.0.0",
        feature_records=(feature,),
        signal=None if risk_outcome == "no_signal" else signal,
        risk_outcome=risk_outcome,
        reason_codes=("RISK_APPROVED",) if risk_outcome == "approved" else ("RISK_REJECTED",),
        data_hash=DATA_HASH,
        config_hash=CONFIG_HASH,
        code_hash=CODE_HASH,
        idempotency_key=f"evidence:ase03:{action.value}:{risk_outcome}",
        provenance=provenance,
    )


def _controller(
    tmp_path: Path,
    *,
    simulator: ShadowDecisionEvidence | None = None,
    shadow: ShadowDecisionEvidence | None = None,
) -> tuple[Ase03PaperShadowController, _Adapter, _Engine, _Engine, Ase03AuditStore]:
    simulator_engine = _Engine(simulator or _evidence())
    shadow_engine = _Engine(shadow or _evidence())
    adapter = _Adapter()
    store = Ase03AuditStore(tmp_path)
    controller = Ase03PaperShadowController(
        simulator_engine=simulator_engine,
        shadow_engine=shadow_engine,
        execution_adapter=adapter,
        audit_store=store,
        clock=lambda: NOW,
    )
    return controller, adapter, simulator_engine, shadow_engine, store


def _admit(
    controller: Ase03PaperShadowController,
    *,
    mode: Ase03Mode,
    idempotency_key: str,
    bot: BotInstance | None = None,
):
    return controller.admit(
        idempotency_key=idempotency_key,
        mode=mode,
        tenant_id="tenant-a",
        bot_id="bot-paper-1",
        events=(),
        strategy_document={"strategy_id": "strategy-v1"},
        decision_time=NOW,
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
        context=_context(),
        bot=bot,
    )


def test_shadow_admission_is_append_only_and_never_touches_runtime(tmp_path: Path) -> None:
    controller, adapter, simulator, shadow, store = _controller(tmp_path)

    first = _admit(controller, mode=Ase03Mode.SHADOW, idempotency_key="admit-shadow")
    replay = _admit(controller, mode=Ase03Mode.SHADOW, idempotency_key="admit-shadow")

    assert first.status is Ase03Status.ADMITTED
    assert replay.record_hash == first.record_hash
    assert simulator.calls == 1
    assert shadow.calls == 1
    assert adapter.provision_calls == 0
    assert adapter.submit_calls == 0
    assert len(store.records()) == 1
    assert all((tmp_path / reference).exists() for reference in first.evidence_refs.values())


def test_paper_admission_starts_only_private_dry_run_runtime(tmp_path: Path) -> None:
    controller, adapter, _simulator, _shadow, store = _controller(tmp_path)

    admission = _admit(
        controller,
        mode=Ase03Mode.PAPER,
        idempotency_key="admit-paper",
        bot=_bot(),
    )

    assert admission.status is Ase03Status.ADMITTED
    assert admission.runtime_observed_state == BotObservedState.RUNNING.value
    assert admission.runtime_health == RuntimeHealthState.HEALTHY.value
    assert admission.execution_submission_performed is False
    assert admission.no_order_submitted is True
    assert adapter.provision_calls == 1
    assert adapter.start_calls == 1
    assert adapter.submit_calls == 0
    assert store.records() == (admission,)


def test_parity_mismatch_rejects_before_runtime(tmp_path: Path) -> None:
    controller, adapter, _simulator, _shadow, _store = _controller(
        tmp_path,
        shadow=_evidence(action=Action.EXIT),
    )

    admission = _admit(
        controller,
        mode=Ase03Mode.PAPER,
        idempotency_key="reject-parity",
        bot=_bot(),
    )

    assert admission.status is Ase03Status.REJECTED
    assert "SIMULATOR_PARITY_REJECTED" in admission.reason_codes
    assert "PARITY_SIGNAL_MISMATCH" in admission.reason_codes
    assert adapter.provision_calls == 0
    assert adapter.submit_calls == 0


def test_risk_rejection_blocks_paper_runtime(tmp_path: Path) -> None:
    rejected = _evidence(risk_outcome="rejected")
    controller, adapter, _simulator, _shadow, _store = _controller(
        tmp_path,
        simulator=rejected,
        shadow=rejected,
    )

    admission = _admit(
        controller,
        mode=Ase03Mode.PAPER,
        idempotency_key="reject-risk",
        bot=_bot(),
    )

    assert admission.status is Ase03Status.REJECTED
    assert "RISK_APPROVAL_REQUIRED" in admission.reason_codes
    assert adapter.provision_calls == 0


def test_production_environment_is_rejected_even_in_dry_run(tmp_path: Path) -> None:
    controller, adapter, _simulator, _shadow, _store = _controller(tmp_path)

    admission = _admit(
        controller,
        mode=Ase03Mode.PAPER,
        idempotency_key="reject-production",
        bot=_bot(Environment.PRODUCTION),
    )

    assert admission.status is Ase03Status.REJECTED
    assert "PAPER_ENVIRONMENT_FORBIDDEN" in admission.reason_codes
    assert adapter.provision_calls == 0


def test_paper_rollback_stops_runtime_and_replays_idempotently(tmp_path: Path) -> None:
    controller, adapter, _simulator, _shadow, store = _controller(tmp_path)
    admission = _admit(
        controller,
        mode=Ase03Mode.PAPER,
        idempotency_key="admit-for-rollback",
        bot=_bot(),
    )

    first = controller.rollback(
        idempotency_key="rollback-paper",
        admission=admission,
        context=_context(),
    )
    replay = controller.rollback(
        idempotency_key="rollback-paper",
        admission=admission,
        context=_context(),
    )

    assert first.status is Ase03Status.ROLLED_BACK
    assert first.runtime_observed_state == BotObservedState.STOPPED.value
    assert first.source_admission_hash == admission.record_hash
    assert replay.record_hash == first.record_hash
    assert adapter.stop_calls == 1
    assert adapter.submit_calls == 0
    assert store.records() == (admission, first)
