from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

from ai_platform.portal.bot_operations.activation_errors import (
    CommandActivationAmbiguousError,
    CommandActivationRejectedError,
    CommandActivationTransportError,
)
from ai_platform.portal.bot_operations.activation_schema import RuntimeCommandAcknowledgement
from ai_platform.portal.credentials.material import ResolvedCredentialLease
from ai_platform.portal.execution_submission.transport import PrivateRuntimeTarget


Clock = Callable[[], datetime]


class PrivateRuntimeCommandTransport(Protocol):
    def force_exit(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        *,
        trade_id: str,
        amount: str | None = None,
    ) -> RuntimeCommandAcknowledgement: ...

    def cancel_open_order(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        *,
        trade_id: str,
    ) -> RuntimeCommandAcknowledgement: ...


class HttpxPrivateRuntimeCommandTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        max_body_bytes: int = 1_048_576,
        http_transport: httpx.BaseTransport | None = None,
        clock: Clock | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._timeout_seconds = timeout_seconds
        self._max_body_bytes = max_body_bytes
        self._http_transport = http_transport
        self._clock = clock or (lambda: datetime.now(UTC))

    def force_exit(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        *,
        trade_id: str,
        amount: str | None = None,
    ) -> RuntimeCommandAcknowledgement:
        payload: dict[str, Any] = {"tradeid": trade_id}
        if amount is not None:
            payload["amount"] = amount
        response = self._request(target, lease, "POST", "/api/v1/forceexit", payload)
        status = response.get("status")
        if not isinstance(status, str) or not status.strip():
            raise CommandActivationRejectedError()
        return self._acknowledgement("forceexit", trade_id, response)

    def cancel_open_order(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        *,
        trade_id: str,
    ) -> RuntimeCommandAcknowledgement:
        response = self._request(
            target,
            lease,
            "DELETE",
            f"/api/v1/trades/{trade_id}/open-order",
            None,
        )
        if response.get("result") is not True:
            raise CommandActivationRejectedError()
        return self._acknowledgement("cancel", trade_id, response)

    def _request(
        self,
        target: PrivateRuntimeTarget,
        lease: ResolvedCredentialLease,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        return lease.use_runtime_api(
            lambda username, password: self._request_with_auth(
                target,
                method,
                path,
                payload,
                username,
                password,
            )
        )

    def _request_with_auth(
        self,
        target: PrivateRuntimeTarget,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None,
        username: bytes,
        password: bytes,
    ) -> dict[str, Any]:
        try:
            auth = (username.decode("utf-8"), password.decode("utf-8"))
        except UnicodeError:
            raise CommandActivationTransportError(
                "RUNTIME_AUTHENTICATION_ENCODING_INVALID"
            ) from None
        try:
            with httpx.Client(
                verify=str(target.ca_certificate_path),
                timeout=self._timeout_seconds,
                follow_redirects=False,
                trust_env=False,
                transport=self._http_transport,
            ) as client:
                response = client.request(
                    method,
                    f"{target.endpoint}{path}",
                    auth=auth,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    json=dict(payload) if payload is not None else None,
                )
        except (httpx.TimeoutException, httpx.NetworkError):
            raise CommandActivationAmbiguousError() from None
        return self._decode(response)

    def _decode(self, response: httpx.Response) -> dict[str, Any]:
        if 300 <= response.status_code < 400:
            raise CommandActivationTransportError("RUNTIME_REDIRECT_REJECTED")
        if response.status_code in {401, 403}:
            raise CommandActivationTransportError("RUNTIME_AUTHENTICATION_FAILED")
        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            digest = hashlib.sha256(response.content).hexdigest() if response.content else None
            raise CommandActivationAmbiguousError(digest) from None
        if response.status_code >= 400:
            raise CommandActivationRejectedError()
        if len(response.content) > self._max_body_bytes:
            raise CommandActivationAmbiguousError(
                hashlib.sha256(response.content).hexdigest()
            ) from None
        try:
            decoded = response.json()
        except ValueError:
            raise CommandActivationAmbiguousError(
                hashlib.sha256(response.content).hexdigest()
            ) from None
        if not isinstance(decoded, dict):
            raise CommandActivationAmbiguousError(_digest(decoded))
        return decoded

    def _acknowledgement(
        self,
        operation: str,
        target_id: str,
        response: Mapping[str, Any],
    ) -> RuntimeCommandAcknowledgement:
        digest = _digest(response)
        return RuntimeCommandAcknowledgement(
            runtime_request_ref=f"freqtrade-{operation}-{target_id}-{digest[:16]}",
            response_digest=digest,
            acknowledged_at=self._clock(),
        )


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()
