from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from ai_platform.portal.identity.oidc import OidcClientConfig, PyJwtOidcClient


ISSUER = "https://identity.example.test/application/o/portal/"
CLIENT_ID = "portal-client"
REDIRECT_URI = "https://portal.example.test/api/identity/callback"


def _b64(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(length, "big")).rstrip(b"=").decode()


def test_trailing_slash_issuer_is_preserved_for_jwt_and_identity() -> None:
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
    discovery = {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}authorize",
        "token_endpoint": f"{ISSUER}token",
        "jwks_uri": f"{ISSUER}jwks",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/.well-known/openid-configuration"):
            assert "//.well-known/" not in str(request.url)
            return httpx.Response(200, json=discovery)
        if request.url.path.endswith("/jwks"):
            return httpx.Response(200, json={"keys": [jwk]})
        if request.url.path.endswith("/token"):
            form = parse_qs(request.content.decode())
            assert form["code_verifier"] == ["v" * 64]
            now = datetime.now(UTC)
            token = jwt.encode(
                {
                    "iss": ISSUER,
                    "sub": "user-1",
                    "aud": CLIENT_ID,
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(minutes=5)).timestamp()),
                    "auth_time": int(now.timestamp()),
                    "nonce": "nonce-1",
                    "sid": "sid-1",
                    "name": "Portal User",
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
