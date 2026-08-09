from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from ai_platform.portal.bot_operations.schema import AuthoritativeBotRuntimeState
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
from ai_platform.portal.contracts.execution import OrderState, RuntimeHealthState
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    TradeIntent,
    TradeSide,
)
from ai_platform.portal.execution.errors import UnsupportedExecutionOperationError
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.execution_submission.integration import (
    PrivateDryRunApprovedIntentSubmitter,
)
from ai_platform.portal.execution_submission.schema import (
    PrivateDryRunSubmission,
    PrivateSubmissionReceipt,
    RuntimeDryRunEvidence,
)


NOW = datetime(2026, 7, 29, 6, 0, tzinfo=UTC)
CONTEXT = CorrelationContext(
    request_id=UUID("10000000-0000-0000-0000-000000000001"),
    correlation_id=UUID("20000000-0000-0000-0000-000000000002"),
)


def _intent() -> ApprovedExecutionIntent:
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
        context=CONTEXT,
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
        context=CONTEXT,
    )
    return ApprovedExecutionIntent(
        execution_intent_id=UUID("60000000-0000-0000-0000-000000000006"),
        tenant_id="tenant-a",
        trade_intent=trade_intent,
        risk_decision=decision,
        created_at=NOW,
        context=CONTEXT,
    )


def _submission(intent: ApprovedExecutionIntent) -> PrivateDryRunSubmission:
    binding = ExecutionBinding(
        tenant_id="tenant-a",
        bot_id="bot-1",
        config_revision=7,
        runtime_id="runtime-1",
        runtime_revision=9,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
        idempotency_key="submit-intent-1",
        correlation=CONTEXT,
    )
    return PrivateDryRunSubmission(
        command_id="command-1",
        intent=intent,
        binding=binding,
        runtime=AuthoritativeBotRuntimeState(
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
        ),
        runtime_health=RuntimeHealthState.HEALTHY,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        approved_until=NOW + timedelta(minutes=1),
    )


def _receipt(
    submission: PrivateDryRunSubmission,
    *,
    accepted: bool,
) -> PrivateSubmissionReceipt:
    attempt_id = "exec_0123456789abcdef0123456789abcdef"
    reconciliation = ReconciliationRecord(
        reconciliation_id="recon_exec_0123456789abcdef0123456789abcdef",
        attempt_id=attempt_id,
        command_id=submission.command_id,
        binding=submission.binding,
        state=ReconciliationState.PENDING,
        started_at=NOW,
    )
    if not accepted:
        return PrivateSubmissionReceipt(
            attempt=ExecutionAttempt(
                attempt_id=attempt_id,
                command_id=submission.command_id,
                binding=submission.binding,
                state=ExecutionAttemptState.AMBIGUOUS,
                attempt_number=1,
                started_at=NOW,
                completed_at=NOW,
            ),
            ambiguity={
                "ambiguity_id": "ambiguity-1",
                "attempt_id": attempt_id,
                "binding": submission.binding,
                "reason_code": ExecutionReasonCode.TRANSPORT_AMBIGUOUS,
                "observed_at": NOW,
            },
            reconciliation=reconciliation.model_copy(
                update={"reason_codes": (ExecutionReasonCode.TRANSPORT_AMBIGUOUS,)}
            ),
        )
    acknowledgement = ExecutionAcknowledgement(
        acknowledgement_id="ack-1",
        attempt_id=attempt_id,
        binding=submission.binding,
        status=AcknowledgementStatus.ACCEPTED,
        reason_codes=(ExecutionReasonCode.ACKNOWLEDGED_NOT_EXECUTED,),
        runtime_request_ref="freqtrade-trade_id-77",
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
        reconciliation=reconciliation,
        runtime_config=RuntimeDryRunEvidence(
            runtime_id="runtime-1",
            verified_at=NOW,
            config_digest="0" * 64,
        ),
    )


class _Factory:
    def __init__(self, submission: PrivateDryRunSubmission) -> None:
        self.submission = submission
        self.calls = 0

    def build(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> PrivateDryRunSubmission:
        self.calls += 1
        assert intent == self.submission.intent
        assert context == self.submission.binding.correlation
        return self.submission


class _Service:
    def __init__(self, receipt: PrivateSubmissionReceipt) -> None:
        self.receipt = receipt
        self.calls = 0

    def submit(self, submission: PrivateDryRunSubmission) -> PrivateSubmissionReceipt:
        del submission
        self.calls += 1
        return self.receipt


def test_accepted_acknowledgement_maps_to_submitted_order_without_proving_execution() -> None:
    intent = _intent()
    submission = _submission(intent)
    factory = _Factory(submission)
    service = _Service(_receipt(submission, accepted=True))
    submitter = PrivateDryRunApprovedIntentSubmitter(service, factory)

    order = submitter.submit_approved_intent(intent, CONTEXT)

    assert order.order_id == "freqtrade-trade_id-77"
    assert order.execution_intent_id == str(intent.execution_intent_id)
    assert order.state == OrderState.SUBMITTED
    assert order.pair == "BTC/USDT"
    assert factory.calls == service.calls == 1


def test_ambiguous_receipt_cannot_be_reported_as_submitted_order() -> None:
    intent = _intent()
    submission = _submission(intent)
    submitter = PrivateDryRunApprovedIntentSubmitter(
        _Service(_receipt(submission, accepted=False)),
        _Factory(submission),
    )

    with pytest.raises(UnsupportedExecutionOperationError) as error:
        submitter.submit_approved_intent(intent, CONTEXT)
    assert error.value.reason_code == "ORDER_SUBMISSION_PENDING_RECONCILIATION"
