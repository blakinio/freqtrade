from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai_platform.portal.bot_operations.activation_errors import CommandActivationAmbiguousError
from ai_platform.portal.bot_operations.activation_schema import (
    CommandActivationState,
    OrderCommandActivationRequest,
    PolicyEntryActivationRequest,
    PolicyEntrySource,
    PositionCommandActivationRequest,
    RuntimeCommandAcknowledgement,
    RuntimeOrderEvidence,
    RuntimePositionEvidence,
)
from ai_platform.portal.bot_operations.activation_service import BotCommandActivationService
from ai_platform.portal.bot_operations.schema import (
    AuthoritativeBotRuntimeState,
    BotCommandContext,
)
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    CommandConfirmationRequirement,
    CommandOutcomeStatus,
    CommandTarget,
    ConfirmationMethod,
    OrderAction,
    OrderCommand,
    PositionAction,
    PositionCommand,
)
from ai_platform.portal.contracts.bot_management.execution import (
    AcknowledgementStatus,
    ExecutionAcknowledgement,
    ExecutionAttempt,
    ExecutionAttemptState,
    ExecutionBinding,
    ExecutionReasonCode,
    ReconciliationRecord,
    ReconciliationState,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    TradeIntent,
    TradeSide,
)
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.credentials.material import CredentialMaterial, ResolvedCredentialLease
from ai_platform.portal.credentials.schema import (
    CredentialLeaseEvidence,
    CredentialLeaseRequest,
)
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.execution_submission.schema import (
    PrivateDryRunSubmission,
    PrivateSubmissionReceipt,
    RuntimeDryRunEvidence,
)
from ai_platform.portal.execution_submission.transport import PrivateRuntimeTarget


NOW = datetime(2026, 7, 29, 8, 0, tzinfo=UTC)
CORRELATION = CorrelationContext(
    request_id=UUID("10000000-0000-0000-0000-000000000001"),
    correlation_id=UUID("20000000-0000-0000-0000-000000000002"),
)
ACTOR = Actor(actor_id="actor-1", tenant_id="tenant-a", actor_type=ActorType.USER)
TARGET = CommandTarget(
    tenant_id="tenant-a",
    bot_id="bot-1",
    config_revision=7,
    runtime_generation_id="generation-1",
    runtime_id="runtime-1",
    runtime_revision=9,
)
RUNTIME = AuthoritativeBotRuntimeState(
    tenant_id="tenant-a",
    bot_id="bot-1",
    config_revision=7,
    runtime_generation_id="generation-1",
    runtime_id="runtime-1",
    runtime_revision=9,
    environment=Environment.TEST,
    freshness=RuntimeReadFreshness.CURRENT,
    kill_switch_active=False,
    observed_at=NOW,
)
CONFIRMATION = CommandConfirmationRequirement(
    required=True,
    step_up_required=True,
    method=ConfirmationMethod.STEP_UP_MFA,
    confirmation_reference="step-up-1",
)


class _Broker:
    def __init__(self) -> None:
        self.calls = 0
        self.last_lease: ResolvedCredentialLease | None = None

    def resolve(self, request: CredentialLeaseRequest) -> ResolvedCredentialLease:
        self.calls += 1
        self.last_lease = ResolvedCredentialLease(
            evidence=CredentialLeaseEvidence(
                lease_id="credlease_0123456789abcdef0123456789abcdef",
                tenant_id=request.tenant_id,
                connection_id=request.connection_id,
                credential_ref=request.credential_ref,
                exchange_id=request.exchange_id,
                runtime_id=request.runtime_id,
                purpose=request.purpose,
                vault_version=1,
                issued_at=NOW,
                expires_at=NOW + timedelta(minutes=5),
                rotated_at=NOW - timedelta(days=1),
                evidence_ref="vault-evidence-1",
            ),
            _material=CredentialMaterial.from_values(
                exchange_api_key="exchange-key-secret",
                exchange_api_secret="exchange-secret",
                exchange_passphrase=None,
                runtime_api_username="runtime-user-secret",
                runtime_api_password="runtime-password-secret",
            ),
        )
        return self.last_lease


class _Resolver:
    def __init__(self, target: PrivateRuntimeTarget) -> None:
        self.target = target
        self.calls = 0

    def resolve(self, runtime_id: str) -> PrivateRuntimeTarget:
        self.calls += 1
        assert runtime_id == self.target.runtime_id
        return self.target


class _Verifier:
    def __init__(self) -> None:
        self.calls = 0

    def verify_dry_run(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
    ) -> RuntimeDryRunEvidence:
        del lease
        self.calls += 1
        return RuntimeDryRunEvidence(
            runtime_id=target.runtime_id,
            verified_at=NOW,
            config_digest="0" * 64,
        )


class _Transport:
    def __init__(self) -> None:
        self.force_exit_calls: list[tuple[str, str | None]] = []
        self.cancel_calls: list[str] = []
        self.ambiguous = False

    def force_exit(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        *,
        trade_id: str,
        amount: str | None = None,
    ) -> RuntimeCommandAcknowledgement:
        del target, lease
        self.force_exit_calls.append((trade_id, amount))
        if self.ambiguous:
            raise CommandActivationAmbiguousError("a" * 64)
        return _ack(f"force-{trade_id}")

    def cancel_open_order(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        *,
        trade_id: str,
    ) -> RuntimeCommandAcknowledgement:
        del target, lease
        self.cancel_calls.append(trade_id)
        if self.ambiguous:
            raise CommandActivationAmbiguousError("b" * 64)
        return _ack(f"cancel-{trade_id}")


class _ReplacementService:
    def __init__(self) -> None:
        self.calls = 0
        self.receipt: PrivateSubmissionReceipt | None = None

    def submit(self, submission: PrivateDryRunSubmission) -> PrivateSubmissionReceipt:
        self.calls += 1
        if self.receipt is None:
            self.receipt = _replacement_receipt(submission)
        return self.receipt


def _ack(reference: str) -> RuntimeCommandAcknowledgement:
    return RuntimeCommandAcknowledgement(
        runtime_request_ref=reference,
        response_digest="1" * 64,
        acknowledged_at=NOW,
    )


def _context(capability: BotManagementCapability) -> BotCommandContext:
    return BotCommandContext(
        tenant_id="tenant-a",
        actor=ACTOR,
        environment=Environment.TEST,
        capabilities=(capability,),
    )


def _position_command(
    action: PositionAction,
    *,
    command_id: str = "position-command-1",
) -> PositionCommand:
    capability = {
        PositionAction.CLOSE_POSITION: BotManagementCapability.POSITION_CLOSE,
        PositionAction.PARTIAL_CLOSE: BotManagementCapability.POSITION_PARTIAL_CLOSE,
        PositionAction.CLOSE_ALL: BotManagementCapability.POSITION_CLOSE_ALL,
        PositionAction.FORCE_TAKE_PROFIT: BotManagementCapability.POSITION_CLOSE,
    }[action]
    values: dict[str, Any] = {
        "command_id": command_id,
        "tenant_id": "tenant-a",
        "actor": ACTOR,
        "environment": Environment.TEST,
        "capability": capability,
        "target": TARGET,
        "correlation": CORRELATION,
        "idempotency_key": f"idem-{command_id}",
        "confirmation": CONFIRMATION,
        "submitted_at": NOW,
        "action": action,
    }
    if action != PositionAction.CLOSE_ALL:
        values.update(position_id="position-1", position_revision=3)
    if action == PositionAction.PARTIAL_CLOSE:
        values["close_fraction"] = Decimal("0.25")
    return PositionCommand.model_validate(values)


def _order_command(
    action: OrderAction,
    *,
    command_id: str = "order-command-1",
) -> OrderCommand:
    capability = {
        OrderAction.CANCEL_ORDER: BotManagementCapability.ORDER_CANCEL,
        OrderAction.CANCEL_ALL_ORDERS: BotManagementCapability.ORDER_CANCEL_ALL,
        OrderAction.REPLACE_ORDER: BotManagementCapability.ORDER_REPLACE,
    }[action]
    values: dict[str, Any] = {
        "command_id": command_id,
        "tenant_id": "tenant-a",
        "actor": ACTOR,
        "environment": Environment.TEST,
        "capability": capability,
        "target": TARGET,
        "correlation": CORRELATION,
        "idempotency_key": f"idem-{command_id}",
        "confirmation": CONFIRMATION,
        "submitted_at": NOW,
        "action": action,
    }
    if action != OrderAction.CANCEL_ALL_ORDERS:
        values.update(order_id="order-1", order_revision=4)
    if action == OrderAction.REPLACE_ORDER:
        values["replacement_quantity"] = Decimal("25")
    return OrderCommand.model_validate(values)


def _position() -> RuntimePositionEvidence:
    return RuntimePositionEvidence(
        tenant_id="tenant-a",
        bot_id="bot-1",
        runtime_id="runtime-1",
        position_id="position-1",
        position_revision=3,
        source_trade_id="77",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("100"),
        observed_at=NOW,
    )


def _order(order_id: str = "order-1", trade_id: str = "77") -> RuntimeOrderEvidence:
    return RuntimeOrderEvidence(
        tenant_id="tenant-a",
        bot_id="bot-1",
        runtime_id="runtime-1",
        order_id=order_id,
        order_revision=4,
        source_trade_id=trade_id,
        pair="BTC/USDT",
        side=TradeSide.BUY,
        stake_amount=Decimal("25"),
        observed_at=NOW,
    )


def _submission() -> PrivateDryRunSubmission:
    trade_intent = TradeIntent(
        trade_intent_id=UUID("40000000-0000-0000-0000-000000000004"),
        tenant_id="tenant-a",
        bot_id="bot-1",
        source_actor_id="actor-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("25"),
        environment=Environment.TEST,
        created_at=NOW - timedelta(seconds=1),
        context=CORRELATION,
    )
    decision = RiskDecision(
        risk_decision_id=UUID("50000000-0000-0000-0000-000000000005"),
        tenant_id="tenant-a",
        trade_intent_id=trade_intent.trade_intent_id,
        risk_policy_version="risk-v1",
        decision=RiskDecisionOutcome.APPROVED,
        reason_codes=("RISK_APPROVED",),
        evaluated_limits=(
            RiskLimitEvaluation(
                limit_name="max_order_amount",
                configured_value="100",
                observed_value="25",
                passed=True,
            ),
        ),
        occurred_at=NOW,
        context=CORRELATION,
    )
    intent = ApprovedExecutionIntent(
        execution_intent_id=UUID("60000000-0000-0000-0000-000000000006"),
        tenant_id="tenant-a",
        trade_intent=trade_intent,
        risk_decision=decision,
        created_at=NOW,
        context=CORRELATION,
    )
    return PrivateDryRunSubmission(
        command_id="replacement-command-1",
        intent=intent,
        binding=ExecutionBinding(
            tenant_id="tenant-a",
            bot_id="bot-1",
            config_revision=7,
            runtime_id="runtime-1",
            runtime_revision=9,
            environment=Environment.TEST,
            execution_mode=ExecutionMode.DRY_RUN,
            idempotency_key="replacement-idem-1",
            correlation=CORRELATION,
        ),
        runtime=RUNTIME,
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        approved_until=NOW + timedelta(minutes=1),
    )


def _replacement_receipt(submission: PrivateDryRunSubmission) -> PrivateSubmissionReceipt:
    attempt_id = "exec_0123456789abcdef0123456789abcdef"
    acknowledgement = ExecutionAcknowledgement(
        acknowledgement_id="ack-replacement-1",
        attempt_id=attempt_id,
        binding=submission.binding,
        status=AcknowledgementStatus.ACCEPTED,
        reason_codes=(ExecutionReasonCode.ACKNOWLEDGED_NOT_EXECUTED,),
        runtime_request_ref="freqtrade-trade_id-88",
        received_at=NOW,
    )
    return PrivateSubmissionReceipt(
        attempt=ExecutionAttempt(
            attempt_id=attempt_id,
            command_id=submission.command_id,
            binding=submission.binding,
            state=ExecutionAttemptState.ACKNOWLEDGED,
            attempt_number=1,
            started_at=NOW,
            completed_at=NOW,
            acknowledgement_ref=acknowledgement.acknowledgement_id,
        ),
        acknowledgement=acknowledgement,
        reconciliation=ReconciliationRecord(
            reconciliation_id="recon-1",
            attempt_id=attempt_id,
            command_id=submission.command_id,
            binding=submission.binding,
            state=ReconciliationState.PENDING,
            started_at=NOW,
        ),
        runtime_config=RuntimeDryRunEvidence(
            runtime_id="runtime-1",
            verified_at=NOW,
            config_digest="0" * 64,
        ),
    )


def _service(tmp_path: Path):
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    command_service = BotCommandService(build_session_factory(engine), clock=lambda: NOW)
    certificate = tmp_path / "runtime-ca.pem"
    certificate.write_text("test-ca", encoding="utf-8")
    broker = _Broker()
    resolver = _Resolver(
        PrivateRuntimeTarget(
            runtime_id="runtime-1",
            endpoint="https://freqtrade.internal:8443",
            ca_certificate_path=certificate,
        )
    )
    verifier = _Verifier()
    transport = _Transport()
    replacement = _ReplacementService()
    service = BotCommandActivationService(
        command_service,
        broker,
        resolver,
        verifier,
        transport,
        replacement,
    )
    return service, broker, resolver, verifier, transport, replacement


def test_partial_close_is_reserved_before_io_and_replay_is_safe(tmp_path: Path) -> None:
    service, broker, resolver, verifier, transport, _replacement = _service(tmp_path)
    request = PositionCommandActivationRequest(
        context=_context(BotManagementCapability.POSITION_PARTIAL_CLOSE),
        command=_position_command(PositionAction.PARTIAL_CLOSE),
        runtime=RUNTIME,
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        positions=(_position(),),
    )

    first = service.activate_position(request)
    replay = service.activate_position(request)

    assert first.activation_state == CommandActivationState.ACKNOWLEDGED
    assert first.outcome.status == CommandOutcomeStatus.PENDING_RECONCILIATION
    assert first.acknowledgement is not None and first.acknowledgement.execution_proven is False
    assert transport.force_exit_calls == [("77", "25.00")]
    assert replay.activation_state == CommandActivationState.REPLAY_PENDING
    assert replay.execution_attempt_ref == first.execution_attempt_ref
    assert broker.calls == resolver.calls == verifier.calls == 1
    assert broker.last_lease is not None and broker.last_lease.closed


def test_degraded_health_blocks_before_credentials_or_runtime(tmp_path: Path) -> None:
    service, broker, resolver, verifier, transport, _replacement = _service(tmp_path)
    request = PositionCommandActivationRequest(
        context=_context(BotManagementCapability.POSITION_CLOSE),
        command=_position_command(PositionAction.CLOSE_POSITION),
        runtime=RUNTIME,
        runtime_health=RuntimeHealthState.DEGRADED,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        positions=(_position(),),
    )

    result = service.activate_position(request)

    assert result.activation_state == CommandActivationState.NOT_SUBMITTED
    assert result.outcome.status == CommandOutcomeStatus.BLOCKED
    assert broker.calls == resolver.calls == verifier.calls == 0
    assert transport.force_exit_calls == []


def test_ambiguous_close_remains_pending_and_is_not_retried(tmp_path: Path) -> None:
    service, _broker, _resolver, _verifier, transport, _replacement = _service(tmp_path)
    transport.ambiguous = True
    request = PositionCommandActivationRequest(
        context=_context(BotManagementCapability.POSITION_CLOSE),
        command=_position_command(PositionAction.FORCE_TAKE_PROFIT),
        runtime=RUNTIME,
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        positions=(_position(),),
    )

    first = service.activate_position(request)
    replay = service.activate_position(request)

    assert first.activation_state == CommandActivationState.AMBIGUOUS
    assert first.outcome.status == CommandOutcomeStatus.PENDING_RECONCILIATION
    assert replay.activation_state == CommandActivationState.REPLAY_PENDING
    assert transport.force_exit_calls == [("77", None)]


def test_cancel_all_is_deterministic_and_replace_reuses_pi08(tmp_path: Path) -> None:
    service, _broker, _resolver, _verifier, transport, replacement = _service(tmp_path)
    cancel_all = OrderCommandActivationRequest(
        context=_context(BotManagementCapability.ORDER_CANCEL_ALL),
        command=_order_command(OrderAction.CANCEL_ALL_ORDERS, command_id="cancel-all-1"),
        runtime=RUNTIME,
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        orders=(_order("order-2", "88"), _order("order-1", "77")),
    )
    cancel_result = service.activate_order(cancel_all)
    assert cancel_result.activation_state == CommandActivationState.ACKNOWLEDGED
    assert transport.cancel_calls == ["77", "88"]

    replace = OrderCommandActivationRequest(
        context=_context(BotManagementCapability.ORDER_REPLACE),
        command=_order_command(OrderAction.REPLACE_ORDER, command_id="replace-1"),
        runtime=RUNTIME,
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        orders=(_order(),),
        replacement_submission=_submission(),
    )
    replace_result = service.activate_order(replace)
    assert replace_result.activation_state == CommandActivationState.ACKNOWLEDGED
    assert replacement.calls == 1
    assert transport.cancel_calls[-1] == "77"


def test_price_replace_and_cross_tenant_evidence_fail_closed() -> None:
    price_values = _order_command(OrderAction.REPLACE_ORDER).model_dump()
    price_values.update(replacement_quantity=None, replacement_price=Decimal("65000"))
    price_command = OrderCommand.model_validate(price_values)
    with pytest.raises(ValidationError, match="price-changing replace"):
        OrderCommandActivationRequest(
            context=_context(BotManagementCapability.ORDER_REPLACE),
            command=price_command,
            runtime=RUNTIME,
            runtime_health=RuntimeHealthState.HEALTHY,
            connection_id="connection-1",
            credential_ref="credref_okxDryRun01",
            exchange_id="okx",
            orders=(_order(),),
            replacement_submission=_submission(),
        )

    foreign = _position().model_copy(update={"tenant_id": "tenant-b"})
    with pytest.raises(ValidationError, match="scope mismatch"):
        PositionCommandActivationRequest(
            context=_context(BotManagementCapability.POSITION_CLOSE),
            command=_position_command(PositionAction.CLOSE_POSITION),
            runtime=RUNTIME,
            runtime_health=RuntimeHealthState.HEALTHY,
            connection_id="connection-1",
            credential_ref="credref_okxDryRun01",
            exchange_id="okx",
            positions=(foreign,),
        )


def test_dca_and_grid_entries_delegate_to_single_pi08_path(tmp_path: Path) -> None:
    service, _broker, _resolver, _verifier, _transport, replacement = _service(tmp_path)
    receipt = service.activate_policy_entry(
        PolicyEntryActivationRequest(
            source=PolicyEntrySource.DCA,
            policy_ref="dca-policy-v1",
            evidence_ref="dca-evidence-1",
            submission=_submission(),
        )
    )
    assert receipt.acknowledgement is not None
    assert replacement.calls == 1
