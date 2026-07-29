from __future__ import annotations

from typing import Protocol

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.execution import OrderRecord, OrderState
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent
from ai_platform.portal.execution.errors import UnsupportedExecutionOperationError
from ai_platform.portal.execution_submission.schema import PrivateDryRunSubmission
from ai_platform.portal.execution_submission.service import PrivateDryRunSubmissionService


class PrivateSubmissionFactory(Protocol):
    def build(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> PrivateDryRunSubmission: ...


class PrivateDryRunApprovedIntentSubmitter:
    """Adapter for the existing risk-terminal submission protocol.

    The returned ``OrderRecord`` represents only a private-runtime acknowledgement.
    Authoritative execution remains pending until PI-01 reconciliation succeeds.
    """

    def __init__(
        self,
        service: PrivateDryRunSubmissionService,
        submission_factory: PrivateSubmissionFactory,
    ) -> None:
        self._service = service
        self._submission_factory = submission_factory

    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord:
        submission = self._submission_factory.build(intent, context)
        receipt = self._service.submit(submission)
        acknowledgement = receipt.acknowledgement
        if acknowledgement is None:
            raise UnsupportedExecutionOperationError("ORDER_SUBMISSION_PENDING_RECONCILIATION")
        if not acknowledgement.status.value == "ACCEPTED":
            reason = (
                acknowledgement.reason_codes[0].value
                if acknowledgement.reason_codes
                else "ORDER_SUBMISSION_REJECTED"
            )
            raise UnsupportedExecutionOperationError(reason)
        return OrderRecord(
            tenant_id=submission.binding.tenant_id,
            bot_id=submission.binding.bot_id,
            order_id=acknowledgement.runtime_request_ref,
            execution_intent_id=str(intent.execution_intent_id),
            pair=intent.trade_intent.pair,
            side=intent.trade_intent.side,
            state=OrderState.SUBMITTED,
            amount=intent.trade_intent.amount,
            created_at=acknowledgement.received_at,
        )
