from __future__ import annotations

from datetime import timedelta

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionRevocationStatus,
    ConnectionVerificationStatus,
    CredentialRotationStatus,
    ExchangeConnectionMetadata,
    ExchangeConnectionVerificationRequest,
    ExchangeConnectionVerificationResult,
    VerificationReasonCode,
)
from ai_platform.portal.contracts.common import CorrelationContext, UtcDateTime
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor
from ai_platform.portal.exchange_connections.credential_interface import (
    CredentialReferenceInspection,
    CredentialReferenceState,
    CredentialReferenceStatusPort,
)
from ai_platform.portal.exchange_connections.repository import (
    InMemoryExchangeConnectionRepository,
)
from ai_platform.portal.exchange_connections.schema import (
    ConnectionAvailabilityStatus,
    ConnectionProductStatus,
    ExchangeCapabilityProductProfile,
    ExchangeConnectionProduct,
    ExchangeConnectionState,
    TradingPermissionStatus,
    VerificationProbeResult,
    WithdrawalPermissionStatus,
)
from ai_platform.portal.exchange_connections.verification import (
    ExchangeConnectionVerificationStateMachine,
    VerificationStateError,
)


class ExchangeConnectionValidationError(ValueError):
    pass


class ExchangeConnectionService:
    def __init__(
        self,
        repository: InMemoryExchangeConnectionRepository,
        *,
        credential_status_port: CredentialReferenceStatusPort | None = None,
    ) -> None:
        self._repository = repository
        self._credential_status_port = credential_status_port

    def register_capability_profile(self, profile: ExchangeCapabilityProductProfile) -> None:
        self._repository.add_capability_profile(profile)

    def create_connection(self, metadata: ExchangeConnectionMetadata) -> ExchangeConnectionProduct:
        profile = self._repository.get_capability_profile(metadata.exchange_profile_ref)
        if metadata.exchange_id != profile.capability.exchange_id:
            raise ExchangeConnectionValidationError("connection exchange does not match profile")
        if not set(metadata.enabled_market_types).issubset(set(profile.capability.market_types)):
            raise ExchangeConnectionValidationError(
                "enabled market types must be supported by capability profile"
            )
        if metadata.subaccount_label is not None and not profile.capability.supports_subaccounts:
            raise ExchangeConnectionValidationError(
                "subaccount metadata requires subaccount capability"
            )

        state = self._initial_state(metadata)
        self._repository.add_connection(metadata, state)
        return ExchangeConnectionProduct(
            metadata=metadata,
            capability_profile=profile,
            state=state,
        )

    def _initial_state(self, metadata: ExchangeConnectionMetadata) -> ExchangeConnectionState:
        product_status = ConnectionProductStatus.UNVERIFIED
        if metadata.revocation_status == ConnectionRevocationStatus.REVOKED:
            product_status = ConnectionProductStatus.REVOKED
        elif metadata.rotation_status in {
            CredentialRotationStatus.ROTATION_REQUIRED,
            CredentialRotationStatus.ROTATION_PENDING,
        }:
            product_status = ConnectionProductStatus.ROTATION_REQUIRED
        elif metadata.verification_status == ConnectionVerificationStatus.PENDING:
            product_status = ConnectionProductStatus.VERIFYING
        elif metadata.verification_status == ConnectionVerificationStatus.STALE:
            product_status = ConnectionProductStatus.STALE
        elif metadata.verification_status == ConnectionVerificationStatus.FAILED:
            product_status = ConnectionProductStatus.FAILED

        return ExchangeConnectionState(
            connection_id=metadata.connection_id,
            tenant_id=metadata.tenant_id,
            metadata_revision=metadata.metadata_revision,
            verification_status=metadata.verification_status,
            product_status=product_status,
            availability_status=ConnectionAvailabilityStatus.UNKNOWN,
            trading_permission_status=TradingPermissionStatus.UNKNOWN,
            withdrawal_permission_status=WithdrawalPermissionStatus.EXPECTED_DISABLED,
            updated_at=metadata.updated_at,
        )

    def get_connection(
        self,
        *,
        tenant_id: str,
        connection_id: str,
    ) -> ExchangeConnectionProduct:
        metadata = self._repository.get_connection(tenant_id, connection_id)
        state = self._repository.get_state(tenant_id, connection_id)
        profile = self._repository.get_capability_profile(metadata.exchange_profile_ref)
        return ExchangeConnectionProduct(
            metadata=metadata,
            capability_profile=profile,
            state=state,
        )

    def list_connections(self, *, tenant_id: str) -> tuple[ExchangeConnectionProduct, ...]:
        return tuple(
            self.get_connection(tenant_id=tenant_id, connection_id=metadata.connection_id)
            for metadata in self._repository.list_connections(tenant_id)
        )

    def request_verification(
        self,
        *,
        verification_id: str,
        tenant_id: str,
        connection_id: str,
        actor: Actor,
        environment: Environment,
        correlation: CorrelationContext,
        idempotency_key: str,
        requested_at: UtcDateTime,
    ) -> ExchangeConnectionVerificationRequest:
        metadata = self._repository.get_connection(tenant_id, connection_id)
        state = self._repository.get_state(tenant_id, connection_id)
        if actor.tenant_id != tenant_id:
            raise ExchangeConnectionValidationError("verification actor tenant mismatch")
        if metadata.revocation_status == ConnectionRevocationStatus.REVOKED:
            raise VerificationStateError("revoked connection cannot be verified")

        existing = self._repository.get_request_by_idempotency(
            tenant_id,
            connection_id,
            idempotency_key,
        )
        if existing is not None:
            return existing
        if state.verification_status == ConnectionVerificationStatus.PENDING:
            raise VerificationStateError("connection already has pending verification")

        request = ExchangeConnectionVerificationRequest(
            verification_id=verification_id,
            connection_id=connection_id,
            tenant_id=tenant_id,
            metadata_revision=metadata.metadata_revision,
            actor=actor,
            environment=environment,
            correlation=correlation,
            idempotency_key=idempotency_key,
            requested_at=requested_at,
        )
        self._repository.add_verification_request(request)
        pending_metadata = metadata.model_copy(
            update={
                "verification_status": ConnectionVerificationStatus.PENDING,
                "updated_at": requested_at,
            }
        )
        pending_state = state.model_copy(
            update={
                "verification_status": ConnectionVerificationStatus.PENDING,
                "product_status": ConnectionProductStatus.VERIFYING,
                "last_verification_id": verification_id,
                "reason_codes": (),
                "updated_at": requested_at,
            }
        )
        self._repository.replace_connection(pending_metadata, pending_state)
        return request

    def complete_verification(
        self,
        probe: VerificationProbeResult,
    ) -> ExchangeConnectionVerificationResult:
        request = self._repository.get_verification_request(
            probe.tenant_id,
            probe.verification_id,
        )
        existing = self._repository.get_verification_result(
            probe.tenant_id,
            probe.verification_id,
        )
        if existing is not None:
            return existing

        metadata = self._repository.get_connection(probe.tenant_id, probe.connection_id)
        state = self._repository.get_state(probe.tenant_id, probe.connection_id)
        result = ExchangeConnectionVerificationStateMachine.complete(
            request=request,
            current_status=state.verification_status,
            profile_ref=metadata.exchange_profile_ref,
            probe=probe,
        )
        self._repository.add_verification_result(result)

        if result.status == ConnectionVerificationStatus.VERIFIED:
            product_status = ConnectionProductStatus.READY
            availability = ConnectionAvailabilityStatus.AVAILABLE
            trading = TradingPermissionStatus.ENABLED
            withdrawals = WithdrawalPermissionStatus.DISABLED_CONFIRMED
            last_verified_at = result.completed_at
        else:
            reason_set = set(result.reason_codes)
            product_status = (
                ConnectionProductStatus.UNAVAILABLE
                if VerificationReasonCode.EXCHANGE_UNAVAILABLE in reason_set
                else ConnectionProductStatus.FAILED
            )
            availability = (
                ConnectionAvailabilityStatus.UNAVAILABLE
                if VerificationReasonCode.EXCHANGE_UNAVAILABLE in reason_set
                else ConnectionAvailabilityStatus.AVAILABLE
            )
            trading = (
                TradingPermissionStatus.DISABLED
                if VerificationReasonCode.TRADING_PERMISSION_DISABLED in reason_set
                else TradingPermissionStatus.UNKNOWN
            )
            withdrawals = (
                WithdrawalPermissionStatus.ENABLED_REJECTED
                if VerificationReasonCode.WITHDRAWAL_PERMISSION_ENABLED in reason_set
                else WithdrawalPermissionStatus.EXPECTED_DISABLED
            )
            last_verified_at = state.last_verified_at

        updated_metadata = metadata.model_copy(
            update={
                "verification_status": result.status,
                "updated_at": result.completed_at,
            }
        )
        updated_state = state.model_copy(
            update={
                "verification_status": result.status,
                "product_status": product_status,
                "availability_status": availability,
                "trading_permission_status": trading,
                "withdrawal_permission_status": withdrawals,
                "last_verification_id": result.verification_id,
                "last_verified_at": last_verified_at,
                "reason_codes": result.reason_codes,
                "updated_at": result.completed_at,
            }
        )
        self._repository.replace_connection(updated_metadata, updated_state)
        return result

    def mark_stale(
        self,
        *,
        tenant_id: str,
        connection_id: str,
        as_of: UtcDateTime,
        maximum_age: timedelta,
    ) -> ExchangeConnectionProduct:
        if maximum_age <= timedelta(0):
            raise ExchangeConnectionValidationError("maximum_age must be positive")
        metadata = self._repository.get_connection(tenant_id, connection_id)
        state = self._repository.get_state(tenant_id, connection_id)
        if (
            state.last_verified_at is None
            or state.verification_status != ConnectionVerificationStatus.VERIFIED
        ):
            return self.get_connection(tenant_id=tenant_id, connection_id=connection_id)
        if as_of - state.last_verified_at <= maximum_age:
            return self.get_connection(tenant_id=tenant_id, connection_id=connection_id)

        stale_metadata = metadata.model_copy(
            update={
                "verification_status": ConnectionVerificationStatus.STALE,
                "updated_at": as_of,
            }
        )
        stale_state = state.model_copy(
            update={
                "verification_status": ConnectionVerificationStatus.STALE,
                "product_status": ConnectionProductStatus.STALE,
                "updated_at": as_of,
            }
        )
        self._repository.replace_connection(stale_metadata, stale_state)
        return self.get_connection(tenant_id=tenant_id, connection_id=connection_id)

    def apply_credential_inspection(
        self,
        inspection: CredentialReferenceInspection,
        *,
        connection_id: str,
    ) -> ExchangeConnectionProduct:
        metadata = self._repository.get_connection(inspection.tenant_id, connection_id)
        state = self._repository.get_state(inspection.tenant_id, connection_id)
        if inspection.credential_ref != metadata.credential_ref:
            raise ExchangeConnectionValidationError("credential inspection reference mismatch")

        product_status = state.product_status
        rotation_status = metadata.rotation_status
        revocation_status = metadata.revocation_status
        availability_status = state.availability_status

        if inspection.state == CredentialReferenceState.REVOKED:
            product_status = ConnectionProductStatus.REVOKED
            rotation_status = CredentialRotationStatus.REVOKED
            revocation_status = ConnectionRevocationStatus.REVOKED
        elif inspection.state == CredentialReferenceState.ROTATION_REQUIRED:
            product_status = ConnectionProductStatus.ROTATION_REQUIRED
            rotation_status = CredentialRotationStatus.ROTATION_REQUIRED
        elif inspection.state == CredentialReferenceState.UNAVAILABLE:
            product_status = ConnectionProductStatus.UNAVAILABLE
            availability_status = ConnectionAvailabilityStatus.UNAVAILABLE

        updated_metadata = metadata.model_copy(
            update={
                "rotation_status": rotation_status,
                "revocation_status": revocation_status,
                "updated_at": inspection.inspected_at,
            }
        )
        updated_state = state.model_copy(
            update={
                "product_status": product_status,
                "availability_status": availability_status,
                "updated_at": inspection.inspected_at,
            }
        )
        self._repository.replace_connection(updated_metadata, updated_state)
        return self.get_connection(tenant_id=inspection.tenant_id, connection_id=connection_id)

    def refresh_credential_reference(
        self,
        *,
        tenant_id: str,
        connection_id: str,
    ) -> ExchangeConnectionProduct:
        if self._credential_status_port is None:
            raise ExchangeConnectionValidationError("credential status port is not configured")
        metadata = self._repository.get_connection(tenant_id, connection_id)
        inspection = self._credential_status_port.inspect_reference(
            tenant_id=tenant_id,
            credential_ref=metadata.credential_ref,
        )
        return self.apply_credential_inspection(inspection, connection_id=connection_id)
