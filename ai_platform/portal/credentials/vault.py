from __future__ import annotations

import ipaddress
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, Self
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator

from ai_platform.portal.contracts.bot_management.exchange_connections import CredentialReference
from ai_platform.portal.contracts.common import NonEmptyStr, UtcDateTime
from ai_platform.portal.credentials.errors import (
    CredentialUnavailableError,
    VaultAuthenticationError,
    VaultProtocolError,
    VaultTransportError,
)


Clock = Callable[[], datetime]


class VaultHttpTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]: ...


def validate_private_https_endpoint(
    endpoint: str,
    *,
    allowed_hosts: tuple[str, ...] = (),
) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.hostname:
        raise VaultProtocolError("VAULT_TLS_PRIVATE_ENDPOINT_REQUIRED")
    if parsed.username is not None or parsed.password is not None:
        raise VaultProtocolError("VAULT_ENDPOINT_EMBEDS_CREDENTIALS")
    if parsed.query or parsed.fragment:
        raise VaultProtocolError("VAULT_ENDPOINT_MUST_NOT_HAVE_QUERY_OR_FRAGMENT")
    if parsed.path not in {"", "/"}:
        raise VaultProtocolError("VAULT_ENDPOINT_MUST_NOT_HAVE_PATH")

    hostname = parsed.hostname.lower().rstrip(".")
    normalized_allowed = {value.lower().rstrip(".") for value in allowed_hosts}
    private_hostname = (
        hostname in normalized_allowed
        or "." not in hostname
        or hostname.endswith((".internal", ".local", ".lan"))
    )
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        private_hostname = address.is_private or address.is_loopback or address.is_link_local
    if not private_hostname:
        raise VaultProtocolError("VAULT_ENDPOINT_MUST_BE_PRIVATE")

    port = parsed.port
    authority = hostname if port is None else f"{hostname}:{port}"
    return f"https://{authority}"


class HttpxVaultTransport:
    def __init__(
        self,
        endpoint: str,
        ca_certificate_path: Path,
        *,
        allowed_hosts: tuple[str, ...] = (),
        timeout_seconds: float = 5.0,
        max_body_bytes: int = 1_048_576,
        client: httpx.Client | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Vault timeout must be positive")
        if max_body_bytes < 1:
            raise ValueError("Vault response limit must be positive")
        if not ca_certificate_path.is_file():
            raise VaultProtocolError("VAULT_CA_CERTIFICATE_UNAVAILABLE")
        self._endpoint = validate_private_https_endpoint(
            endpoint,
            allowed_hosts=allowed_hosts,
        )
        self._max_body_bytes = max_body_bytes
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self._endpoint,
            verify=str(ca_certificate_path),
            timeout=timeout_seconds,
            follow_redirects=False,
            trust_env=False,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if not path.startswith("/v1/"):
            raise VaultProtocolError("VAULT_API_PATH_INVALID")
        headers = {"Accept": "application/json"}
        if token is not None:
            headers["X-Vault-Token"] = token
        try:
            response = self._client.request(
                method,
                path,
                headers=headers,
                json=dict(payload) if payload is not None else None,
            )
        except (httpx.TimeoutException, httpx.NetworkError):
            raise VaultTransportError() from None

        if 300 <= response.status_code < 400:
            raise VaultProtocolError("VAULT_REDIRECT_REJECTED")
        if response.status_code in {401, 403}:
            raise VaultAuthenticationError() from None
        if response.status_code == 404:
            raise CredentialUnavailableError("CREDENTIAL_REFERENCE_NOT_FOUND") from None
        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            raise VaultTransportError() from None
        if response.status_code >= 400:
            raise VaultProtocolError("VAULT_REQUEST_REJECTED")
        if len(response.content) > self._max_body_bytes:
            raise VaultProtocolError("VAULT_RESPONSE_TOO_LARGE")
        try:
            decoded = response.json()
        except ValueError:
            raise VaultProtocolError("VAULT_RESPONSE_NOT_JSON") from None
        if not isinstance(decoded, Mapping):
            raise VaultProtocolError("VAULT_RESPONSE_SHAPE_INVALID")
        return decoded

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> HttpxVaultTransport:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


@dataclass(frozen=True)
class VaultAppRoleConfig:
    role_id_path: Path
    secret_id_path: Path
    kv_mount: str = "portal-secrets"
    auth_mount: str = "approle"
    maximum_token_ttl: timedelta = timedelta(minutes=15)

    def __post_init__(self) -> None:
        for value, name in (
            (self.kv_mount, "kv_mount"),
            (self.auth_mount, "auth_mount"),
        ):
            if not value or "/" in value or value in {".", ".."}:
                raise ValueError(f"{name} must be one safe Vault mount segment")
        if self.maximum_token_ttl <= timedelta(0):
            raise ValueError("maximum_token_ttl must be positive")


@dataclass
class _VaultToken:
    value: bytearray = field(repr=False)
    expires_at: datetime

    def text(self) -> str:
        return bytes(self.value).decode("utf-8")

    def clear(self) -> None:
        for index in range(len(self.value)):
            self.value[index] = 0


class VaultCredentialDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    tenant_id: NonEmptyStr
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    exchange_api_key: SecretStr
    exchange_api_secret: SecretStr
    exchange_passphrase: SecretStr | None = None
    runtime_api_username: SecretStr
    runtime_api_password: SecretStr
    withdrawals_enabled: bool
    dry_run_only: bool
    rotated_at: UtcDateTime
    revoked: bool = False

    @model_validator(mode="after")
    def validate_secret_values(self) -> Self:
        required = (
            self.exchange_api_key,
            self.exchange_api_secret,
            self.runtime_api_username,
            self.runtime_api_password,
        )
        if any(not value.get_secret_value().strip() for value in required):
            raise ValueError("credential secret values must not be empty")
        if self.exchange_passphrase is not None:
            if not self.exchange_passphrase.get_secret_value().strip():
                raise ValueError("exchange passphrase must not be empty")
        return self


@dataclass(frozen=True)
class VaultCredentialRecord:
    document: VaultCredentialDocument
    version: int


class VaultAppRoleClient:
    def __init__(
        self,
        transport: VaultHttpTransport,
        config: VaultAppRoleConfig,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._transport = transport
        self._config = config
        self._clock = clock or (lambda: datetime.now(UTC))
        self._token: _VaultToken | None = None

    def read_credential(self, secret_path: str) -> VaultCredentialRecord:
        response = self._transport.request(
            "GET",
            f"/v1/{self._config.kv_mount}/data/{secret_path}",
            token=self._token_text(),
        )
        outer_data = self._mapping(response.get("data"), "VAULT_KV_RESPONSE_INVALID")
        secret_data = self._mapping(
            outer_data.get("data"),
            "VAULT_KV_SECRET_DATA_INVALID",
        )
        metadata = self._mapping(
            outer_data.get("metadata"),
            "VAULT_KV_SECRET_METADATA_INVALID",
        )
        version = metadata.get("version")
        if not isinstance(version, int) or version < 1:
            raise VaultProtocolError("VAULT_KV_VERSION_INVALID")
        try:
            document = VaultCredentialDocument.model_validate(secret_data)
        except ValueError:
            raise VaultProtocolError("VAULT_CREDENTIAL_DOCUMENT_INVALID") from None
        return VaultCredentialRecord(document=document, version=version)

    def read_metadata(self, secret_path: str) -> Mapping[str, Any]:
        response = self._transport.request(
            "GET",
            f"/v1/{self._config.kv_mount}/metadata/{secret_path}",
            token=self._token_text(),
        )
        return self._mapping(response.get("data"), "VAULT_KV_METADATA_INVALID")

    def close(self) -> None:
        if self._token is not None:
            self._token.clear()
            self._token = None

    def _token_text(self) -> str:
        now = self._clock()
        if self._token is None or self._token.expires_at - now <= timedelta(seconds=30):
            self._login(now)
        if self._token is None:
            raise VaultAuthenticationError()
        return self._token.text()

    def _login(self, now: datetime) -> None:
        role_id = self._read_secret_file(self._config.role_id_path)
        secret_id = self._read_secret_file(self._config.secret_id_path)
        try:
            response = self._transport.request(
                "POST",
                f"/v1/auth/{self._config.auth_mount}/login",
                payload={"role_id": role_id, "secret_id": secret_id},
            )
        finally:
            role_id = ""
            secret_id = ""
        auth = self._mapping(response.get("auth"), "VAULT_AUTH_RESPONSE_INVALID")
        token = auth.get("client_token")
        lease_duration = auth.get("lease_duration")
        if not isinstance(token, str) or not token.strip():
            raise VaultAuthenticationError()
        if not isinstance(lease_duration, int) or lease_duration < 1:
            raise VaultAuthenticationError()
        lease = timedelta(seconds=lease_duration)
        if lease > self._config.maximum_token_ttl:
            raise VaultProtocolError("VAULT_TOKEN_TTL_EXCEEDS_POLICY")
        if self._token is not None:
            self._token.clear()
        self._token = _VaultToken(
            value=bytearray(token.encode("utf-8")),
            expires_at=now + lease,
        )

    @staticmethod
    def _read_secret_file(path: Path) -> str:
        if not path.is_file():
            raise VaultAuthenticationError()
        if path.stat().st_size > 4096:
            raise VaultAuthenticationError()
        value = path.read_text(encoding="utf-8").strip()
        if not value:
            raise VaultAuthenticationError()
        return value

    @staticmethod
    def _mapping(value: object, reason_code: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise VaultProtocolError(reason_code)
        return value

    def __enter__(self) -> VaultAppRoleClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
