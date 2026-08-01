from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from ai_platform.portal.identity.oidc import (
    OidcClientConfig,
    OidcProtocolError,
    PyJwtOidcClient,
)


ISSUER = "https://identity.example.test/application/o/portal/"
CLIENT_ID = "portal-client"
REDIRECT_URI = "https://portal.example.test/api/identity/callback"


def _b64(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(length, "big")).rstrip(b"=").decode()


def test_authentik_trailing_slash_issuer_is_preserved_for_id_token_validation() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = key.public_key().public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": "key-1",
        "alg": "RS256",
        "use": "sig",
        "n": _b64(public.n),
        "e": _b64(public.e),
    }
    root = ISSUER.rstrip("/")
    discovery = {
        "issuer": ISSUER,
        "authorization_endpoint": f"{root}/authorize",
        "token_endpoint": f"{root}/token",
        "jwks_uri": f"{root}/jwks",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/.well-known/openid-configuration"):
            assert "//.well-known" not in str(request.url)
            return httpx.Response(200, json=discovery)
        if request.url.path.endswith("/jwks"):
            return httpx.Response(200, json={"keys": [jwk]})
        if request.url.path.endswith("/token"):
            now = datetime.now(UTC)
            verifier = parse_qs(request.content.decode())["code_verifier"][0]
            assert len(verifier) >= 43
            token = jwt.encode(
                {
                    "iss": ISSUER,
                    "sub": "user-1",
                    "aud": CLIENT_ID,
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(minutes=5)).timestamp()),
                    "auth_time": int(now.timestamp()),
                    "nonce": "nonce-1",
                    "amr": ["pwd", "totp"],
                },
                key,
                algorithm="RS256",
                headers={"kid": "key-1"},
            )
            return httpx.Response(200, json={"id_token": token})
        raise AssertionError(f"unexpected request: {request.url}")

    client = PyJwtOidcClient(
        OidcClientConfig(
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret="secret",
            redirect_uri=REDIRECT_URI,
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    identity = client.exchange_code(
        code="code-1",
        code_verifier="v" * 64,
        expected_nonce="nonce-1",
    )

    assert client.issuer == ISSUER
    assert identity.issuer == ISSUER
    assert identity.subject == "user-1"
    assert identity.mfa_satisfied is True


def test_discovery_issuer_must_match_trailing_slash_exactly() -> None:
    root = ISSUER.rstrip("/")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "issuer": root,
                "authorization_endpoint": f"{root}/authorize",
                "token_endpoint": f"{root}/token",
                "jwks_uri": f"{root}/jwks",
            },
        )

    client = PyJwtOidcClient(
        OidcClientConfig(
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret="secret",
            redirect_uri=REDIRECT_URI,
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OidcProtocolError, match="issuer mismatch"):
        client.authorization_url(state="state-1", nonce="nonce-1", code_challenge="challenge-1")
