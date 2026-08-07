from __future__ import annotations

import base64
from typing import Any, cast

import pytest

from ai_platform.portal.identity.oidc import OidcClientConfig
from ai_platform.portal.identity.runtime import (
    IdentityConfigurationError,
    IdentityRuntimeConfig,
    build_identity_service,
)


def _set_required_identity_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    encoded_key = base64.urlsafe_b64encode(b"x" * 32).decode("ascii")
    monkeypatch.setenv(
        "PORTAL_IDENTITY_ISSUER",
        "https://identity.example.test/application/o/portal",
    )
    monkeypatch.setenv("PORTAL_IDENTITY_CLIENT_ID", "portal-client")
    monkeypatch.setenv("PORTAL_IDENTITY_CLIENT_SECRET", "synthetic-secret")
    monkeypatch.setenv(
        "PORTAL_IDENTITY_REDIRECT_URI",
        "https://portal.example.test/v1/identity/callback",
    )
    monkeypatch.setenv("PORTAL_IDENTITY_SESSION_HMAC_KEY_B64", encoded_key)
    monkeypatch.setenv("PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64", encoded_key)


def test_logout_replay_retention_must_cover_clock_skew() -> None:
    with pytest.raises(ValueError, match="replay retention must cover clock skew"):
        OidcClientConfig(
            issuer="https://identity.example.test/application/o/portal",
            client_id="portal-client",
            client_secret="secret",
            redirect_uri="https://portal.example.test/v1/identity/callback",
            logout_clock_skew_seconds=61,
            logout_replay_retention_seconds=60,
        )


def test_runtime_exposes_strict_logout_token_type_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_identity_environment(monkeypatch)
    monkeypatch.setenv("PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP", "true")

    config = IdentityRuntimeConfig.from_environment()
    service = build_identity_service(cast(Any, lambda: None), config)

    assert config.require_logout_token_typ is True
    assert service._oidc.config.require_logout_token_typ is True


def test_runtime_defaults_logout_token_type_policy_to_compatibility_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_identity_environment(monkeypatch)
    monkeypatch.delenv("PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP", raising=False)

    config = IdentityRuntimeConfig.from_environment()

    assert config.require_logout_token_typ is False


def test_runtime_rejects_invalid_logout_token_type_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_identity_environment(monkeypatch)
    monkeypatch.setenv("PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP", "sometimes")

    with pytest.raises(
        IdentityConfigurationError,
        match="PORTAL_IDENTITY_REQUIRE_LOGOUT_TOKEN_TYP must be true, false, 1, or 0",
    ):
        IdentityRuntimeConfig.from_environment()
