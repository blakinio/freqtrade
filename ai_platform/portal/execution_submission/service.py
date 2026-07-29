from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from ai_platform.portal.contracts.bot_management.execution import (
    AcknowledgementStatus,
    AmbiguousExecutionResponse,
    ExecutionAcknowledgement,
    ExecutionAttempt,
    ExecutionAttemptState,
    ExecutionBinding,
    ExecutionEvidenceRef,
    ExecutionEvidenceSource,
    ExecutionEvidenceType,
    ExecutionReasonCode,
    ReconciliationRecord,
    ReconciliationState,
)
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.credentials.errors import CredentialBrokerError
from ai_platform.portal.credentials.material import ResolvedCredentialLease
from ai_platform.portal.credentials.schema import CredentialLeaseRequest, CredentialPurpose
from ai_platform.portal.execution.private_read import (
    OrderReadResult,
    RuntimeReadFreshness,
    RuntimeReadReconciliationStatus,
)
from ai_platform.portal.execution_submission.errors import (
    ExecutionSubmissionError,
    SubmissionPolicyError,
    SubmissionRuntimeRejectedError,
    SubmissionTransportAmbiguousError,
)
from ai_platform.portal.execution_submission.schema import (
    PrivateDryRunSubmission,
    PrivateSubmissionReceipt,
    RuntimeDryRunEvidence,
)
from ai_platform.portal.execution_submission.store import ExecutionSubmissionStore
from ai_platform.portal.execution_submission.transport import (
    PrivateRuntimeTarget,
    PrivateSubmissionTransport,
)


Clock = Callable[[], datetime]


class CredentialLeaseBroker(Protocol):
    def resolve(self, request: CredentialLeaseRequest) -> ResolvedCredentialLease: ...


class RuntimeTargetResolver(Protocol):
    def resolve(self, runtime_id: str) -> PrivateRuntimeTarget: ...


class PrivateDryRunSubmissionService:
    def __init__(
        self,
        store: ExecutionSubmissionStore,
        broker: CredentialLeaseBroker,
        target_resolver: RuntimeTargetResolver,
        transport: PrivateSubmissionTransport,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._store = store
        self._broker = broker
        self._target_resolver = target_resolver
        self._transport = transport
        self._clock = clock or (lambda: datetime.now(UTC))

    def submit(self, submission: PrivateDryRunSubmission) -> PrivateSubmissionReceipt:
        now = self._clock()
        self._require_submission_policy(submission, now)
        initial = self._initial_receipt(submission, now)
        stored, created = self._store.reserve(submission, initial)
        if not created:
            return stored.receipt

        try:
            target = self._target_resolver.resolve(submission.binding.runtime_id)
        except ExecutionSubmissionError:
            return self._reject(
                submission,
                initial,
                ExecutionReasonCode.RUNTIME_UNAVAILABLE,
                self._clock(),
            )
        if target.runtime_id != submission.binding.runtime_id:
            return self._reject(
                submission,
                initial,
                ExecutionReasonCode.RUNTIME_REVISION_MISMATCH,
                self._clock(),
            )

        credential_request = CredentialLeaseRequest(
            tenant_id=submission.binding.tenant_id,
            connection_id=submission.connection_id,
            credential_ref=submission.credential_ref,
            exchange_id=submission.exchange_id,
            runtime_id=submission.binding.runtime_id,
            environment=submission.binding.environment,
            execution_mode=submission.binding.execution_mode,
            purpose=CredentialPurpose.RUNTIME_API,
            requested_at=now,
            correlation=submission.binding.correlation,
        )
        runtime_config: RuntimeDryRunEvidence | None = None
        try:
            with self._broker.resolve(credential_request) as lease:
                self._require_lease(submission, lease, self._clock())
                runtime_config = self._transport.verify_dry_run(target, lease)
                if runtime_config.runtime_id != submission.binding.runtime_id:
                    raise SubmissionPolicyError("RUNTIME_CONFIG_SCOPE_MISMATCH")
                response = self._transport.submit(target, submission, lease)
        except SubmissionTransportAmbiguousError as exc:
            return self._ambiguous(
                submission,
                initial,
                exc,
                self._clock(),
                runtime_config=runtime_config,
            )
        except SubmissionRuntimeRejectedError:
            return self._reject(
                submission,
                initial,
                ExecutionReasonCode.EXECUTION_REJECTED,
                self._clock(),
            )
        except (CredentialBrokerError, ExecutionSubmissionError):
            return self._reject(
                submission,
                initial,
                ExecutionReasonCode.RUNTIME_UNAVAILABLE,
                self._clock(),
            )

        received_at = self._clock()
        acknowledgement = ExecutionAcknowledgement(
            acknowledgement_id=f"ack_{initial.attempt.attempt_id}",
            attempt_id=initial.attempt.attempt_id,
            binding=submission.binding,
            status=AcknowledgementStatus.ACCEPTED,
            reason_codes=(ExecutionReasonCode.ACKNOWLEDGED_NOT_EXECUTED,),
            runtime_request_ref=response.runtime_request_ref,
            received_at=received_at,
        )
        attempt = initial.attempt.model_copy(
            update={
                "state": ExecutionAttemptState.ACKNOWLEDGED,
                "completed_at": received_at,
                "acknowledgement_ref": acknowledgement.acknowledgement_id,
            }
        )
        receipt = PrivateSubmissionReceipt(
            attempt=attempt,
            acknowledgement=acknowledgement,
            reconciliation=initial.reconciliation,
            runtime_config=runtime_config,
        )
        return self._store.update_receipt(
            submission.binding.tenant_id,
            attempt.attempt_id,
            receipt,
        ).receipt

    def get_receipt(self, tenant_id: str, attempt_id: str) -> PrivateSubmissionReceipt:
        return self._store.get_by_attempt(tenant_id, attempt_id).receipt

    def reconcile_orders(
        self,
        tenant_id: str,
        attempt_id: str,
        orders: OrderReadResult,
        *,
        timed_out: bool = False,
    ) -> PrivateSubmissionReceipt:
        stored = self._store.get_by_attempt(tenant_id, attempt_id)
        receipt = stored.receipt
        submission = stored.submission
        now = self._clock()
        self._require_read_binding(submission.binding, orders)

        if receipt.reconciliation.state != ReconciliationState.PENDING:
            return receipt

        exact_orders = tuple(
            order
            for order in orders.records
            if order.execution_intent_id == str(submission.intent.execution_intent_id)
            and order.source_updated_at >= receipt.attempt.started_at
        )
        current_complete = (
            orders.status.freshness == RuntimeReadFreshness.CURRENT
            and orders.status.reconciliation_status == RuntimeReadReconciliationStatus.SYNCED
            and orders.status.complete
        )
        if len(exact_orders) == 1 and current_complete:
            order = exact_orders[0]
            evidence = ExecutionEvidenceRef(
                evidence_id=f"order-{order.source_order_id}",
                evidence_type=ExecutionEvidenceType.ORDER,
                source=ExecutionEvidenceSource.RUNTIME_DATABASE,
                authoritative=True,
                tenant_id=submission.binding.tenant_id,
                bot_id=submission.binding.bot_id,
                config_revision=submission.binding.config_revision,
                runtime_id=submission.binding.runtime_id,
                runtime_revision=submission.binding.runtime_revision,
                observed_at=order.source_updated_at,
                sha256=hashlib.sha256(order.canonical_json().encode()).hexdigest(),
            )
            reconciliation = ReconciliationRecord(
                reconciliation_id=receipt.reconciliation.reconciliation_id,
                attempt_id=attempt_id,
                command_id=submission.command_id,
                binding=submission.binding,
                state=ReconciliationState.SUCCEEDED,
                evidence_refs=(evidence,),
                started_at=receipt.reconciliation.started_at,
                reconciled_at=now,
            )
        elif len(exact_orders) > 1:
            reconciliation = self._terminal_reconciliation(
                submission,
                receipt,
                ReconciliationState.CONFLICT,
                ExecutionReasonCode.EVIDENCE_MISMATCH,
                now,
            )
        elif timed_out:
            reconciliation = self._terminal_reconciliation(
                submission,
                receipt,
                ReconciliationState.FAILED,
                ExecutionReasonCode.RECONCILIATION_TIMEOUT,
                now,
            )
        else:
            reconciliation = receipt.reconciliation.model_copy(
                update={
                    "reason_codes": (ExecutionReasonCode.EVIDENCE_INCOMPLETE,),
                }
            )
        updated = receipt.model_copy(update={"reconciliation": reconciliation})
        return self._store.update_receipt(tenant_id, attempt_id, updated).receipt

    @staticmethod
    def _require_submission_policy(
        submission: PrivateDryRunSubmission,
        now: datetime,
    ) -> None:
        if submission.approved_until <= now:
            raise SubmissionPolicyError("APPROVED_INTENT_EXPIRED")
        if submission.runtime.observed_at > now:
            raise SubmissionPolicyError("RUNTIME_EVIDENCE_FROM_FUTURE")
        if submission.runtime.freshness != RuntimeReadFreshness.CURRENT:
            raise SubmissionPolicyError("RUNTIME_UNAVAILABLE")
        if submission.runtime_health != RuntimeHealthState.HEALTHY:
            raise SubmissionPolicyError("RUNTIME_HEALTH_NOT_HEALTHY")
        if submission.runtime.kill_switch_active:
            raise SubmissionPolicyError("KILL_SWITCH_ACTIVE")

    @staticmethod
    def _require_lease(
        submission: PrivateDryRunSubmission,
        lease: ResolvedCredentialLease,
        now: datetime,
    ) -> None:
        evidence = lease.evidence
        if (
            evidence.tenant_id != submission.binding.tenant_id
            or evidence.connection_id != submission.connection_id
            or evidence.credential_ref != submission.credential_ref
            or evidence.exchange_id != submission.exchange_id
            or evidence.runtime_id != submission.binding.runtime_id
        ):
            raise SubmissionPolicyError("CREDENTIAL_LEASE_SCOPE_MISMATCH")
        if evidence.expires_at <= now:
            raise SubmissionPolicyError("CREDENTIAL_LEASE_EXPIRED")

    @staticmethod
    def _require_read_binding(
        binding: ExecutionBinding,
        orders: OrderReadResult,
    ) -> None:
        status = orders.status
        if (
            status.tenant_id != binding.tenant_id
            or status.bot_id != binding.bot_id
            or status.source_runtime_id != binding.runtime_id
        ):
            raise SubmissionPolicyError("EVIDENCE_MISMATCH")

    @staticmethod
    def _initial_receipt(
        submission: PrivateDryRunSubmission,
        now: datetime,
    ) -> PrivateSubmissionReceipt:
        attempt_id = _attempt_id(submission)
        attempt = ExecutionAttempt(
            attempt_id=attempt_id,
            command_id=submission.command_id,
            binding=submission.binding,
            state=ExecutionAttemptState.CREATED,
            attempt_number=1,
            started_at=now,
        )
        reconciliation = ReconciliationRecord(
            reconciliation_id=f"recon_{attempt_id}",
            attempt_id=attempt_id,
            command_id=submission.command_id,
            binding=submission.binding,
            state=ReconciliationState.PENDING,
            started_at=now,
        )
        return PrivateSubmissionReceipt(
            attempt=attempt,
            reconciliation=reconciliation,
        )

    def _reject(
        self,
        submission: PrivateDryRunSubmission,
        receipt: PrivateSubmissionReceipt,
        reason: ExecutionReasonCode,
        now: datetime,
    ) -> PrivateSubmissionReceipt:
        acknowledgement = ExecutionAcknowledgement(
            acknowledgement_id=f"ack_{receipt.attempt.attempt_id}",
            attempt_id=receipt.attempt.attempt_id,
            binding=submission.binding,
            status=AcknowledgementStatus.REJECTED,
            reason_codes=(reason,),
            runtime_request_ref=f"not-submitted-{receipt.attempt.attempt_id}",
            received_at=now,
        )
        attempt = receipt.attempt.model_copy(
            update={
                "state": ExecutionAttemptState.REJECTED,
                "completed_at": now,
                "acknowledgement_ref": acknowledgement.acknowledgement_id,
            }
        )
        reconciliation = self._terminal_reconciliation(
            submission,
            receipt,
            ReconciliationState.FAILED,
            reason,
            now,
        )
        updated = receipt.model_copy(
            update={
                "attempt": attempt,
                "acknowledgement": acknowledgement,
                "reconciliation": reconciliation,
            }
        )
        return self._store.update_receipt(
            submission.binding.tenant_id,
            attempt.attempt_id,
            updated,
        ).receipt

    def _ambiguous(
        self,
        submission: PrivateDryRunSubmission,
        receipt: PrivateSubmissionReceipt,
        error: SubmissionTransportAmbiguousError,
        now: datetime,
        *,
        runtime_config: RuntimeDryRunEvidence | None,
    ) -> PrivateSubmissionReceipt:
        ambiguity = AmbiguousExecutionResponse(
            ambiguity_id=f"ambiguity_{receipt.attempt.attempt_id}",
            attempt_id=receipt.attempt.attempt_id,
            binding=submission.binding,
            reason_code=ExecutionReasonCode.TRANSPORT_AMBIGUOUS,
            response_digest=error.response_digest,
            observed_at=now,
        )
        attempt = receipt.attempt.model_copy(
            update={
                "state": ExecutionAttemptState.AMBIGUOUS,
                "completed_at": now,
            }
        )
        updated = receipt.model_copy(
            update={
                "attempt": attempt,
                "ambiguity": ambiguity,
                "runtime_config": runtime_config,
                "reconciliation": receipt.reconciliation.model_copy(
                    update={
                        "reason_codes": (ExecutionReasonCode.TRANSPORT_AMBIGUOUS,),
                    }
                ),
            }
        )
        return self._store.update_receipt(
            submission.binding.tenant_id,
            attempt.attempt_id,
            updated,
        ).receipt

    @staticmethod
    def _terminal_reconciliation(
        submission: PrivateDryRunSubmission,
        receipt: PrivateSubmissionReceipt,
        state: ReconciliationState,
        reason: ExecutionReasonCode,
        now: datetime,
    ) -> ReconciliationRecord:
        return ReconciliationRecord(
            reconciliation_id=receipt.reconciliation.reconciliation_id,
            attempt_id=receipt.attempt.attempt_id,
            command_id=submission.command_id,
            binding=submission.binding,
            state=state,
            reason_codes=(reason,),
            started_at=receipt.reconciliation.started_at,
            reconciled_at=now,
        )


def _attempt_id(submission: PrivateDryRunSubmission) -> str:
    identity = "\0".join(
        (
            submission.binding.tenant_id,
            submission.binding.idempotency_key,
            submission.command_id,
            str(submission.intent.execution_intent_id),
        )
    )
    return f"exec_{hashlib.sha256(identity.encode()).hexdigest()[:32]}"
