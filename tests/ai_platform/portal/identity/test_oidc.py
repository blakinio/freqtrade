from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from ai_platform.portal.identity.oidc import (
    OidcClientConfig,
    OidcProtocolError,
    PyJwtOidcClient,
)


ISSUER = "https://identity.example.test/application/o/portal"
CLIENT_ID = "portal-client"
REDIRECT_URI = "https://portal.example.test/v1/identity/callback"


def _b64(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(length, "big")).rstrip(b"=").decode()


def _client() -> tuple[PyJwtOidcClient, rsa.RSAPrivateKey]:
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
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/.well-known/openid-configuration"):
            return httpx.Response(200, json=discovery)
        if request.url.path.endswith("/jwks"):
            return httpx.Response(200, json={"keys": [jwk]})
        if request.url.path.endswith("/token"):
            now = datetime.now(UTC)
            body = request.content.decode()
            verifier = parse_qs(body)["code_verifier"][0]
            nonce = "nonce-1"
            assert len(verifier) >= 43
            token = jwt.encode(
                {
                    "iss": ISSUER,
                    "sub": "user-1",
                    "aud": CLIENT_ID,
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(minutes=5)).timestamp()),
                    "auth_time": int(now.timestamp()),
                    "nonce": nonce,
                    "sid": "sid-1",
                    "name": "Portal User",
                    "email": "portal@example.test",
                    "amr": ["pwd", "webauthn"],
                },
                key,
                algorithm="RS256",
                headers={"kid": "key-1"},
            )
            return httpx.Response(200, json={"id_token": token})
        raise AssertionError(f"unexpected request: {request.url}")

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = PyJwtOidcClient(
        OidcClientConfig(
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret="secret",
            redirect_uri=REDIRECT_URI,
        ),
        http_client=http,
    )
    return client, key


def test_authorization_and_token_validation_use_pkce_nonce_issuer_and_audience() -> None:
    client, _ = _client()
    authorization_url = client.authorization_url(
        state="state-1",
        nonce="nonce-1",
        code_challenge="challenge-1",
    )
    query = parse_qs(urlparse(authorization_url).query)

    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == ["state-1"]
    identity = client.exchange_code(
        code="code-1",
        code_verifier="v" * 64,
        expected_nonce="nonce-1",
    )
    assert identity.subject == "user-1"
    assert identity.mfa_satisfied is True
    assert identity.idp_session_id == "sid-1"


def test_nonce_mismatch_is_rejected() -> None:
    client, _ = _client()

    with pytest.raises(OidcProtocolError, match="nonce mismatch"):
        client.exchange_code(
            code="code-1",
            code_verifier="v" * 64,
            expected_nonce="wrong",
        )


def test_backchannel_logout_requires_event_and_sub_or_sid() -> None:
    client, key = _client()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "iss": ISSUER,
            "sub": "user-1",
            "sid": "sid-1",
            "aud": CLIENT_ID,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "jti": "logout-1",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        },
        key,
        algorithm="RS256",
        headers={"kid": "key-1"},
    )

    result = client.validate_backchannel_logout(token)

    assert result.subject == "user-1"
    assert result.idp_session_id == "sid-1"


def test_discovery_issuer_mismatch_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(
                {
                    "issuer": "https://wrong.example",
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": f"{ISSUER}/jwks",
                }
            ),
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
        client.authorization_url(state="s", nonce="n", code_challenge="c")
