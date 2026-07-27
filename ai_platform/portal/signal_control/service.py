from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from pydantic import ValidationError

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import SignalAuthority
from ai_platform.portal.signal_control.authentication import SignatureVerificationProvider
from ai_platform.portal.signal_control.command_mapping import map_signal_to_command_intent
from ai_platform.portal.signal_control.replay import ReplayDecision, nonce_digest
from ai_platform.portal.signal_control.repository import SignalControlRepository
from ai_platform.portal.signal_control.schema import (
    AuthoritativeSignalTargetState,
    CreateSignalEndpoint,
    ReviseSignalEndpoint,
    SIGNAL_PAYLOAD_SCHEMA_V1,
    SignalAuditRecord,
    SignalControlContext,
    SignalControlReasonCode,
    SignalEndpointRevision,
    SignalMappingEvidence,
    SignalMappingStatus,
    SignalPayloadV1,
    SignalProcessingMode,
    SignalProcessingRequest,
    SignalProcessingResult,
    SignalValidationEvidence,
    SignalValidationStatus,
    SignatureVerificationDecision,
    SignatureVerificationStatus,
)


Clock = Callable[[], datetime]


class SignalControlServiceError(RuntimeError):
    def __init__(self, reason_code: SignalControlReasonCode) -> None:
        super().__init__(reason_code.value)
        self.reason_code = reason_code


class SignalControlService:
    """Validate and map external signals without execution or BM-03 submission."""

    def __init__(
        self,
        repository: SignalControlRepository,
        verifier: SignatureVerificationProvider,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._verifier = verifier
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_endpoint(
        self,
        context: SignalControlContext,
        request: CreateSignalEndpoint,
    ) -> SignalEndpointRevision:
        self._require_capability(context, BotManagementCapability.SIGNAL_ENDPOINT_MANAGE)
        if self._repository.get_latest_endpoint(context.tenant_id, request.endpoint_id) is not None:
            raise SignalControlServiceError(SignalControlReasonCode.ENDPOINT_ALREADY_EXISTS)
        endpoint = self._endpoint_revision(context, request, revision=1)
        self._repository.save_endpoint(endpoint)
        return endpoint

    def revise_endpoint(
        self,
        context: SignalControlContext,
        request: ReviseSignalEndpoint,
    ) -> SignalEndpointRevision:
        self._require_capability(context, BotManagementCapability.SIGNAL_ENDPOINT_MANAGE)
        latest = self._repository.get_latest_endpoint(context.tenant_id, request.endpoint_id)
        if latest is None:
            raise SignalControlServiceError(SignalControlReasonCode.ENDPOINT_NOT_FOUND)
        if latest.revision != request.expected_revision:
            raise SignalControlServiceError(SignalControlReasonCode.ENDPOINT_REVISION_CONFLICT)
        endpoint = self._endpoint_revision(
            context,
            request,
            revision=latest.revision + 1,
            supersedes_revision=latest.revision,
        )
        self._repository.save_endpoint(endpoint)
        return endpoint

    def process(
        self,
        context: SignalControlContext,
        request: SignalProcessingRequest,
        *,
        signature: bytes,
        target: AuthoritativeSignalTargetState,
    ) -> SignalProcessingResult:
        return self._process(
            context,
            request,
            signature=signature,
            target=target,
            mode=SignalProcessingMode.ACCEPT,
        )

    def preview(
        self,
        context: SignalControlContext,
        request: SignalProcessingRequest,
        *,
        signature: bytes,
        target: AuthoritativeSignalTargetState,
    ) -> SignalProcessingResult:
        return self._process(
            context,
            request,
            signature=signature,
            target=target,
            mode=SignalProcessingMode.PREVIEW,
        )

    def _process(
        self,
        context: SignalControlContext,
        request: SignalProcessingRequest,
        *,
        signature: bytes,
        target: AuthoritativeSignalTargetState,
        mode: SignalProcessingMode,
    ) -> SignalProcessingResult:
        now = self._clock()
        payload_bytes, payload_sha256 = self._canonical_payload(request.payload)
        reasons: list[SignalControlReasonCode] = []
        endpoint = self._resolve_endpoint(context, request, reasons)
        payload = self._parse_payload(request, reasons)
        verification = self._verify(endpoint, payload_bytes, signature)
        self._append_verification_reasons(endpoint, verification, reasons)
        if endpoint is not None and payload is not None:
            self._validate_bindings(context, request, endpoint, payload, target, reasons)
            self._validate_timestamp(endpoint, payload, now, reasons)

        nonce_sha256 = nonce_digest(payload.nonce) if payload is not None else None
        existing = self._claim_replay(
            context=context,
            endpoint=endpoint,
            payload=payload,
            payload_sha256=payload_sha256,
            nonce_sha256=nonce_sha256,
            now=now,
            mode=mode,
            reasons=reasons,
        )
        if existing is not None:
            return existing

        result = self._build_result(
            context=context,
            request=request,
            endpoint=endpoint,
            payload=payload,
            target=target,
            payload_sha256=payload_sha256,
            nonce_sha256=nonce_sha256,
            verification=verification,
            reasons=self._sorted_reasons(reasons),
            now=now,
            mode=mode,
        )
        self._persist_result(context, endpoint, payload, result, mode)
        return result

    def _endpoint_revision(
        self,
        context: SignalControlContext,
        request: CreateSignalEndpoint,
        *,
        revision: int,
        supersedes_revision: int | None = None,
    ) -> SignalEndpointRevision:
        return SignalEndpointRevision(
            endpoint_id=request.endpoint_id,
            tenant_id=context.tenant_id,
            revision=revision,
            supersedes_revision=supersedes_revision,
            display_name=request.display_name,
            endpoint_slug=request.endpoint_slug,
            authentication_mode=request.authentication_mode,
            authentication_ref=request.authentication_ref,
            schema_id=request.schema_id,
            schema_revision=request.schema_revision,
            supported_commands=request.supported_commands,
            authority=request.authority,
            max_past_age_seconds=request.max_past_age_seconds,
            max_future_skew_seconds=request.max_future_skew_seconds,
            replay_window_seconds=request.replay_window_seconds,
            require_nonce=request.require_nonce,
            enabled=request.enabled,
            created_by_actor_id=context.actor.actor_id,
            created_at=self._clock(),
        )

    def _resolve_endpoint(
        self,
        context: SignalControlContext,
        request: SignalProcessingRequest,
        reasons: list[SignalControlReasonCode],
    ) -> SignalEndpointRevision | None:
        endpoint = self._repository.get_endpoint(
            context.tenant_id,
            request.endpoint_id,
            request.endpoint_revision,
        )
        if endpoint is None:
            other = self._repository.get_endpoint_any_tenant(
                request.endpoint_id,
                request.endpoint_revision,
            )
            reasons.append(
                SignalControlReasonCode.TENANT_MISMATCH
                if other is not None
                else SignalControlReasonCode.ENDPOINT_NOT_FOUND
            )
            return None
        latest = self._repository.get_latest_endpoint(context.tenant_id, request.endpoint_id)
        if latest is not None and endpoint.revision != latest.revision:
            reasons.append(SignalControlReasonCode.ENDPOINT_REVISION_STALE)
        if not endpoint.enabled:
            reasons.append(SignalControlReasonCode.ENDPOINT_DISABLED)
        return endpoint

    @staticmethod
    def _parse_payload(
        request: SignalProcessingRequest,
        reasons: list[SignalControlReasonCode],
    ) -> SignalPayloadV1 | None:
        if (
            request.schema_id != SIGNAL_PAYLOAD_SCHEMA_V1.schema_id
            or request.schema_revision != SIGNAL_PAYLOAD_SCHEMA_V1.revision
        ):
            reasons.append(SignalControlReasonCode.SCHEMA_UNSUPPORTED)
            return None
        try:
            return SignalPayloadV1.model_validate(request.payload)
        except ValidationError:
            reasons.append(SignalControlReasonCode.PAYLOAD_INVALID)
            return None

    @staticmethod
    def _append_verification_reasons(
        endpoint: SignalEndpointRevision | None,
        verification: SignatureVerificationDecision,
        reasons: list[SignalControlReasonCode],
    ) -> None:
        if endpoint is None:
            return
        if verification.status == SignatureVerificationStatus.INVALID:
            reasons.append(SignalControlReasonCode.AUTHENTICATION_FAILED)
        if verification.status == SignatureVerificationStatus.UNAVAILABLE:
            reasons.append(SignalControlReasonCode.AUTHENTICATION_PROVIDER_UNAVAILABLE)

    def _claim_replay(
        self,
        *,
        context: SignalControlContext,
        endpoint: SignalEndpointRevision | None,
        payload: SignalPayloadV1 | None,
        payload_sha256: str,
        nonce_sha256: str | None,
        now: datetime,
        mode: SignalProcessingMode,
        reasons: list[SignalControlReasonCode],
    ) -> SignalProcessingResult | None:
        if reasons or endpoint is None or payload is None:
            return None
        decision, existing = self._repository.claim_replay(
            tenant_id=context.tenant_id,
            endpoint_id=endpoint.endpoint_id,
            endpoint_revision=endpoint.revision,
            idempotency_key=payload.idempotency_key,
            signal_id=payload.signal_id,
            nonce_sha256=nonce_sha256,
            payload_sha256=payload_sha256,
            idempotency_expires_at=payload.issued_at
            + timedelta(seconds=endpoint.max_past_age_seconds),
            nonce_expires_at=payload.issued_at
            + timedelta(seconds=endpoint.replay_window_seconds),
            now=now,
            consume=mode == SignalProcessingMode.ACCEPT,
        )
        if decision == ReplayDecision.IDEMPOTENT_REPLAY:
            if mode == SignalProcessingMode.ACCEPT and existing is not None:
                return existing
            reasons.append(SignalControlReasonCode.IDEMPOTENCY_DUPLICATE)
        elif decision == ReplayDecision.IDEMPOTENCY_CONFLICT:
            reasons.append(SignalControlReasonCode.IDEMPOTENCY_CONFLICT)
        elif decision == ReplayDecision.NONCE_REPLAYED:
            reasons.append(SignalControlReasonCode.NONCE_REPLAYED)
        elif decision == ReplayDecision.SIGNAL_REPLAYED:
            reasons.append(SignalControlReasonCode.SIGNAL_REPLAYED)
        return None

    def _persist_result(
        self,
        context: SignalControlContext,
        endpoint: SignalEndpointRevision | None,
        payload: SignalPayloadV1 | None,
        result: SignalProcessingResult,
        mode: SignalProcessingMode,
    ) -> None:
        if mode != SignalProcessingMode.ACCEPT:
            return
        self._repository.save_processing(result)
        if result.validation.reason_codes or endpoint is None or payload is None:
            return
        self._repository.complete_replay(
            tenant_id=context.tenant_id,
            endpoint_id=endpoint.endpoint_id,
            endpoint_revision=endpoint.revision,
            idempotency_key=payload.idempotency_key,
            result=result,
        )

    @staticmethod
    def _validate_bindings(
        context: SignalControlContext,
        request: SignalProcessingRequest,
        endpoint: SignalEndpointRevision,
        payload: SignalPayloadV1,
        target: AuthoritativeSignalTargetState,
        reasons: list[SignalControlReasonCode],
    ) -> None:
        if (
            payload.tenant_id != context.tenant_id
            or payload.tenant_id != endpoint.tenant_id
            or target.tenant_id != context.tenant_id
        ):
            reasons.append(SignalControlReasonCode.TENANT_MISMATCH)
        if payload.endpoint_id != request.endpoint_id:
            reasons.append(SignalControlReasonCode.PAYLOAD_INVALID)
        if (
            endpoint.schema_id != request.schema_id
            or endpoint.schema_revision != request.schema_revision
        ):
            reasons.append(SignalControlReasonCode.SCHEMA_UNSUPPORTED)
        if payload.command not in endpoint.supported_commands:
            reasons.append(SignalControlReasonCode.COMMAND_UNSUPPORTED)
        if endpoint.require_nonce and payload.nonce is None:
            reasons.append(SignalControlReasonCode.NONCE_MISSING)
        if payload.bot_id != target.bot_id or payload.bot_revision != target.bot_revision:
            reasons.append(SignalControlReasonCode.BOT_REVISION_STALE)
        if payload.config_revision != target.config_revision:
            reasons.append(SignalControlReasonCode.CONFIGURATION_REVISION_STALE)
        if (
            payload.runtime_id != target.runtime_id
            or payload.runtime_revision != target.runtime_revision
        ):
            reasons.append(SignalControlReasonCode.RUNTIME_REVISION_STALE)

    @staticmethod
    def _validate_timestamp(
        endpoint: SignalEndpointRevision,
        payload: SignalPayloadV1,
        now: datetime,
        reasons: list[SignalControlReasonCode],
    ) -> None:
        age_seconds = (now - payload.issued_at).total_seconds()
        if age_seconds > endpoint.max_past_age_seconds:
            reasons.append(SignalControlReasonCode.TIMESTAMP_EXPIRED)
        if age_seconds < -endpoint.max_future_skew_seconds:
            reasons.append(SignalControlReasonCode.TIMESTAMP_FUTURE)

    def _verify(
        self,
        endpoint: SignalEndpointRevision | None,
        payload_bytes: bytes,
        signature: bytes,
    ) -> SignatureVerificationDecision:
        if endpoint is None:
            return SignatureVerificationDecision(status=SignatureVerificationStatus.UNAVAILABLE)
        try:
            return self._verifier.verify(
                authentication_ref=endpoint.authentication_ref,
                authentication_mode=endpoint.authentication_mode,
                canonical_payload=payload_bytes,
                signature=signature,
            )
        except Exception:
            return SignatureVerificationDecision(status=SignatureVerificationStatus.UNAVAILABLE)

    def _build_result(
        self,
        *,
        context: SignalControlContext,
        request: SignalProcessingRequest,
        endpoint: SignalEndpointRevision | None,
        payload: SignalPayloadV1 | None,
        target: AuthoritativeSignalTargetState,
        payload_sha256: str,
        nonce_sha256: str | None,
        verification: SignatureVerificationDecision,
        reasons: tuple[SignalControlReasonCode, ...],
        now: datetime,
        mode: SignalProcessingMode,
    ) -> SignalProcessingResult:
        signal_id = payload.signal_id if payload is not None else f"invalid-{payload_sha256[:16]}"
        attempted_tenant = payload.tenant_id if payload is not None else context.tenant_id
        endpoint_revision = endpoint.revision if endpoint is not None else request.endpoint_revision
        validation_status = self._validation_status(reasons)
        validation_id = self._digest_id(
            "validation",
            context.tenant_id,
            request.endpoint_id,
            str(endpoint_revision),
            payload_sha256,
            ",".join(reason.value for reason in reasons),
        )
        validation = SignalValidationEvidence(
            validation_id=validation_id,
            signal_id=signal_id,
            scope_tenant_id=context.tenant_id,
            attempted_tenant_id=attempted_tenant,
            endpoint_id=request.endpoint_id,
            endpoint_revision=endpoint_revision,
            schema_id=request.schema_id,
            schema_revision=request.schema_revision,
            payload_sha256=payload_sha256,
            nonce_sha256=nonce_sha256,
            authentication_evidence_ref=verification.evidence_ref,
            status=validation_status,
            reason_codes=reasons,
            validated_at=now,
        )
        command_intent = None
        if reasons:
            mapping_status = SignalMappingStatus.REJECTED
            authority = (
                endpoint.authority if endpoint is not None else SignalAuthority.ADVISORY_ONLY
            )
            vocabulary = None
            mapped_action = None
            command_intent_id = None
        elif endpoint is not None and payload is not None:
            authority = endpoint.authority
            if authority == SignalAuthority.ADVISORY_ONLY:
                mapping_status = SignalMappingStatus.ADVISORY_RECORDED
                vocabulary = None
                mapped_action = None
                command_intent_id = None
            else:
                command_intent = map_signal_to_command_intent(
                    endpoint=endpoint,
                    payload=payload,
                    target=target,
                    payload_sha256=payload_sha256,
                    created_at=now,
                    preview_only=mode == SignalProcessingMode.PREVIEW,
                )
                mapping_status = SignalMappingStatus.COMMAND_INTENT_CREATED
                vocabulary = command_intent.vocabulary
                mapped_action = command_intent.action
                command_intent_id = command_intent.intent_id
        else:
            raise AssertionError("valid signal mapping requires endpoint and payload")

        mapping_id = self._digest_id(
            "mapping",
            validation_id,
            mapping_status.value,
            command_intent_id or "none",
        )
        mapping = SignalMappingEvidence(
            mapping_id=mapping_id,
            signal_id=signal_id,
            tenant_id=context.tenant_id,
            endpoint_id=request.endpoint_id,
            endpoint_revision=endpoint_revision,
            status=mapping_status,
            authority=authority,
            command_intent_id=command_intent_id,
            vocabulary=vocabulary,
            mapped_action=mapped_action,
            reason_codes=reasons,
            mapped_at=now,
        )
        processing_id = self._digest_id("processing", validation_id, mapping_id, mode.value)
        audit = SignalAuditRecord(
            audit_id=UUID(processing_id[:32]),
            tenant_id=context.tenant_id,
            actor_id=context.actor.actor_id,
            processing_id=processing_id,
            result=validation_status,
            reason_codes=reasons,
            occurred_at=now,
        )
        return SignalProcessingResult(
            processing_id=processing_id,
            mode=mode,
            validation=validation,
            mapping=mapping,
            audit=audit,
            command_intent=command_intent,
            persisted=mode == SignalProcessingMode.ACCEPT,
        )

    @staticmethod
    def _canonical_payload(payload: dict[str, object]) -> tuple[bytes, str]:
        try:
            rendered = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        except (TypeError, ValueError):
            rendered = b"INVALID_JSON_PAYLOAD"
        return rendered, sha256(rendered).hexdigest()

    @staticmethod
    def _validation_status(
        reasons: tuple[SignalControlReasonCode, ...],
    ) -> SignalValidationStatus:
        if not reasons:
            return SignalValidationStatus.VALID
        if SignalControlReasonCode.AUTHENTICATION_PROVIDER_UNAVAILABLE in reasons:
            return SignalValidationStatus.BLOCKED
        if (
            SignalControlReasonCode.NONCE_REPLAYED in reasons
            or SignalControlReasonCode.SIGNAL_REPLAYED in reasons
        ):
            return SignalValidationStatus.REPLAYED
        if SignalControlReasonCode.TIMESTAMP_EXPIRED in reasons:
            return SignalValidationStatus.EXPIRED
        return SignalValidationStatus.REJECTED

    @staticmethod
    def _sorted_reasons(
        reasons: list[SignalControlReasonCode],
    ) -> tuple[SignalControlReasonCode, ...]:
        return tuple(sorted(set(reasons), key=lambda item: item.value))

    @staticmethod
    def _digest_id(*parts: str) -> str:
        return sha256("|".join(parts).encode("utf-8")).hexdigest()

    @staticmethod
    def _require_capability(
        context: SignalControlContext,
        capability: BotManagementCapability,
    ) -> None:
        if capability not in context.capabilities:
            raise SignalControlServiceError(SignalControlReasonCode.CAPABILITY_MISSING)
