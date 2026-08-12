from __future__ import annotations

import http.client
import json
from dataclasses import dataclass
from typing import Any, Protocol

from ai_platform.portal.runtime_gateway.errors import GatewayError, UpstreamError


_SENSITIVE_KEYS = frozenset(
    {"api_key", "apikey", "authorization", "credential", "password", "secret", "token"}
)


class FreqtradeUpstream(Protocol):
    def get(self, endpoint: str) -> Any: ...


@dataclass(frozen=True)
class LocalFreqtradeBinding:
    host: str
    port: int
    api_username: str
    api_password: str

    def __post_init__(self) -> None:
        if self.host not in {"127.0.0.1", "::1"}:
            raise GatewayError("ARBITRARY_UPSTREAM_FORBIDDEN", "upstream must be generation-local")
        if not 1 <= self.port <= 65535:
            raise GatewayError("INVALID_UPSTREAM", "invalid upstream port")
        if not self.api_username or not self.api_password:
            raise GatewayError("INVALID_UPSTREAM", "generation-local API material is required")


class LocalFreqtradeHttpClient:
    """Fixed-target, bounded Freqtrade client; callers cannot select methods or paths."""

    def __init__(
        self,
        binding: LocalFreqtradeBinding,
        *,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> None:
        self._binding = binding
        self._timeout = timeout_seconds
        self._max_response_bytes = max_response_bytes

    def get(self, endpoint: str) -> Any:
        if endpoint not in {
            "/api/v1/ping",
            "/api/v1/status",
            "/api/v1/trades",
        }:
            raise GatewayError("ARBITRARY_ENDPOINT_FORBIDDEN", "endpoint is not reviewed")
        connection = http.client.HTTPConnection(
            self._binding.host,
            self._binding.port,
            timeout=self._timeout,
        )
        headers = {
            "Accept": "application/json",
            "Authorization": _basic_auth(self._binding.api_username, self._binding.api_password),
        }
        try:
            connection.request("GET", endpoint, headers=headers)
            response = connection.getresponse()
            payload = response.read(self._max_response_bytes + 1)
        except (OSError, TimeoutError) as exc:
            raise UpstreamError(
                "UPSTREAM_UNAVAILABLE", "generation-local Freqtrade unavailable"
            ) from exc
        finally:
            connection.close()
        if len(payload) > self._max_response_bytes:
            raise UpstreamError("UPSTREAM_RESPONSE_TOO_LARGE", "Freqtrade response exceeds bound")
        if response.status != 200:
            raise UpstreamError("UPSTREAM_REJECTED", "Freqtrade rejected the bounded read")
        try:
            document = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise UpstreamError(
                "MALFORMED_UPSTREAM_RESPONSE", "Freqtrade returned invalid JSON"
            ) from exc
        _reject_sensitive(document)
        return document


def _basic_auth(username: str, password: str) -> str:
    import base64

    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


def _reject_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).casefold() in _SENSITIVE_KEYS:
                raise UpstreamError(
                    "CREDENTIAL_DISCLOSURE_BLOCKED", "sensitive upstream field blocked"
                )
            _reject_sensitive(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_sensitive(nested)
