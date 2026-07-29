from __future__ import annotations

import hashlib
import ipaddress
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx

from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.credentials.material import ResolvedCredentialLease
from ai_platform.portal.execution_submission.errors import (
    SubmissionPolicyError,
    SubmissionRuntimeRejectedError,
    SubmissionTransportAmbiguousError,
    SubmissionTransportError,
)
from ai_platform.portal.execution_submission.schema import (
    PrivateDryRunSubmission,
    RuntimeDryRunEvidence,
    RuntimeSubmissionResponse,
)


@dataclass(frozen=True)
class PrivateRuntimeTarget:
    runtime_id: str
    endpoint: str = field(repr=False)
    ca_certificate_path: Path = field(repr=False)

    def __post_init__(self) -> None:
        if not self.runtime_id.strip():
            raise ValueError("runtime_id must not be empty")
        if not self.ca_certificate_path.is_file():
            raise SubmissionPolicyError("RUNTIME_CA_CERTIFICATE_UNAVAILABLE")
        object.__setattr__(self, "endpoint", _validate_private_https_endpoint(self.endpoint))


class PrivateSubmissionTransport(Protocol):
    def verify_dry_run(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
    ) -> RuntimeDryRunEvidence: ...

    def submit(
        self,
        target: PrivateRuntimeTarget,
        submission: PrivateDryRunSubmission,
        lease: ResolvedCredentialLease,
    ) -> RuntimeSubmissionResponse: ...


def _validate_private_https_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SubmissionPolicyError("RUNTIME_TLS_PRIVATE_ENDPOINT_REQUIRED")
    if parsed.username is not None or parsed.password is not None:
        raise SubmissionPolicyError("RUNTIME_ENDPOINT_EMBEDS_CREDENTIALS")
    if parsed.query or parsed.fragment:
        raise SubmissionPolicyError("RUNTIME_ENDPOINT_QUERY_OR_FRAGMENT_REJECTED")
    if parsed.path not in {"", "/"}:
        raise SubmissionPolicyError("RUNTIME_ENDPOINT_PATH_REJECTED")

    hostname = parsed.hostname.lower().rstrip(".")
    private = "." not in hostname or hostname.endswith((".internal", ".local", ".lan"))
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        private = address.is_private or address.is_loopback or address.is_link_local
    if not private:
        raise SubmissionPolicyError("RUNTIME_ENDPOINT_MUST_BE_PRIVATE")
    authority = hostname if parsed.port is None else f"{hostname}:{parsed.port}"
    return f"https://{authority}"


class HttpxPrivateFreqtradeTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        max_body_bytes: int = 1_048_576,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._timeout_seconds = timeout_seconds
        self._max_body_bytes = max_body_bytes

    def verify_dry_run(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
    ) -> RuntimeDryRunEvidence:
        payload = lease.use_runtime_api(
            lambda username, password: self._request(
                target,
                "GET",
                "/api/v1/show_config",
                username,
                password,
                payload=None,
                ambiguous_on_transport=False,
            )
        )
        if payload.get("dry_run") is not True:
            raise SubmissionPolicyError("RUNTIME_NOT_DRY_RUN")
        if payload.get("force_entry_enable") is not True:
            raise SubmissionPolicyError("RUNTIME_FORCE_ENTRY_DISABLED")
        digest = _digest(payload)
        return RuntimeDryRunEvidence(
            runtime_id=target.runtime_id,
            verified_at=datetime.now(UTC),
            config_digest=digest,
        )

    def submit(
        self,
        target: PrivateRuntimeTarget,
        submission: PrivateDryRunSubmission,
        lease: ResolvedCredentialLease,
    ) -> RuntimeSubmissionResponse:
        trade_intent = submission.intent.trade_intent
        payload: dict[str, Any] = {
            "pair": trade_intent.pair,
            "side": "long" if trade_intent.side == TradeSide.BUY else "short",
            "stakeamount": str(trade_intent.amount),
            "enter_tag": f"portal:{submission.intent.execution_intent_id}",
        }
        response = lease.use_runtime_api(
            lambda username, password: self._request(
                target,
                "POST",
                "/api/v1/forceenter",
                username,
                password,
                payload=payload,
                ambiguous_on_transport=True,
            )
        )
        _require_force_entry_acknowledgement(response, expected_pair=trade_intent.pair)
        digest = _digest(response)
        runtime_ref = _runtime_request_ref(response, digest)
        return RuntimeSubmissionResponse(
            runtime_request_ref=runtime_ref,
            response_digest=digest,
        )

    def _request(
        self,
        target: PrivateRuntimeTarget,
        method: str,
        path: str,
        username: bytes,
        password: bytes,
        *,
        payload: Mapping[str, Any] | None,
        ambiguous_on_transport: bool,
    ) -> dict[str, Any]:
        url = f"{target.endpoint}{path}"
        try:
            username_text = username.decode("utf-8")
            password_text = password.decode("utf-8")
        except UnicodeError:
            raise SubmissionTransportError("RUNTIME_AUTHENTICATION_ENCODING_INVALID") from None

        try:
            with httpx.Client(
                verify=str(target.ca_certificate_path),
                timeout=self._timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = client.request(
                    method,
                    url,
                    auth=(username_text, password_text),
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    json=dict(payload) if payload is not None else None,
                )
        except (httpx.TimeoutException, httpx.NetworkError):
            if ambiguous_on_transport:
                raise SubmissionTransportAmbiguousError() from None
            raise SubmissionTransportError("RUNTIME_CONFIG_TRANSPORT_UNAVAILABLE") from None

        if 300 <= response.status_code < 400:
            raise SubmissionTransportError("RUNTIME_REDIRECT_REJECTED")
        if response.status_code in {401, 403}:
            raise SubmissionTransportError("RUNTIME_AUTHENTICATION_FAILED")
        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            digest = hashlib.sha256(response.content).hexdigest() if response.content else None
            if ambiguous_on_transport:
                raise SubmissionTransportAmbiguousError(digest) from None
            raise SubmissionTransportError("RUNTIME_CONFIG_TRANSPORT_UNAVAILABLE")
        if response.status_code >= 400:
            if ambiguous_on_transport:
                raise SubmissionRuntimeRejectedError() from None
            raise SubmissionTransportError("RUNTIME_CONFIG_REQUEST_REJECTED")
        if len(response.content) > self._max_body_bytes:
            if ambiguous_on_transport:
                raise SubmissionTransportAmbiguousError(
                    hashlib.sha256(response.content).hexdigest()
                ) from None
            raise SubmissionTransportError("RUNTIME_RESPONSE_TOO_LARGE")
        try:
            decoded = response.json()
        except ValueError:
            if ambiguous_on_transport:
                raise SubmissionTransportAmbiguousError(
                    hashlib.sha256(response.content).hexdigest()
                ) from None
            raise SubmissionTransportError("RUNTIME_CONFIG_INVALID_JSON") from None
        if not isinstance(decoded, dict):
            if ambiguous_on_transport:
                raise SubmissionTransportAmbiguousError(_digest(decoded)) from None
            raise SubmissionTransportError("RUNTIME_CONFIG_INVALID_SHAPE")
        return decoded


def _require_force_entry_acknowledgement(
    response: Mapping[str, Any],
    *,
    expected_pair: str,
) -> None:
    runtime_id_present = any(
        isinstance(response.get(key), (str, int)) and str(response[key]).strip()
        for key in ("trade_id", "order_id", "id")
    )
    if not runtime_id_present:
        raise SubmissionRuntimeRejectedError()
    observed_pair = response.get("pair")
    if observed_pair is not None and observed_pair != expected_pair:
        raise SubmissionTransportAmbiguousError(_digest(response))


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _runtime_request_ref(response: Mapping[str, Any], digest: str) -> str:
    for key in ("trade_id", "order_id", "id"):
        value = response.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return f"freqtrade-{key}-{value}"
    return f"freqtrade-response-{digest[:32]}"
