from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Literal

from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.oidc import OidcClientConfig, PyJwtOidcClient
from ai_platform.portal.identity.service import IdentityService


class IdentityConfigurationError(RuntimeError):
    pass


IdentityTransportMode = Literal["secure_https", "local_http_test"]


@dataclass(frozen=True)
class IdentityRuntimeConfig:
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    session_hmac_key: bytes
    flow_encryption_key: bytes
    transport_mode: IdentityTransportMode = "secure_https"

    @property
    def allow_insecure_local_http(self) -> bool:
        return self.transport_mode == "local_http_test"

    @classmethod
    def from_environment(cls) -> IdentityRuntimeConfig:
        transport_mode = _transport_mode()
        if transport_mode == "local_http_test" and os.environ.get("PORTAL_ENVIRONMENT") != "test":
            raise IdentityConfigurationError(
                "local_http_test identity transport requires PORTAL_ENVIRONMENT=test"
            )
        return cls(
            issuer=_required("PORTAL_IDENTITY_ISSUER"),
            client_id=_required("PORTAL_IDENTITY_CLIENT_ID"),
            client_secret=_required("PORTAL_IDENTITY_CLIENT_SECRET"),
            redirect_uri=_required("PORTAL_IDENTITY_REDIRECT_URI"),
            session_hmac_key=_decode_secret(_required("PORTAL_IDENTITY_SESSION_HMAC_KEY_B64")),
            flow_encryption_key=_decode_secret(
                _required("PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64")
            ),
            transport_mode=transport_mode,
        )


def build_identity_service(
    session_factory: SessionFactory,
    config: IdentityRuntimeConfig,
) -> IdentityService:
    oidc = PyJwtOidcClient(
        OidcClientConfig(
            issuer=config.issuer,
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            allow_insecure_local_http=config.allow_insecure_local_http,
        )
    )
    crypto = IdentityCrypto(
        IdentitySecrets(
            session_hmac_key=config.session_hmac_key,
            flow_encryption_key=config.flow_encryption_key,
        )
    )
    return IdentityService(session_factory, oidc, crypto)


def _transport_mode() -> IdentityTransportMode:
    value = os.environ.get("PORTAL_IDENTITY_TRANSPORT_MODE", "secure_https").strip()
    if value not in {"secure_https", "local_http_test"}:
        raise IdentityConfigurationError(
            "PORTAL_IDENTITY_TRANSPORT_MODE must be secure_https or local_http_test"
        )
    return value  # type: ignore[return-value]


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise IdentityConfigurationError(f"required identity setting is missing: {name}")
    return value


def _decode_secret(value: str) -> bytes:
    try:
        padded = value + ("=" * (-len(value) % 4))
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise IdentityConfigurationError("identity secret must be URL-safe base64") from exc
    if len(decoded) < 32:
        raise IdentityConfigurationError("identity secret must decode to at least 32 bytes")
    return decoded
