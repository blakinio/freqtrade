from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from ai_platform.portal.bot_operations.activation_errors import (
    CommandActivationAmbiguousError,
    CommandActivationError,
    CommandActivationRejectedError,
)
from ai_platform.portal.bot_operations.activation_schema import (
    CommandActivationResult,
    CommandActivationState,
    OrderCommandActivationRequest,
    PolicyEntryActivationRequest,
    PositionCommandActivationRequest,
    RuntimeCommandAcknowledgement,
    RuntimeOrderEvidence,
    RuntimePositionEvidence,
)
from ai_platform.portal.bot_operations.activation_transport import (
    PrivateRuntimeCommandTransport,
)
from ai_platform.portal.bot_operations.schema import AuthoritativeBotRuntimeState
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.commands import (
    CommandOutcome,
    CommandOutcomeStatus,
    OrderAction,
    PositionAction,
)
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.credentials.material import ResolvedCredentialLease
from ai_platform.portal.credentials.schema import CredentialLeaseRequest, CredentialPurpose
from ai_platform.portal.execution.private_read import RuntimeReadFreshness
from ai_platform.portal.execution_submission.schema import PrivateSubmissionReceipt
from ai_platform.portal.execution_submission.service import PrivateDryRunSubmissionService
from ai_platform.portal.execution_submission.transport import (
    PrivateRuntimeTarget,
    PrivateSubmissionTransport,
)


class CredentialLeaseBroker(Protocol):
    def resolve(self, request: CredentialLeaseRequest) -> ResolvedCredentialLease: ...


class RuntimeTargetResolver(Protocol):
    def resolve(self, runtime_id: str) -> PrivateRuntimeTarget: ...


class BotCommandActivationService:
    def __init__(
        self,
        command_service: BotCommandService,
        broker: CredentialLeaseBroker,
        target_resolver: RuntimeTargetResolver,
        dry_run_verifier: PrivateSubmissionTransport,
        command_transport: PrivateRuntimeCommandTransport,
        replacement_service: PrivateDryRunSubmissionService,
    ) -> None:
        self._commands = command_service
        self._broker = broker
        self._target_resolver = target_resolver
        self._dry_run_verifier = dry_run_verifier
        self._transport = command_transport
        self._replacement_service = replacement_service

    def activate_position(
        self,
        request: PositionCommandActivationRequest,
    ) -> CommandActivationResult:
        runtime = _runtime_for_health(request.runtime, request.runtime_health)
        outcome = self._commands.submit_position(request.context, request.command, runtime)
        replay = _existing_result(outcome)
        if replay is not None:
            return replay
        if outcome.status != CommandOutcomeStatus.ACCEPTED:
            return CommandActivationResult(
                outcome=outcome,
                activation_state=CommandActivationState.NOT_SUBMITTED,
                reason_code=(outcome.reason_codes[0].value if outcome.reason_codes else None),
            )

        attempt_ref = _attempt_ref(request.command.command_id, request.command.canonical_json())
        pending = self._commands.mark_pending_reconciliation(
            request.context,
            request.command.command_id,
            attempt_ref,
        )
        try:
            acknowledgement = self._execute_position(request)
        except CommandActivationAmbiguousError as exc:
            return CommandActivationResult(
                outcome=pending,
                activation_state=CommandActivationState.AMBIGUOUS,
                execution_attempt_ref=attempt_ref,
                reason_code=exc.reason_code,
            )
        except CommandActivationRejectedError as exc:
            return CommandActivationResult(
                outcome=pending,
                activation_state=CommandActivationState.REJECTED,
                execution_attempt_ref=attempt_ref,
                reason_code=exc.reason_code,
            )
        except CommandActivationError as exc:
            return CommandActivationResult(
                outcome=pending,
                activation_state=CommandActivationState.AMBIGUOUS,
                execution_attempt_ref=attempt_ref,
                reason_code=exc.reason_code,
            )
        return CommandActivationResult(
            outcome=pending,
            activation_state=CommandActivationState.ACKNOWLEDGED,
            execution_attempt_ref=attempt_ref,
            acknowledgement=acknowledgement,
        )

    def activate_order(
        self,
        request: OrderCommandActivationRequest,
    ) -> CommandActivationResult:
        runtime = _runtime_for_health(request.runtime, request.runtime_health)
        outcome = self._commands.submit_order(request.context, request.command, runtime)
        replay = _existing_result(outcome)
        if replay is not None:
            return replay
        if outcome.status != CommandOutcomeStatus.ACCEPTED:
            return CommandActivationResult(
                outcome=outcome,
                activation_state=CommandActivationState.NOT_SUBMITTED,
                reason_code=(outcome.reason_codes[0].value if outcome.reason_codes else None),
            )

        attempt_ref = _attempt_ref(request.command.command_id, request.command.canonical_json())
        pending = self._commands.mark_pending_reconciliation(
            request.context,
            request.command.command_id,
            attempt_ref,
        )
        try:
            acknowledgement = self._execute_order(request)
        except CommandActivationAmbiguousError as exc:
            return CommandActivationResult(
                outcome=pending,
                activation_state=CommandActivationState.AMBIGUOUS,
                execution_attempt_ref=attempt_ref,
                reason_code=exc.reason_code,
            )
        except CommandActivationRejectedError as exc:
            return CommandActivationResult(
                outcome=pending,
                activation_state=CommandActivationState.REJECTED,
                execution_attempt_ref=attempt_ref,
                reason_code=exc.reason_code,
            )
        except CommandActivationError as exc:
            return CommandActivationResult(
                outcome=pending,
                activation_state=CommandActivationState.AMBIGUOUS,
                execution_attempt_ref=attempt_ref,
                reason_code=exc.reason_code,
            )
        return CommandActivationResult(
            outcome=pending,
            activation_state=CommandActivationState.ACKNOWLEDGED,
            execution_attempt_ref=attempt_ref,
            acknowledgement=acknowledgement,
        )

    def activate_policy_entry(
        self,
        request: PolicyEntryActivationRequest,
    ) -> PrivateSubmissionReceipt:
        """DCA and grid entries reuse the single risk-approved PI-08 path."""
        return self._replacement_service.submit(request.submission)

    def _execute_position(
        self,
        request: PositionCommandActivationRequest,
    ) -> RuntimeCommandAcknowledgement:
        target = self._target_resolver.resolve(request.runtime.runtime_id)
        _require_target(request.runtime.runtime_id, target)
        lease_request = _lease_request(
            request.runtime,
            request.connection_id,
            request.credential_ref,
            request.exchange_id,
            request.command.submitted_at,
            request.command.correlation,
        )
        with self._broker.resolve(lease_request) as lease:
            self._dry_run_verifier.verify_dry_run(target, lease)
            action = request.command.action
            if action == PositionAction.CLOSE_ALL:
                return self._transport.force_exit(target, lease, trade_id="all")
            position = _position(request)
            amount = _partial_amount(request, position)
            return self._transport.force_exit(
                target,
                lease,
                trade_id=position.source_trade_id,
                amount=amount,
            )

    def _execute_order(
        self,
        request: OrderCommandActivationRequest,
    ) -> RuntimeCommandAcknowledgement:
        target = self._target_resolver.resolve(request.runtime.runtime_id)
        _require_target(request.runtime.runtime_id, target)
        lease_request = _lease_request(
            request.runtime,
            request.connection_id,
            request.credential_ref,
            request.exchange_id,
            request.command.submitted_at,
            request.command.correlation,
        )
        with self._broker.resolve(lease_request) as lease:
            self._dry_run_verifier.verify_dry_run(target, lease)
            action = request.command.action
            if action == OrderAction.CANCEL_ALL_ORDERS:
                acknowledgements = [
                    self._transport.cancel_open_order(
                        target,
                        lease,
                        trade_id=trade_id,
                    )
                    for trade_id in sorted({item.source_trade_id for item in request.orders})
                ]
                return _combined_acknowledgement(
                    request.command.command_id,
                    acknowledgements,
                )
            order = _order(request)
            cancelled = self._transport.cancel_open_order(
                target,
                lease,
                trade_id=order.source_trade_id,
            )

        if request.command.action != OrderAction.REPLACE_ORDER:
            return cancelled
        replacement = request.replacement_submission
        if replacement is None:
            raise CommandActivationRejectedError()
        receipt = self._replacement_service.submit(replacement)
        if receipt.ambiguity is not None:
            raise CommandActivationAmbiguousError(receipt.ambiguity.response_digest)
        acknowledgement = receipt.acknowledgement
        if acknowledgement is None or acknowledgement.status.value != "ACCEPTED":
            raise CommandActivationRejectedError()
        digest = hashlib.sha256(
            f"{cancelled.response_digest}\0{acknowledgement.runtime_request_ref}".encode()
        ).hexdigest()
        return RuntimeCommandAcknowledgement(
            runtime_request_ref=(
                f"replace-{request.command.command_id}-{acknowledgement.runtime_request_ref}"
            ),
            response_digest=digest,
            acknowledged_at=acknowledgement.received_at,
        )


def _runtime_for_health(
    runtime: AuthoritativeBotRuntimeState,
    health: RuntimeHealthState,
) -> AuthoritativeBotRuntimeState:
    if health == RuntimeHealthState.HEALTHY:
        return runtime
    return runtime.model_copy(update={"freshness": RuntimeReadFreshness.SOURCE_UNAVAILABLE})


def _existing_result(outcome: CommandOutcome) -> CommandActivationResult | None:
    if outcome.status != CommandOutcomeStatus.PENDING_RECONCILIATION:
        return None
    return CommandActivationResult(
        outcome=outcome,
        activation_state=CommandActivationState.REPLAY_PENDING,
        execution_attempt_ref=outcome.execution_attempt_ref,
        reason_code="COMMAND_ALREADY_PENDING_RECONCILIATION",
    )


def _attempt_ref(command_id: str, command_json: str) -> str:
    digest = hashlib.sha256(f"{command_id}\0{command_json}".encode()).hexdigest()[:32]
    return f"cmdexec_{digest}"


def _lease_request(
    runtime: AuthoritativeBotRuntimeState,
    connection_id: str,
    credential_ref: str,
    exchange_id: str,
    requested_at: datetime,
    correlation: object,
) -> CredentialLeaseRequest:
    return CredentialLeaseRequest(
        tenant_id=runtime.tenant_id,
        connection_id=connection_id,
        credential_ref=credential_ref,
        exchange_id=exchange_id,
        runtime_id=runtime.runtime_id,
        environment=runtime.environment,
        execution_mode="dry_run",
        purpose=CredentialPurpose.RUNTIME_API,
        requested_at=requested_at,
        correlation=correlation,
    )


def _require_target(runtime_id: str, target: PrivateRuntimeTarget) -> None:
    if target.runtime_id != runtime_id:
        raise CommandActivationAmbiguousError()


def _position(request: PositionCommandActivationRequest) -> RuntimePositionEvidence:
    for position in request.positions:
        if (
            position.position_id == request.command.position_id
            and position.position_revision == request.command.position_revision
        ):
            return position
    raise CommandActivationRejectedError()


def _order(request: OrderCommandActivationRequest) -> RuntimeOrderEvidence:
    for order in request.orders:
        if (
            order.order_id == request.command.order_id
            and order.order_revision == request.command.order_revision
        ):
            return order
    raise CommandActivationRejectedError()


def _partial_amount(
    request: PositionCommandActivationRequest,
    position: RuntimePositionEvidence,
) -> str | None:
    if request.command.action != PositionAction.PARTIAL_CLOSE:
        return None
    quantity = request.command.close_quantity
    if quantity is None:
        fraction = request.command.close_fraction
        if fraction is None:
            raise CommandActivationRejectedError()
        quantity = position.amount * Decimal(fraction)
    if quantity <= 0 or quantity >= position.amount:
        raise CommandActivationRejectedError()
    return format(quantity, "f")


def _combined_acknowledgement(
    command_id: str,
    acknowledgements: list[RuntimeCommandAcknowledgement],
) -> RuntimeCommandAcknowledgement:
    if not acknowledgements:
        digest = hashlib.sha256(f"{command_id}\0no-open-orders".encode()).hexdigest()
        return RuntimeCommandAcknowledgement(
            runtime_request_ref=f"freqtrade-cancel-all-noop-{command_id}",
            response_digest=digest,
            acknowledged_at=datetime.now(UTC),
        )
    joined = "\0".join(item.response_digest for item in acknowledgements)
    digest = hashlib.sha256(joined.encode()).hexdigest()
    return RuntimeCommandAcknowledgement(
        runtime_request_ref=f"freqtrade-cancel-all-{command_id}-{digest[:16]}",
        response_digest=digest,
        acknowledged_at=max(item.acknowledged_at for item in acknowledgements),
    )
