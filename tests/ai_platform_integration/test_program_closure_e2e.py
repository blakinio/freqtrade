from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError
from strategy_engine.domain.models import (
    Action,
    FeatureRecord,
    Provenance,
    ShadowDecisionEvidence,
    Side,
    SignalEvent,
)
from strategy_engine.validation.leakage import (
    LeakageError,
    LeakageReason,
    assert_features_available,
)

from ai_platform.portal.contracts.audit import AuditAction
from ai_platform.portal.contracts.bots import (
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
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    TradeSide,
)
from ai_platform.portal.contracts.strategy_closure import (
    CapabilityRequirement,
    ClosureRequestContext,
    PublicContractProvenance,
    SignalWizardFeatureSelection,
    SignalWizardPreviewCommand,
    SignalWizardPreviewResult,
    SignalWizardSubmitCommand,
    StrategyCapability,
    StrategyMutationResult,
)
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.execution.errors import UnsupportedExecutionOperationError
from ai_platform.portal.execution.private_read import (
    OrderReadResult,
    PositionReadResult,
    PrivateOrderRecord,
    PrivateRuntimeSnapshot,
    PrivateTradeRecord,
    RuntimeReadFreshness,
    RuntimeReadKind,
    RuntimeReadReconciliationStatus,
    RuntimeReadStatus,
    TradeReadResult,
)
from ai_platform.portal.intelligence.schema import ReconciliationStatus
from ai_platform.portal.operations.service import OperationalReadService
from ai_platform.portal.risk.schema import RiskPolicyLimits
from ai_platform.portal.risk.service import RiskService
from ai_platform.portal.security.authorization import PermissionDeniedError
from ai_platform.portal.signal_wizard.service import (
    SignalWizardService,
    SignalWizardValidationError,
)
from ai_platform.portal.simulator.costs import ExecutionCostModel
from ai_platform.portal.simulator.exchange import DeterministicExchangeSimulator
from ai_platform.portal.simulator.funding import FundingEvent
from ai_platform.portal.simulator.schema import MarketTick, ScenarioManifest
from ai_platform.research.strategy_engine.ase03_integration import (
    Ase03AuditStore,
    Ase03Mode,
    Ase03PaperShadowController,
    Ase03Status,
)


NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
TENANT = "tenant-closure"
BOT_ID = "bot-program-closure"
RUNTIME_ID = "runtime-program-closure"
REQUEST_ID = UUID("70000000-0000-4000-8000-000000000001")
CORRELATION_ID = UUID("70000000-0000-4000-8000-000000000002")
CAUSATION_ID = UUID("70000000-0000-4000-8000-000000000003")
CODE_HASH = "1" * 64
DATA_HASH = "2" * 64
CONFIG_HASH = "3" * 64
REPO_ROOT = Path(__file__).resolve().parents[2]


def _permissions() -> tuple[Permission, ...]:
    return tuple(
        sorted(
            (
                Permission.AUDIT_READ,
                Permission.BOT_CREATE,
                Permission.BOT_READ,
                Permission.MODEL_READ,
                Permission.MODEL_TRAIN,
                Permission.RISK_MANAGE,
                Permission.TRADE_MANUAL_EXECUTE,
            ),
            key=lambda item: item.value,
        )
    )


def _context(
    tenant_id: str = TENANT,
    *,
    permissions: tuple[Permission, ...] | None = None,
) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id="program-closure-agent",
        actor_type=ActorType.USER,
        permissions=permissions or _permissions(),
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
        causation_id=CAUSATION_ID,
    )


def _correlation() -> CorrelationContext:
    return CorrelationContext(
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
        causation_id=CAUSATION_ID,
    )


def _closure_context(
    tenant_id: str = TENANT,
    *,
    environment: Environment = Environment.RESEARCH,
) -> ClosureRequestContext:
    return ClosureRequestContext(
        tenant_id=tenant_id,
        actor_id="program-closure-agent",
        actor_type=ActorType.USER,
        resource_type="strategy",
        resource_id="program-closure-strategy",
        environment=environment,
        execution_mode=ExecutionMode.SIMULATED,
        correlation=_correlation(),
        provenance=PublicContractProvenance(
            producer="program-closure-e2e",
            artifact_id="program-closure-fixture-v1",
            created_at=NOW,
            source_refs=("repository-fixture:program-closure-v1",),
            metadata={
                "evidence_class": "REPOSITORY_FIXTURE",
                "workflow": "paper-shadow-program-closure",
            },
        ),
    )


def _capability(value: StrategyCapability) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability=value,
        authorization_decision_ref=f"fixture-authorization:{value.value}",
    )


def _preview_command(
    *,
    tenant_id: str = TENANT,
    environment: Environment = Environment.RESEARCH,
) -> SignalWizardPreviewCommand:
    return SignalWizardPreviewCommand(
        context=_closure_context(tenant_id, environment=environment),
        idempotency_key="program-closure-preview-v1",
        strategy_id="program-closure-strategy",
        feature_selections=(
            SignalWizardFeatureSelection(
                feature_id="atr.v1",
                timeframe="5m",
                parameters={"period": 14},
            ),
        ),
        condition_ast={
            "all": [
                {
                    "feature": "atr.v1",
                    "parameter": "value",
                    "op": "gt",
                    "value": 0,
                }
            ]
        },
        capability=_capability(StrategyCapability.STRATEGY_RESEARCH),
    )


def _limits() -> RiskPolicyLimits:
    return RiskPolicyLimits(
        max_order_notional=Decimal(1000),
        max_projected_gross_exposure=Decimal(5000),
        max_projected_open_positions=3,
        max_daily_loss=Decimal(500),
        max_drawdown=Decimal("0.20"),
        require_healthy_runtime=True,
    )


def _manifest() -> ScenarioManifest:
    return ScenarioManifest(
        scenario_id="program-closure-simulation-v1",
        tenant_id=TENANT,
        bot_id=BOT_ID,
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("1.5"),
        environment=Environment.TEST,
        initial_equity=Decimal(1000),
        entry_tick=MarketTick(
            occurred_at=NOW,
            pair="BTC/USDT",
            price=Decimal(100),
        ),
        exit_tick=MarketTick(
            occurred_at=NOW + timedelta(minutes=5),
            pair="BTC/USDT",
            price=Decimal(105),
        ),
        seed=42,
        cost_model=ExecutionCostModel(
            entry_fee_rate=Decimal("0.001"),
            exit_fee_rate=Decimal("0.001"),
            entry_slippage_bps=Decimal(5),
            exit_slippage_bps=Decimal(5),
        ),
        funding_events=(
            FundingEvent(
                occurred_at=NOW + timedelta(minutes=3),
                rate=Decimal("0.0001"),
            ),
        ),
    )


def _bot_spec(strategy_version: str) -> BotSpec:
    return BotSpec(
        tenant_id=TENANT,
        strategy_version=strategy_version,
        model_version="selected-model-null",
        risk_policy_version="risk-program-closure-v1",
        exchange_connection_ref="deterministic-simulator-private",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation=Decimal(1000),
        capital_currency="USDT",
        runtime_version="private-dry-run-v1",
        config_revision=1,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
    )


def _source_status(
    kind: RuntimeReadKind,
    *,
    count: int,
) -> RuntimeReadStatus:
    return RuntimeReadStatus(
        tenant_id=TENANT,
        bot_id=BOT_ID,
        source_runtime_id=RUNTIME_ID,
        kind=kind,
        source_observed_at=NOW + timedelta(minutes=5),
        observed_at=NOW + timedelta(minutes=5),
        last_reconciled_at=NOW + timedelta(minutes=5),
        freshness=RuntimeReadFreshness.CURRENT,
        reconciliation_status=RuntimeReadReconciliationStatus.SYNCED,
        complete=True,
        record_count=count,
        reason_code=None,
    )


def _runtime_snapshot(
    *,
    order: OrderRecord,
    realized_pnl: Decimal,
    fees: Decimal,
    trade_id: str,
) -> PrivateRuntimeSnapshot:
    return PrivateRuntimeSnapshot(
        tenant_id=TENANT,
        bot_id=BOT_ID,
        source_runtime_id=RUNTIME_ID,
        observed_at=NOW + timedelta(minutes=5),
        positions=PositionReadResult(
            status=_source_status(RuntimeReadKind.OPEN_POSITIONS, count=0),
            records=(),
        ),
        orders=OrderReadResult(
            status=_source_status(RuntimeReadKind.ORDERS, count=1),
            records=(
                PrivateOrderRecord(
                    source_order_id=order.order_id,
                    source_trade_id=trade_id,
                    execution_intent_id=order.execution_intent_id,
                    pair=order.pair,
                    side=order.side,
                    state=order.state.value,
                    amount=order.amount,
                    created_at=order.created_at,
                    source_updated_at=NOW + timedelta(minutes=5),
                ),
            ),
        ),
        trades=TradeReadResult(
            status=_source_status(RuntimeReadKind.TRADES, count=1),
            records=(
                PrivateTradeRecord(
                    source_trade_id=trade_id,
                    pair="BTC/USDT",
                    side=TradeSide.BUY,
                    state="CLOSED",
                    amount=Decimal("1.5"),
                    opened_at=NOW,
                    closed_at=NOW + timedelta(minutes=5),
                    realized_pnl=realized_pnl,
                    fees=fees,
                    exit_reason="scenario_exit",
                    source_updated_at=NOW + timedelta(minutes=5),
                ),
            ),
        ),
    )


def _shadow_evidence(strategy_version: str) -> ShadowDecisionEvidence:
    provenance = Provenance(
        producer="program-closure-e2e",
        source_event_id="repository-fixture:program-closure",
        details={
            "evidence_class": "DETERMINISTIC_SIMULATION",
            "execution_adapter_used": False,
        },
    )
    feature = FeatureRecord(
        feature_id="atr.v1",
        feature_version="1.0.0",
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        event_time=NOW,
        detected_at=NOW,
        available_at=NOW,
        value={"value": 2.5},
        source="repository-fixture",
        is_confirmed=True,
        idempotency_key="program-closure-feature",
        code_version=CODE_HASH,
        data_version=DATA_HASH,
        configuration_hash=CONFIG_HASH,
        parameters={"period": 14},
        provenance=provenance,
    )
    signal = SignalEvent(
        signal_id="program-closure-signal",
        signal_version="1.0.0",
        strategy_id="program-closure-strategy",
        strategy_version=strategy_version,
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        side=Side.LONG,
        action=Action.ENTER,
        event_time=NOW,
        detected_at=NOW,
        available_at=NOW,
        source="program-closure-e2e",
        is_confirmed=True,
        idempotency_key="program-closure-signal",
        code_version=CODE_HASH,
        data_version=DATA_HASH,
        configuration_hash=CONFIG_HASH,
        reason_codes=("CLOSED_BAR_SIGNAL",),
        feature_snapshot={"atr.v1": 2.5},
        provenance=provenance,
        execution_policy={"execution_authority": False},
    )
    return ShadowDecisionEvidence.create(
        evidence_version="1.0.0",
        decision_time=NOW,
        symbol="BTC/USDT:USDT",
        timeframe="5m",
        strategy_id="program-closure-strategy",
        strategy_version=strategy_version,
        feature_records=(feature,),
        signal=signal,
        risk_outcome="approved",
        reason_codes=("RISK_APPROVED",),
        data_hash=DATA_HASH,
        config_hash=CONFIG_HASH,
        code_hash=CODE_HASH,
        idempotency_key="program-closure-shadow-evidence",
        provenance=provenance,
    )


class _EvidenceEngine:
    def __init__(self, evidence: ShadowDecisionEvidence) -> None:
        self.evidence = evidence
        self.calls = 0

    def run(self, **kwargs: Any) -> ShadowDecisionEvidence:
        del kwargs
        self.calls += 1
        return self.evidence


class _PrivateDryRunAdapter:
    def __init__(self) -> None:
        self.runtime_id = RUNTIME_ID
        self.state = BotObservedState.CREATED
        self.provision_calls = 0
        self.start_calls = 0
        self.stop_calls = 0
        self.submit_calls = 0

    def provision_bot(
        self,
        bot: BotInstance,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        del context
        assert bot.spec.environment is Environment.TEST
        assert bot.spec.execution_mode is ExecutionMode.DRY_RUN
        self.provision_calls += 1
        self.state = BotObservedState.CREATED
        return self._status(bot.tenant_id, bot.bot_id)

    def start_bot(
        self,
        bot: BotInstance,
        context: CorrelationContext,
    ) -> RuntimeStatus:
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


def _write_bundle(
    root: Path,
    *,
    passed: bool,
    stage: str,
    evidence: dict[str, Any],
    reason_code: str | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "evidence_class": "REPOSITORY_FIXTURE_AND_DETERMINISTIC_SIMULATION",
        "external_p11_acceptance": False,
        "passed": passed,
        "first_failure": None
        if passed
        else {
            "stage": stage,
            "reason_code": reason_code or "PROGRAM_CLOSURE_ASSERTION_FAILED",
        },
        "evidence": evidence,
    }
    (root / "program-closure-backend.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def test_canonical_paper_shadow_program_closure_e2e(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "program-closure"
    configured = Path(os.environ.get("PROGRAM_CLOSURE_ARTIFACT_DIR", str(artifact_root)))
    stage = "database_and_identity"
    evidence: dict[str, Any] = {
        "tenant_id": TENANT,
        "correlation_id": str(CORRELATION_ID),
    }

    try:
        engine = build_engine("sqlite+pysqlite:///:memory:")
        create_schema(engine)
        factory = build_session_factory(engine)
        context = _context()

        stage = "persisted_research_intent"
        wizard = SignalWizardService(factory)
        preview = wizard.preview(context, _preview_command())
        strategy_version = str(preview.strategy_definition["version"])
        submit = wizard.submit(
            context,
            SignalWizardSubmitCommand(
                context=_closure_context(),
                idempotency_key="program-closure-submit-v1",
                preview_hash=preview.preview_hash,
                experiment_name="Program closure deterministic candidate",
                expected_strategy_version=strategy_version,
                capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
            ),
        )
        assert submit.accepted is True
        assert submit.execution_authority is False
        assert submit.promotion_authority is False
        assert preview.strategy_definition["execution"]["use_closed_bars_only"] is True
        assert preview.strategy_definition["execution"]["live_capital_authority"] is False
        evidence["persisted_intent"] = {
            "experiment_id": submit.experiment_id,
            "preview_hash": preview.preview_hash,
            "strategy_version": strategy_version,
            "execution_authority": submit.execution_authority,
        }

        stage = "bot_and_risk_contract"
        control = ControlPlaneService(factory, clock=lambda: NOW)
        bot = control.create_bot(
            context,
            BOT_ID,
            "Program Closure Private Dry Run",
            _bot_spec(strategy_version),
        )
        risk = RiskService(factory, clock=lambda: NOW)
        policy = risk.register_policy(context, "risk-program-closure-v1", _limits())
        manifest = _manifest()
        simulator = DeterministicExchangeSimulator(manifest)
        snapshot = simulator.build_snapshot(
            context,
            bot,
            pair=manifest.pair,
            side=manifest.side,
            amount=manifest.amount,
        )
        approved = risk.evaluate_manual_intent(
            context,
            bot_id=BOT_ID,
            pair=manifest.pair,
            side=manifest.side,
            amount=manifest.amount,
            environment=Environment.TEST,
            risk_policy_version_id=policy.version.risk_policy_version_id,
            snapshot=snapshot,
        )
        assert isinstance(approved, ApprovedExecutionIntent)
        assert approved.risk_decision.reason_codes == ("RISK_APPROVED",)
        assert approved.context.correlation_id == CORRELATION_ID
        evidence["risk"] = {
            "decision": approved.risk_decision.decision.value,
            "reason_codes": list(approved.risk_decision.reason_codes),
            "policy_hash": policy.version.policy_hash,
        }

        stage = "authoritative_deterministic_execution_proof"
        order = simulator.submit_approved_intent(approved, _correlation())
        outcome = simulator.close_position()
        simulation = simulator.evidence()
        replay = DeterministicExchangeSimulator(manifest)
        replay_order = replay.submit_approved_intent(approved, _correlation())
        replay.close_position()
        replay_evidence = replay.evidence()
        assert replay_order.order_id == order.order_id
        assert replay_evidence.canonical_json() == simulation.canonical_json()
        assert replay_evidence.canonical_sha256() == simulation.canonical_sha256()
        evidence["execution_proof"] = {
            "classification": "DETERMINISTIC_SIMULATION",
            "order_id": order.order_id,
            "trade_id": outcome.trade_id,
            "outcome_id": str(outcome.outcome_id),
            "gross_pnl": str(simulation.gross_pnl),
            "fees": str(simulation.costs.total_fees),
            "funding_cash_flow": str(simulation.funding_cash_flow),
            "realized_pnl": str(simulation.realized_pnl),
            "evidence_hash": simulation.canonical_sha256(),
        }

        stage = "private_runtime_reconciliation"
        operations = OperationalReadService(factory)
        reconciled = operations.reconcile_private_runtime_snapshot(
            context,
            _runtime_snapshot(
                order=order,
                realized_pnl=simulation.realized_pnl,
                fees=simulation.costs.total_fees,
                trade_id=outcome.trade_id,
            ),
            expected_runtime_id=RUNTIME_ID,
        )
        assert reconciled.positions == ()
        assert reconciled.orders[0].source_order_id == order.order_id
        assert reconciled.orders[0].execution_intent_id == order.execution_intent_id
        assert reconciled.trades[0].source_trade_id == outcome.trade_id
        assert reconciled.trades[0].realized_pnl == simulation.realized_pnl
        assert reconciled.trades[0].fees == simulation.costs.total_fees
        assert reconciled.trades[0].reconciliation_status is ReconciliationStatus.SYNCED
        assert all(
            item.reconciliation_status is ReconciliationStatus.SYNCED
            for item in reconciled.source_statuses
        )
        evidence["reconciliation"] = {
            "status": "SYNCED",
            "source_runtime_id": RUNTIME_ID,
            "order_attribution": reconciled.orders[0].execution_intent_id,
            "trade_attribution": reconciled.trades[0].source_trade_id,
            "realized_pnl": str(reconciled.trades[0].realized_pnl),
        }

        stage = "paper_transport_acknowledgement"
        shadow = _shadow_evidence(strategy_version)
        adapter = _PrivateDryRunAdapter()
        store = Ase03AuditStore(tmp_path / "ase03-audit")
        controller = Ase03PaperShadowController(
            simulator_engine=_EvidenceEngine(shadow),
            shadow_engine=_EvidenceEngine(shadow),
            execution_adapter=adapter,
            audit_store=store,
            clock=lambda: NOW,
        )
        admission = controller.admit(
            idempotency_key="program-closure-paper-admission",
            mode=Ase03Mode.PAPER,
            tenant_id=TENANT,
            bot_id=BOT_ID,
            events=(),
            strategy_document=preview.strategy_definition,
            decision_time=NOW,
            risk_limits=_limits(),
            risk_snapshot=snapshot,
            context=_correlation(),
            bot=bot,
        )
        assert admission.status is Ase03Status.ADMITTED
        assert admission.runtime_observed_state == BotObservedState.RUNNING.value
        assert admission.execution_submission_performed is False
        assert admission.no_order_submitted is True
        assert adapter.provision_calls == 1
        assert adapter.start_calls == 1
        assert adapter.submit_calls == 0
        evidence["transport_acknowledgement"] = {
            "audit_hash": admission.record_hash,
            "runtime_id": admission.runtime_id,
            "runtime_state": admission.runtime_observed_state,
            "execution_submission_performed": False,
            "authoritative_execution_proof": False,
        }

        stage = "paper_rollback"
        rollback = controller.rollback(
            idempotency_key="program-closure-paper-rollback",
            admission=admission,
            context=_correlation(),
        )
        assert rollback.status is Ase03Status.ROLLED_BACK
        assert rollback.runtime_observed_state == BotObservedState.STOPPED.value
        assert rollback.source_admission_hash == admission.record_hash
        assert adapter.stop_calls == 1
        assert adapter.submit_calls == 0
        evidence["rollback"] = {
            "audit_hash": rollback.record_hash,
            "source_admission_hash": rollback.source_admission_hash,
            "runtime_state": rollback.runtime_observed_state,
        }

        stage = "audit_and_tenant_isolation"
        audit = operations.list_audit_events(context)
        risk_events = operations.list_risk_events(context)
        assert any(item.action is AuditAction.BOT_CREATED for item in audit)
        assert any(item.action is AuditAction.MANUAL_TRADE_INTENT for item in audit)
        assert any(item.correlation_id == CORRELATION_ID for item in audit)
        assert risk_events[-1].reason_codes == ("RISK_APPROVED",)

        other = _context(
            "tenant-other",
            permissions=tuple(
                sorted(
                    (Permission.AUDIT_READ, Permission.BOT_READ),
                    key=lambda item: item.value,
                )
            ),
        )
        other_runtime = operations.runtime_evidence(other)
        assert other_runtime.positions == ()
        assert other_runtime.orders == ()
        assert other_runtime.trades == ()
        assert other_runtime.source_statuses == ()
        assert operations.list_audit_events(other) == ()
        evidence["isolation"] = {
            "other_tenant_runtime_records": 0,
            "other_tenant_audit_records": 0,
        }

    except Exception as exc:
        _write_bundle(
            configured,
            passed=False,
            stage=stage,
            reason_code=type(exc).__name__,
            evidence=evidence,
        )
        raise

    _write_bundle(configured, passed=True, stage="complete", evidence=evidence)


def test_contract_api_security_and_timestamp_guards() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = build_session_factory(engine)
    context = _context()
    client = create_app(factory, lambda: context)
    openapi = client.openapi()
    assert "/v1/signal-wizard/preview" in openapi["paths"]
    assert "/v1/signal-wizard/submit" in openapi["paths"]
    assert "/v1/runtime-evidence" in openapi["paths"]

    preview_schema = SignalWizardPreviewResult.model_json_schema()
    mutation_schema = StrategyMutationResult.model_json_schema()
    assert preview_schema["properties"]["execution_authority"]["const"] is False
    assert preview_schema["properties"]["promotion_authority"]["const"] is False
    assert mutation_schema["properties"]["execution_authority"]["const"] is False
    assert mutation_schema["properties"]["live_capital_authority"]["const"] is False

    contracts_ts = (REPO_ROOT / "ai_platform/portal/web/lib/signal-wizard-contracts.ts").read_text(
        encoding="utf-8"
    )
    catalog_ts = (REPO_ROOT / "ai_platform/portal/web/lib/strategy-catalog-contracts.ts").read_text(
        encoding="utf-8"
    )
    for required in (
        'contract_version: "v2"',
        "execution_authority: false",
        "promotion_authority: false",
    ):
        assert required in contracts_ts
    for required in (
        'contract_version: "v2"',
        "execution_authority: false",
        "live_capital_authority: false",
    ):
        assert required in catalog_ts

    with pytest.raises(ValidationError, match="sensitive metadata key"):
        PublicContractProvenance(
            producer="forbidden",
            artifact_id="forbidden",
            created_at=NOW,
            metadata={"api_key": "must-not-serialize"},
        )

    wizard = SignalWizardService(factory)
    with pytest.raises(PermissionDeniedError):
        wizard.preview(
            _context(permissions=(Permission.MODEL_READ,)),
            _preview_command(),
        )
    with pytest.raises(SignalWizardValidationError) as cross_tenant:
        wizard.preview(context, _preview_command(tenant_id="tenant-other"))
    assert cross_tenant.value.reason_code == "SIGNAL_WIZARD_CONTEXT_MISMATCH"
    with pytest.raises(SignalWizardValidationError) as production:
        wizard.preview(
            context,
            _preview_command(environment=Environment.PRODUCTION),
        )
    assert production.value.reason_code == "SIGNAL_WIZARD_PRODUCTION_FORBIDDEN"

    future = (
        _shadow_evidence("program-closure-strategy:v1")
        .feature_records[0]
        .model_copy(update={"available_at": NOW + timedelta(seconds=1)})
    )
    with pytest.raises(LeakageError) as leakage:
        assert_features_available((future,), NOW)
    assert leakage.value.reason_code is LeakageReason.FEATURE_AFTER_DECISION


def test_browser_client_sources_exclude_direct_private_engines_and_secrets() -> None:
    web_root = REPO_ROOT / "ai_platform/portal/web"
    client_sources: list[Path] = []
    for root in (web_root / "app", web_root / "components", web_root / "lib"):
        for path in root.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            text = path.read_text(encoding="utf-8")
            if '"use client"' in text or "'use client'" in text:
                client_sources.append(path)

    forbidden = {
        "absolute Freqtrade URL": re.compile(
            r"https?://[^\s\"']*freqtrade",
            re.IGNORECASE,
        ),
        "direct Freqtrade control path": re.compile(
            r"/api/v1/(?:start|stop|forceenter|forceexit|trades|orders)",
            re.IGNORECASE,
        ),
        "exchange private endpoint": re.compile(
            r"https?://(?:api\.)?(?:binance|bybit|okx)\.[^\s\"']+",
            re.IGNORECASE,
        ),
        "Vault address": re.compile(r"(?:vault://|https?://[^\s\"']*vault)", re.IGNORECASE),
        "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "bearer token literal": re.compile(r"authorization\s*:\s*[\"']bearer\s+", re.IGNORECASE),
    }
    failures: list[str] = []
    for path in client_sources:
        text = path.read_text(encoding="utf-8")
        for label, pattern in forbidden.items():
            if pattern.search(text):
                failures.append(f"{path.relative_to(REPO_ROOT)}: {label}")

    assert failures == []
