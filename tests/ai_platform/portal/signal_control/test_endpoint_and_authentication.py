import pytest

from ai_platform.portal.contracts.bot_management.policies import SignalAuthority
from ai_platform.portal.signal_control.schema import (
    ReviseSignalEndpoint,
    SignalControlReasonCode,
    SignalMappingStatus,
    SignalValidationStatus,
    SignatureVerificationStatus,
)
from ai_platform.portal.signal_control.service import SignalControlServiceError
from tests.ai_platform.portal.signal_control.support import (
    NOW,
    RaisingVerifier,
    StaticVerifier,
    context,
    endpoint_request,
    processing_request,
    service_with_endpoint,
    target,
)


def test_create_endpoint_persists_immutable_revision_one() -> None:
    service, repository = service_with_endpoint()
    endpoint = repository.get_endpoint("tenant-a", "endpoint-a", 1)
    assert endpoint is not None
    assert endpoint.revision == 1
    assert endpoint.supersedes_revision is None
    assert endpoint.created_at == NOW
    assert service is not None


def test_create_endpoint_rejects_duplicate_identity() -> None:
    service, _ = service_with_endpoint()
    with pytest.raises(SignalControlServiceError) as error:
        service.create_endpoint(context(), endpoint_request())
    assert error.value.reason_code == SignalControlReasonCode.ENDPOINT_ALREADY_EXISTS


def test_revise_endpoint_creates_contiguous_immutable_revision() -> None:
    service, repository = service_with_endpoint()
    request = ReviseSignalEndpoint(
        **endpoint_request(authority=SignalAuthority.EXECUTION_AUTHORIZED).model_dump(),
        expected_revision=1,
    )
    revised = service.revise_endpoint(context(), request)
    original = repository.get_endpoint("tenant-a", "endpoint-a", 1)
    assert revised.revision == 2
    assert revised.supersedes_revision == 1
    assert original is not None
    assert original.authority == SignalAuthority.ADVISORY_ONLY


def test_revise_endpoint_rejects_stale_expected_revision() -> None:
    service, _ = service_with_endpoint()
    request = ReviseSignalEndpoint(**endpoint_request().model_dump(), expected_revision=2)
    with pytest.raises(SignalControlServiceError) as error:
        service.revise_endpoint(context(), request)
    assert error.value.reason_code == SignalControlReasonCode.ENDPOINT_REVISION_CONFLICT


def test_endpoint_management_requires_capability() -> None:
    service, _ = service_with_endpoint()
    request = ReviseSignalEndpoint(**endpoint_request().model_dump(), expected_revision=1)
    with pytest.raises(SignalControlServiceError) as error:
        service.revise_endpoint(context(manage=False), request)
    assert error.value.reason_code == SignalControlReasonCode.CAPABILITY_MISSING


def test_invalid_signature_is_rejected_with_opaque_evidence() -> None:
    verifier = StaticVerifier(SignatureVerificationStatus.INVALID)
    service, _ = service_with_endpoint(verifier=verifier)
    result = service.process(context(), processing_request(), signature=b"bad", target=target())
    assert result.validation.status == SignalValidationStatus.REJECTED
    assert result.validation.reason_codes == (SignalControlReasonCode.AUTHENTICATION_FAILED,)
    assert result.validation.authentication_evidence_ref == "sigev_invalid001"
    assert result.mapping.status == SignalMappingStatus.REJECTED


def test_unavailable_verification_provider_blocks_signal() -> None:
    verifier = StaticVerifier(SignatureVerificationStatus.UNAVAILABLE)
    service, _ = service_with_endpoint(verifier=verifier)
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert result.validation.status == SignalValidationStatus.BLOCKED
    assert result.validation.reason_codes == (
        SignalControlReasonCode.AUTHENTICATION_PROVIDER_UNAVAILABLE,
    )
    assert result.validation.authentication_evidence_ref is None


def test_verification_provider_exception_fails_closed() -> None:
    service, _ = service_with_endpoint(verifier=RaisingVerifier())
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert result.validation.status == SignalValidationStatus.BLOCKED
    assert result.validation.reason_codes == (
        SignalControlReasonCode.AUTHENTICATION_PROVIDER_UNAVAILABLE,
    )


def test_disabled_endpoint_is_rejected() -> None:
    service, _ = service_with_endpoint(enabled=False)
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert SignalControlReasonCode.ENDPOINT_DISABLED in result.validation.reason_codes


def test_old_endpoint_revision_is_stale_after_revision() -> None:
    service, _ = service_with_endpoint()
    revise = ReviseSignalEndpoint(**endpoint_request().model_dump(), expected_revision=1)
    service.revise_endpoint(context(), revise)
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert SignalControlReasonCode.ENDPOINT_REVISION_STALE in result.validation.reason_codes
