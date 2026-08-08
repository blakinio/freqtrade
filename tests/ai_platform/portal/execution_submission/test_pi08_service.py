from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import select

from ai_platform.portal.bot_operations.schema import AuthoritativeBotRuntimeState
from ai_platform.portal.contracts.bot_management.execution import (
    AcknowledgementStatus,
    ExecutionAttemptState,
    ExecutionBinding,
    ExecutionReasonCode,
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
from ai_platform.portal.execution.private_read import (
    OrderReadResult,
    PrivateOrderRecord,
    RuntimeReadFreshness,
    RuntimeReadKind,
    RuntimeReadReconciliationStatus,
    RuntimeReadStatus,
)
from ai_platform.portal.execution_submission.errors import (
    SubmissionIdempotencyConflictError,
    SubmissionPolicyError,
    SubmissionRuntimeRejectedError,
    SubmissionTransportAmbiguousError,
)
from ai_platform.portal.execution_submission.models import ExecutionSubmissionRow
from ai_platform.portal.execution_submission.schema import (
    PrivateDryRunSubmission,
    RuntimeDryRunEvidence,
    RuntimeSubmissionResponse,
)
from ai_platform.portal.execution_submission.service import PrivateDryRunSubmissionService
from ai_platform.portal.execution_submission.store import ExecutionSubmissionStore
from ai_platform.portal.execution_submission.transport import PrivateRuntimeTarget


NOW = datetime(2026, 7, 29, 6, 0, tzinfo=UTC)
CONTEXT = CorrelationContext(
    request_id=UUID("10000000-0000-0000-0000-000000000001"),
    correlation_id=UUID("20000000-0000-0000-0000-000000000002"),
    causation_id=UUID("30000000-0000-0000-0000-000000000003"),
)


class _Clock:
    def __init__(self) -> None:
        self.value = NOW

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs: int) -> None:
        self.value += timedelta(**kwargs)


class _Broker:
    def __init__(self, *, mismatched_exchange: bool = False) -> None:
        self.requests: list[CredentialLeaseRequest] = []
        self.last_lease: ResolvedCredentialLease | None = None
        self.mismatched_exchange = mismatched_exchange

    def resolve(self, request: CredentialLeaseRequest) -> ResolvedCredentialLease:
        self.requests.append(request)
        evidence = CredentialLeaseEvidence(
            lease_id="credlease_0123456789abcdef0123456789abcdef",
            tenant_id=request.tenant_id,
            connection_id=request.connection_id,
            credential_ref=request.credential_ref,
            exchange_id=("wrong-exchange" if self.mismatched_exchange else request.exchange_id),
            runtime_id=request.runtime_id,
            purpose=request.purpose,
            vault_version=3,
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
            rotated_at=NOW - timedelta(days=1),
            evidence_ref="vault-evidence-1",
        )
        material = CredentialMaterial.from_values(
            exchange_api_key="exchange-key-secret-value",
            exchange_api_secret="exchange-secret-value",
            exchange_passphrase="exchange-passphrase-value",
            runtime_api_username="runtime-user-secret-value",
            runtime_api_password="runtime-password-secret-value",
        )
        self.last_lease = ResolvedCredentialLease(evidence=evidence, _material=material)
        return self.last_lease


class _Resolver:
    def __init__(self, target: PrivateRuntimeTarget) -> None:
        self.target = target
        self.calls = 0

    def resolve(self, runtime_id: str) -> PrivateRuntimeTarget:
        self.calls += 1
        assert runtime_id == "runtime-1"
        return self.target


class _Transport:
    def __init__(self) -> None:
        self.verify_calls = 0
        self.submit_calls = 0
        self.ambiguous = False
        self.reject = False

    def verify_dry_run(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
    ) -> RuntimeDryRunEvidence:
        del lease
        self.verify_calls += 1
        return RuntimeDryRunEvidence(
            runtime_id=target.runtime_id,
            verified_at=NOW,
            config_digest="0" * 64,
        )

    def submit(
        self,
        target: PrivateRuntimeTarget,
        submission: PrivateDryRunSubmission,
        lease: ResolvedCredentialLease,
    ) -> RuntimeSubmissionResponse:
        del target, submission, lease
        self.submit_calls += 1
        if self.ambiguous:
            raise SubmissionTransportAmbiguousError("a" * 64)
        if self.reject:
            raise SubmissionRuntimeRejectedError()
        return RuntimeSubmissionResponse(
            runtime_request_ref="freqtrade-trade_id-77",
            response_digest="1" * 64,
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


def _submission(
    *,
    runtime_health: RuntimeHealthState = RuntimeHealthState.HEALTHY,
    freshness: RuntimeReadFreshness = RuntimeReadFreshness.CURRENT,
    kill_switch_active: bool = False,
    approved_until: datetime | None = None,
) -> PrivateDryRunSubmission:
    binding = ExecutionBinding(
        tenant_id="tenant-a",
        bot_id="bot-1",
        config_revision=7,
        runtime_id="runtime-1",
        runtime_revision=9,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
        idempotency_key="submit-intent-60000000",
        correlation=CONTEXT,
    )
    return PrivateDryRunSubmission(
        command_id="command-1",
        intent=_intent(),
        binding=binding,
        runtime=AuthoritativeBotRuntimeState(
            tenant_id="tenant-a",
            bot_id="bot-1",
            config_revision=7,
            runtime_generation_id="generation-1",
            runtime_id="runtime-1",
            runtime_revision=9,
            environment=Environment.TEST,
            freshness=freshness,
            kill_switch_active=kill_switch_active,
            observed_at=NOW,
        ),
        runtime_health=runtime_health,
        connection_id="connection-1",
        credential_ref="credref_okxDryRun01",
        exchange_id="okx",
        approved_until=approved_until or NOW + timedelta(minutes=1),
    )


def _service(tmp_path: Path, *, broker: _Broker | None = None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    ca_path = tmp_path / "runtime-ca.pem"
    ca_path.write_text("test-ca", encoding="utf-8")
    resolver = _Resolver(
        PrivateRuntimeTarget(
            runtime_id="runtime-1",
            endpoint="https://freqtrade.internal:8443",
            ca_certificate_path=ca_path,
        )
    )
    actual_broker = broker or _Broker()
    transport = _Transport()
    clock = _Clock()
    service = PrivateDryRunSubmissionService(
        ExecutionSubmissionStore(session_factory),
        actual_broker,
        resolver,
        transport,
        clock=clock,
    )
    return service, session_factory, actual_broker, resolver, transport, clock


def test_acknowledgement_is_persisted_and_duplicate_does_not_resubmit(tmp_path: Path) -> None:
    service, factory, broker, resolver, transport, _clock = _service(tmp_path)
    submission = _submission()

    first = service.submit(submission)
    second = service.submit(submission)

    assert first == second
    assert first.attempt.state == ExecutionAttemptState.ACKNOWLEDGED
    assert first.acknowledgement is not None
    assert first.acknowledgement.status == AcknowledgementStatus.ACCEPTED
    assert first.acknowledgement.execution_proven is False
    assert first.reconciliation.state == ReconciliationState.PENDING
    assert resolver.calls == transport.verify_calls == transport.submit_calls == 1
    assert broker.requests[0].exchange_id == "okx"
    assert broker.last_lease is not None and broker.last_lease.closed

    with factory() as session:
        row = session.scalar(select(ExecutionSubmissionRow))
        assert row is not None
        persisted = row.submission_json + row.receipt_json
    for forbidden in (
        "exchange-key-secret-value",
        "exchange-secret-value",
        "exchange-passphrase-value",
        "runtime-user-secret-value",
        "runtime-password-secret-value",
        "freqtrade.internal",
    ):
        assert forbidden not in persisted


def test_idempotency_conflict_does_not_call_transport_twice(tmp_path: Path) -> None:
    service, _factory, _broker, _resolver, transport, _clock = _service(tmp_path)
    submission = _submission()
    service.submit(submission)

    with pytest.raises(SubmissionIdempotencyConflictError):
        service.submit(submission.model_copy(update={"connection_id": "connection-2"}))
    assert transport.submit_calls == 1


@pytest.mark.parametrize(
    "submission,reason",
    [
        (_submission(runtime_health=RuntimeHealthState.DEGRADED), "RUNTIME_HEALTH_NOT_HEALTHY"),
        (_submission(freshness=RuntimeReadFreshness.STALE), "RUNTIME_UNAVAILABLE"),
        (_submission(kill_switch_active=True), "KILL_SWITCH_ACTIVE"),
    ],
)
def test_runtime_policy_gates_fail_before_reservation(
    tmp_path: Path,
    submission: PrivateDryRunSubmission,
    reason: str,
) -> None:
    service, factory, _broker, resolver, transport, _clock = _service(tmp_path)
    with pytest.raises(SubmissionPolicyError) as error:
        service.submit(submission)
    assert error.value.reason_code == reason
    assert resolver.calls == transport.submit_calls == 0
    with factory() as session:
        assert session.scalar(select(ExecutionSubmissionRow)) is None


def test_expired_approval_fails_before_reservation(tmp_path: Path) -> None:
    service, factory, _broker, resolver, transport, clock = _service(tmp_path)
    submission = _submission(approved_until=NOW + timedelta(seconds=1))
    clock.advance(seconds=2)
    with pytest.raises(SubmissionPolicyError) as error:
        service.submit(submission)
    assert error.value.reason_code == "APPROVED_INTENT_EXPIRED"
    assert resolver.calls == transport.submit_calls == 0
    with factory() as session:
        assert session.scalar(select(ExecutionSubmissionRow)) is None


def test_ambiguous_response_is_persisted_and_never_blindly_retried(tmp_path: Path) -> None:
    service, _factory, _broker, _resolver, transport, _clock = _service(tmp_path)
    transport.ambiguous = True
    submission = _submission()
    first = service.submit(submission)
    second = service.submit(submission)
    assert first == second
    assert first.attempt.state == ExecutionAttemptState.AMBIGUOUS
    assert first.ambiguity is not None
    assert first.runtime_config is not None
    assert first.reconciliation.state == ReconciliationState.PENDING
    assert transport.submit_calls == 1


def test_runtime_rejection_and_credential_scope_mismatch_fail_closed(tmp_path: Path) -> None:
    rejected_service, _factory, _broker, _resolver, rejected_transport, _clock = _service(
        tmp_path / "rejected"
    )
    rejected_transport.reject = True
    rejected = rejected_service.submit(_submission())
    assert rejected.attempt.state == ExecutionAttemptState.REJECTED
    assert rejected.acknowledgement is not None
    assert rejected.acknowledgement.reason_codes == (ExecutionReasonCode.EXECUTION_REJECTED,)

    mismatch_service, _factory, _broker, _resolver, mismatch_transport, _clock = _service(
        tmp_path / "mismatch",
        broker=_Broker(mismatched_exchange=True),
    )
    mismatched = mismatch_service.submit(_submission())
    assert mismatched.attempt.state == ExecutionAttemptState.REJECTED
    assert mismatched.acknowledgement is not None
    assert mismatched.acknowledgement.reason_codes == (ExecutionReasonCode.RUNTIME_UNAVAILABLE,)
    assert mismatch_transport.submit_calls == 0


def _orders(
    submission: PrivateDryRunSubmission,
    *,
    matching: bool = True,
    duplicate: bool = False,
    tenant_id: str = "tenant-a",
) -> OrderReadResult:
    intent_id = str(submission.intent.execution_intent_id) if matching else "other-intent"
    records: tuple[PrivateOrderRecord, ...] = (
        PrivateOrderRecord(
            source_order_id="order-1",
            source_trade_id="trade-77",
            execution_intent_id=intent_id,
            pair="BTC/USDT",
            side=TradeSide.BUY,
            state=OrderState.OPEN,
            amount=Decimal("25"),
            created_at=NOW + timedelta(seconds=2),
            source_updated_at=NOW + timedelta(seconds=3),
        ),
    )
    if duplicate:
        records += (records[0].model_copy(update={"source_order_id": "order-2"}),)
    return OrderReadResult(
        status=RuntimeReadStatus(
            tenant_id=tenant_id,
            bot_id="bot-1",
            source_runtime_id="runtime-1",
            kind=RuntimeReadKind.ORDERS,
            source_observed_at=NOW + timedelta(seconds=3),
            observed_at=NOW + timedelta(seconds=4),
            last_reconciled_at=NOW + timedelta(seconds=4),
            freshness=RuntimeReadFreshness.CURRENT,
            reconciliation_status=RuntimeReadReconciliationStatus.SYNCED,
            complete=True,
            record_count=len(records),
        ),
        records=records,
    )


def test_reconciliation_requires_exact_authoritative_order(tmp_path: Path) -> None:
    service, _factory, _broker, _resolver, _transport, clock = _service(tmp_path)
    submission = _submission()
    receipt = service.submit(submission)
    clock.advance(seconds=5)

    pending = service.reconcile_orders(
        "tenant-a", receipt.attempt.attempt_id, _orders(submission, matching=False)
    )
    assert pending.reconciliation.state == ReconciliationState.PENDING
    assert pending.reconciliation.reason_codes == (ExecutionReasonCode.EVIDENCE_INCOMPLETE,)

    succeeded = service.reconcile_orders(
        "tenant-a", receipt.attempt.attempt_id, _orders(submission)
    )
    assert succeeded.reconciliation.state == ReconciliationState.SUCCEEDED
    assert succeeded.reconciliation.evidence_refs[0].authoritative is True
    assert (
        service.reconcile_orders(
            "tenant-a", receipt.attempt.attempt_id, _orders(submission, duplicate=True)
        )
        == succeeded
    )


def test_reconciliation_conflict_timeout_and_tenant_mismatch(tmp_path: Path) -> None:
    conflict_service, _factory, _broker, _resolver, _transport, clock = _service(
        tmp_path / "conflict"
    )
    submission = _submission()
    receipt = conflict_service.submit(submission)
    clock.advance(seconds=5)
    conflict = conflict_service.reconcile_orders(
        "tenant-a", receipt.attempt.attempt_id, _orders(submission, duplicate=True)
    )
    assert conflict.reconciliation.state == ReconciliationState.CONFLICT

    timeout_service, _factory, _broker, _resolver, _transport, clock = _service(
        tmp_path / "timeout"
    )
    receipt = timeout_service.submit(submission)
    clock.advance(seconds=5)
    timed_out = timeout_service.reconcile_orders(
        "tenant-a",
        receipt.attempt.attempt_id,
        _orders(submission, matching=False),
        timed_out=True,
    )
    assert timed_out.reconciliation.state == ReconciliationState.FAILED
    assert timed_out.reconciliation.reason_codes == (ExecutionReasonCode.RECONCILIATION_TIMEOUT,)

    isolated_service, _factory, _broker, _resolver, _transport, _clock = _service(
        tmp_path / "isolation"
    )
    receipt = isolated_service.submit(submission)
    with pytest.raises(SubmissionPolicyError, match="EVIDENCE_MISMATCH"):
        isolated_service.reconcile_orders(
            "tenant-a",
            receipt.attempt.attempt_id,
            _orders(submission, tenant_id="tenant-b"),
        )
