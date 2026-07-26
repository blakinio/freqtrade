from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx
import jwt

from ai_platform.portal.identity.schema import OidcIdentity


class OidcProtocolError(RuntimeError):
    pass


class OidcProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class OidcClientConfig:
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: tuple[str, ...] = ("openid", "profile", "email")
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if not self.issuer.startswith("https://"):
            raise ValueError("OIDC issuer must use HTTPS")
        if not self.redirect_uri.startswith("https://"):
            raise ValueError("OIDC redirect URI must use HTTPS")
        if not self.client_id or not self.client_secret:
            raise ValueError("OIDC client credentials are required")


@dataclass(frozen=True)
class OidcLogoutIdentity:
    issuer: str
    subject: str | None
    idp_session_id: str | None


class OidcClientProtocol(Protocol):
    @property
    def issuer(self) -> str: ...

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str: ...

    def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        expected_nonce: str,
    ) -> OidcIdentity: ...

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity: ...


class PyJwtOidcClient:
    def __init__(
        self,
        config: OidcClientConfig,
        *,
        http_client: httpx.Client | None = None,
    ):
        self.config = config
        self._http = http_client or httpx.Client(timeout=config.timeout_seconds)
        self._discovery: dict[str, Any] | None = None
        self._jwks: dict[str, Any] | None = None

    @property
    def issuer(self) -> str:
        return self.config.issuer.rstrip("/")

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        discovery = self._get_discovery()
        endpoint = _required_url(discovery, "authorization_endpoint")
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{endpoint}?{urlencode(params)}"

    def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        expected_nonce: str,
    ) -> OidcIdentity:
        discovery = self._get_discovery()
        endpoint = _required_url(discovery, "token_endpoint")
        try:
            response = self._http.post(
                endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.config.redirect_uri,
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code_verifier": code_verifier,
                },
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcProviderUnavailable("OIDC token exchange failed") from exc
        id_token = payload.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise OidcProtocolError("OIDC token response did not contain an ID token")
        claims = self._validate_jwt(
            id_token,
            require_nonce=True,
            require_subject=True,
            expected_nonce=expected_nonce,
        )
        return _identity_from_claims(self.issuer, claims)

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity:
        claims = self._validate_jwt(
            logout_token,
            require_nonce=False,
            require_subject=False,
            expected_nonce=None,
        )
        events = claims.get("events")
        if not isinstance(events, dict) or (
            "http://schemas.openid.net/event/backchannel-logout" not in events
        ):
            raise OidcProtocolError("logout token is missing the back-channel logout event")
        if "nonce" in claims:
            raise OidcProtocolError("logout token must not contain nonce")
        subject = claims.get("sub")
        sid = claims.get("sid")
        if not isinstance(subject, str):
            subject = None
        if not isinstance(sid, str):
            sid = None
        if subject is None and sid is None:
            raise OidcProtocolError("logout token must contain sub or sid")
        return OidcLogoutIdentity(
            issuer=self.issuer,
            subject=subject,
            idp_session_id=sid,
        )

    def _get_discovery(self) -> dict[str, Any]:
        if self._discovery is not None:
            return self._discovery
        url = f"{self.issuer}/.well-known/openid-configuration"
        try:
            response = self._http.get(url, headers={"accept": "application/json"})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcProviderUnavailable("OIDC discovery failed") from exc
        if payload.get("issuer", "").rstrip("/") != self.issuer:
            raise OidcProtocolError("OIDC discovery issuer mismatch")
        self._discovery = payload
        return payload

    def _get_jwks(self) -> dict[str, Any]:
        if self._jwks is not None:
            return self._jwks
        discovery = self._get_discovery()
        url = _required_url(discovery, "jwks_uri")
        try:
            response = self._http.get(url, headers={"accept": "application/json"})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcProviderUnavailable("OIDC JWKS fetch failed") from exc
        if not isinstance(payload.get("keys"), list):
            raise OidcProtocolError("OIDC JWKS response is invalid")
        self._jwks = payload
        return payload

    def _validate_jwt(
        self,
        encoded: str,
        *,
        require_nonce: bool,
        require_subject: bool,
        expected_nonce: str | None,
    ) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(encoded)
        except jwt.PyJWTError as exc:
            raise OidcProtocolError("OIDC JWT header is invalid") from exc
        kid = header.get("kid")
        algorithm = header.get("alg")
        if not isinstance(kid, str) or not isinstance(algorithm, str) or algorithm == "none":
            raise OidcProtocolError("OIDC JWT must use a keyed signed algorithm")
        jwk = next(
            (
                item
                for item in self._get_jwks()["keys"]
                if isinstance(item, dict) and item.get("kid") == kid
            ),
            None,
        )
        if jwk is None:
            self._jwks = None
            jwk = next(
                (
                    item
                    for item in self._get_jwks()["keys"]
                    if isinstance(item, dict) and item.get("kid") == kid
                ),
                None,
            )
        if jwk is None:
            raise OidcProtocolError("OIDC signing key is unavailable")
        try:
            key = jwt.PyJWK.from_dict(jwk).key
            required = ["exp", "iat", "iss", "aud"]
            if require_subject:
                required.append("sub")
            if require_nonce:
                required.append("nonce")
            claims = jwt.decode(
                encoded,
                key=key,
                algorithms=[algorithm],
                audience=self.config.client_id,
                issuer=self.issuer,
                options={"require": required},
            )
        except jwt.PyJWTError as exc:
            raise OidcProtocolError("OIDC JWT validation failed") from exc
        if require_nonce and claims.get("nonce") != expected_nonce:
            raise OidcProtocolError("OIDC nonce mismatch")
        return dict(claims)


def pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _required_url(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.startswith("https://"):
        raise OidcProtocolError(f"OIDC discovery {key} must be an HTTPS URL")
    return value


def _identity_from_claims(issuer: str, claims: dict[str, Any]) -> OidcIdentity:
    subject = claims["sub"]
    if not isinstance(subject, str) or not subject:
        raise OidcProtocolError("OIDC subject is invalid")
    display_name = claims.get("name") or claims.get("preferred_username") or subject
    if not isinstance(display_name, str) or not display_name:
        display_name = subject
    email = claims.get("email")
    if not isinstance(email, str):
        email = None
    sid = claims.get("sid")
    if not isinstance(sid, str):
        sid = None
    auth_time_value = claims.get("auth_time", claims.get("iat"))
    if not isinstance(auth_time_value, int | float):
        raise OidcProtocolError("OIDC authentication time is invalid")
    methods = claims.get("amr", ())
    if not isinstance(methods, list):
        methods = []
    normalized_methods = tuple(
        sorted({item.lower() for item in methods if isinstance(item, str) and item})
    )
    acr = claims.get("acr")
    mfa_markers = {"mfa", "otp", "totp", "webauthn", "fido", "hwk"}
    mfa_satisfied = bool(mfa_markers.intersection(normalized_methods))
    if isinstance(acr, str) and any(marker in acr.lower() for marker in ("mfa", "2fa", "webauthn")):
        mfa_satisfied = True
    return OidcIdentity(
        issuer=issuer,
        subject=subject,
        display_name=display_name,
        email=email,
        idp_session_id=sid,
        authentication_time=datetime.fromtimestamp(auth_time_value, tz=UTC),
        mfa_satisfied=mfa_satisfied,
        authentication_methods=normalized_methods,
    )
