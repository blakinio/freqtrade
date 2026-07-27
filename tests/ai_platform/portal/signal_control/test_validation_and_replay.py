from datetime import timedelta

from ai_platform.portal.contracts.bot_management.policies import SignalCommand
from ai_platform.portal.signal_control.schema import (
    SignalControlReasonCode,
    SignalValidationStatus,
)
from tests.ai_platform.portal.signal_control.support import (
    NOW,
    context,
    processing_request,
    service_with_endpoint,
    target,
)


def test_expired_timestamp_is_rejected() -> None:
    service, _ = service_with_endpoint()
    issued_at = (NOW - timedelta(seconds=301)).isoformat()
    result = service.process(
        context(), processing_request(issued_at=issued_at), signature=b"x", target=target()
    )
    assert result.validation.status == SignalValidationStatus.EXPIRED
    assert result.validation.reason_codes == (SignalControlReasonCode.TIMESTAMP_EXPIRED,)


def test_timestamp_beyond_future_skew_is_rejected() -> None:
    service, _ = service_with_endpoint()
    issued_at = (NOW + timedelta(seconds=31)).isoformat()
    result = service.process(
        context(), processing_request(issued_at=issued_at), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.TIMESTAMP_FUTURE,)


def test_required_nonce_missing_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(), processing_request(nonce=None), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.NONCE_MISSING,)


def test_duplicate_nonce_with_new_idempotency_is_replayed() -> None:
    service, _ = service_with_endpoint()
    service.process(context(), processing_request(), signature=b"x", target=target())
    replay = service.process(
        context(),
        processing_request(signal_id="signal-b", idempotency_key="idem-b"),
        signature=b"x",
        target=target(),
    )
    assert replay.validation.status == SignalValidationStatus.REPLAYED
    assert replay.validation.reason_codes == (SignalControlReasonCode.NONCE_REPLAYED,)


def test_replay_attempt_with_changed_command_is_rejected() -> None:
    service, _ = service_with_endpoint()
    service.process(context(), processing_request(), signature=b"x", target=target())
    replay = service.process(
        context(),
        processing_request(
            SignalCommand.DCA,
            signal_id="signal-b",
            idempotency_key="idem-b",
            nonce="nonce-a",
        ),
        signature=b"x",
        target=target(),
    )
    assert replay.validation.reason_codes == (SignalControlReasonCode.NONCE_REPLAYED,)


def test_duplicate_idempotency_returns_original_result() -> None:
    service, repository = service_with_endpoint()
    first = service.process(context(), processing_request(), signature=b"x", target=target())
    duplicate = service.process(context(), processing_request(), signature=b"x", target=target())
    assert duplicate is first
    assert repository.list_processing("tenant-a") == (first,)


def test_idempotency_conflict_is_rejected() -> None:
    service, _ = service_with_endpoint()
    service.process(context(), processing_request(), signature=b"x", target=target())
    conflict = service.process(
        context(),
        processing_request(signal_id="signal-b", nonce="nonce-b"),
        signature=b"x",
        target=target(),
    )
    assert conflict.validation.reason_codes == (SignalControlReasonCode.IDEMPOTENCY_CONFLICT,)


def test_endpoint_command_allowlist_rejects_unsupported_command() -> None:
    service, _ = service_with_endpoint(supported_commands=(SignalCommand.OPEN,))
    result = service.process(
        context(), processing_request(SignalCommand.DCA), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.COMMAND_UNSUPPORTED,)


def test_unexpected_payload_field_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(), processing_request(unexpected="value"), signature=b"x", target=target()
    )
    assert SignalControlReasonCode.PAYLOAD_INVALID in result.validation.reason_codes


def test_malformed_payload_schema_version_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(),
        processing_request(schema_revision=2),
        signature=b"x",
        target=target(),
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.SCHEMA_UNSUPPORTED,)


def test_unknown_command_type_is_payload_invalid() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(), processing_request(command="DROP_DATABASE"), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.PAYLOAD_INVALID,)


def test_cross_tenant_payload_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(),
        processing_request(tenant_id="tenant-b"),
        signature=b"x",
        target=target(),
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.TENANT_MISMATCH,)


def test_stale_bot_revision_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(), processing_request(bot_revision=3), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.BOT_REVISION_STALE,)


def test_stale_configuration_revision_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(), processing_request(config_revision=6), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (
        SignalControlReasonCode.CONFIGURATION_REVISION_STALE,
    )


def test_stale_runtime_revision_is_rejected() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context(), processing_request(runtime_revision=2), signature=b"x", target=target()
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.RUNTIME_REVISION_STALE,)


def test_same_signal_identity_with_new_nonce_and_idempotency_is_replayed() -> None:
    service, _ = service_with_endpoint()
    service.process(context(), processing_request(), signature=b"x", target=target())
    replay = service.process(
        context(),
        processing_request(idempotency_key="idem-b", nonce="nonce-b"),
        signature=b"x",
        target=target(),
    )
    assert replay.validation.status == SignalValidationStatus.REPLAYED
    assert replay.validation.reason_codes == (SignalControlReasonCode.SIGNAL_REPLAYED,)


def test_cross_tenant_endpoint_resolution_fails_closed() -> None:
    service, _ = service_with_endpoint()
    result = service.process(
        context("tenant-b"),
        processing_request(tenant_id="tenant-b"),
        signature=b"x",
        target=target("tenant-b"),
    )
    assert result.validation.reason_codes == (SignalControlReasonCode.TENANT_MISMATCH,)
