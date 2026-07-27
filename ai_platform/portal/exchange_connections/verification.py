from __future__ import annotations

from ai_platform.portal.contracts.bot_management.exchange_connections import (
    ConnectionVerificationStatus,
    ExchangeConnectionVerificationRequest,
    ExchangeConnectionVerificationResult,
    ExchangePermissionObservation,
    VerificationReasonCode,
)
from ai_platform.portal.exchange_connections.schema import VerificationProbeResult


class VerificationStateError(RuntimeError):
    pass


class ExchangeConnectionVerificationStateMachine:
    @staticmethod
    def complete(
        *,
        request: ExchangeConnectionVerificationRequest,
        current_status: ConnectionVerificationStatus,
        profile_ref: str,
        probe: VerificationProbeResult,
    ) -> ExchangeConnectionVerificationResult:
        if current_status != ConnectionVerificationStatus.PENDING:
            raise VerificationStateError("verification completion requires PENDING state")
        ExchangeConnectionVerificationStateMachine._validate_probe_binding(
            request=request,
            probe=probe,
        )

        reasons: list[VerificationReasonCode] = []
        permission_observation: ExchangePermissionObservation | None = None

        if probe.capability_profile_ref != profile_ref:
            reasons.append(VerificationReasonCode.CAPABILITY_PROFILE_MISMATCH)
        if not probe.exchange_available:
            reasons.append(VerificationReasonCode.EXCHANGE_UNAVAILABLE)
        elif probe.trading_enabled is None or probe.withdrawals_enabled is None:
            reasons.append(VerificationReasonCode.PERMISSION_OBSERVATION_MISSING)
        else:
            if not probe.trading_enabled:
                reasons.append(VerificationReasonCode.TRADING_PERMISSION_DISABLED)
            if probe.withdrawals_enabled:
                reasons.append(VerificationReasonCode.WITHDRAWAL_PERMISSION_ENABLED)
            if not reasons:
                permission_observation = ExchangePermissionObservation(
                    connection_id=probe.connection_id,
                    tenant_id=probe.tenant_id,
                    trading_enabled=True,
                    withdrawals_enabled=False,
                    observed_at=probe.observed_at,
                    evidence_ref=probe.evidence_ref,
                )

        status = (
            ConnectionVerificationStatus.VERIFIED
            if not reasons
            else ConnectionVerificationStatus.FAILED
        )
        return ExchangeConnectionVerificationResult(
            verification_id=probe.verification_id,
            connection_id=probe.connection_id,
            tenant_id=probe.tenant_id,
            metadata_revision=probe.metadata_revision,
            status=status,
            permission_observation=permission_observation,
            reason_codes=tuple(sorted(reasons, key=lambda item: item.value)),
            completed_at=probe.observed_at,
        )

    @staticmethod
    def _validate_probe_binding(
        *,
        request: ExchangeConnectionVerificationRequest,
        probe: VerificationProbeResult,
    ) -> None:
        if probe.verification_id != request.verification_id:
            raise VerificationStateError("verification id mismatch")
        if probe.tenant_id != request.tenant_id:
            raise VerificationStateError("verification tenant mismatch")
        if probe.connection_id != request.connection_id:
            raise VerificationStateError("verification connection mismatch")
        if probe.metadata_revision != request.metadata_revision:
            raise VerificationStateError("verification metadata revision mismatch")
