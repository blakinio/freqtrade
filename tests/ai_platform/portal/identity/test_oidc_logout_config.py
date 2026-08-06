from __future__ import annotations

import pytest

from ai_platform.portal.identity.oidc import OidcClientConfig


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
