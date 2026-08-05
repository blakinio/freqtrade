from __future__ import annotations

import base64
import hashlib
import ipaddress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlencode, urlparse

import httpx
import jwt

from ai_platform.portal.identity.schema import OidcIdentity


OIDC_HTTP_USER_AGENT = "Freqtrade-Portal-OIDC/1.0"
_MAX_ISSUER_LENGTH = 1024
_MAX_CLIENT_ID_LENGTH = 255
_MAX_LOGOUT_JTI_LENGTH = 255
_MAX_LOGOUT_IDENTITY_LENGTH = 512
_MAX_SIGNING_KEY_ID_LENGTH = 255
_MAX_SIGNING_ALGORITHM_LENGTH = 32
_DEFAULT_LOGOUT_MAX_TOKEN_AGE_SECONDS = 300
_DEFAULT_LOGOUT_CLOCK_SKEW_SECONDS = 60
_DEFAULT_LOGOUT_REPLAY_RETENTION_SECONDS = 900


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
    allow_insecure_local_http: bool = False
    logout_max_token_age_seconds: int = _DEFAULT_LOGOUT_MAX_TOKEN_AGE_SECONDS
    logout_clock_skew_seconds: int = _DEFAULT_LOGOUT_CLOCK_SKEW_SECONDS
    logout_replay_retention_seconds: int = _DEFAULT_LOGOUT_REPLAY_RETENTION_SECONDS
    require_logout_token_typ: bool = False

    def __post_init__(self) -> None:
        _validate_configured_url(
            self.issuer,
            label="OIDC issuer",
            allow_insecure_local_http=self.allow_insecure_local_http,
        )
        _validate_configured_url(
            self.redirect_uri,
            label="OIDC redirect URI",
            allow_insecure_local_http=self.allow_insecure_local_http,
        )
        if not self.client_id or not self.client_secret:
            raise ValueError("OIDC client credentials are required")
        if len(self.issuer) > _MAX_ISSUER_LENGTH:
            raise ValueError("OIDC issuer is too long")
        if len(self.client_id) > _MAX_CLIENT_ID_LENGTH:
            raise ValueError("OIDC client ID is too long")
        _validate_bounded_seconds(
            self.logout_max_token_age_seconds,
            label="OIDC logout maximum token age",
            minimum=1,
            maximum=3600,
        )
        _validate_bounded_seconds(
            self.logout_clock_skew_seconds,
            label="OIDC logout clock skew",
            minimum=0,
            maximum=300,
        )
        _validate_bounded_seconds(
            self.logout_replay_retention_seconds,
            label="OIDC logout replay retention",
            minimum=60,
            maximum=86400,
        )


@dataclass(frozen=True)
class OidcLogoutIdentity:
    issuer: str
    client_id: str
    jti: str
    issued_at: datetime
    expires_at: datetime
    retention_until: datetime
    token_type: str
    signing_key_id: str
    signing_algorithm: str
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
        self._http = http_client or httpx.Client(timeout=config.timeout_seconds, trust_env=False)
        self._discovery: dict[str, Any] | None = None
        self._jwks: dict[str, Any] | None = None

    @property
    def issuer(self) -> str:
        return self.config.issuer

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        discovery = self._get_discovery()
        endpoint = self._required_discovery_url(discovery, "authorization_endpoint")
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
        endpoint = self._required_discovery_url(discovery, "token_endpoint")
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
                headers=_json_headers(),
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcProviderUnavailable("OIDC token exchange failed") from exc
        id_token = payload.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise OidcProtocolError("OIDC token response did not contain an ID token")
        claims, _header = self._validate_jwt(
            id_token,
            require_nonce=True,
            require_subject=True,
            expected_nonce=expected_nonce,
            leeway_seconds=0,
        )
        return _identity_from_claims(self.issuer, claims)

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity:
        claims, header = self._validate_jwt(
            logout_token,
            require_nonce=False,
            require_subject=False,
            expected_nonce=None,
            leeway_seconds=self.config.logout_clock_skew_seconds,
        )
        events = claims.get("events")
        if not isinstance(events, dict) or (
            "http://schemas.openid.net/event/backchannel-logout" not in events
        ):
            raise OidcProtocolError("logout token is missing the back-channel logout event")
        if "nonce" in claims:
            raise OidcProtocolError("logout token must not contain nonce")
        jti = _required_bounded_claim(
            claims,
            "jti",
            maximum_length=_MAX_LOGOUT_JTI_LENGTH,
            label="logout token jti",
        )
        subject = _optional_bounded_claim(
            claims,
            "sub",
            maximum_length=_MAX_LOGOUT_IDENTITY_LENGTH,
            label="logout token subject",
        )
        sid = _optional_bounded_claim(
            claims,
            "sid",
            maximum_length=_MAX_LOGOUT_IDENTITY_LENGTH,
            label="logout token sid",
        )
        if subject is None and sid is None:
            raise OidcProtocolError("logout token must contain sub or sid")

        issued_at = _numeric_date(claims, "iat", label="logout token iat")
        expires_at = _numeric_date(claims, "exp", label="logout token exp")
        now = datetime.now(UTC)
        maximum_age = timedelta(seconds=self.config.logout_max_token_age_seconds)
        clock_skew = timedelta(seconds=self.config.logout_clock_skew_seconds)
        if expires_at <= issued_at:
            raise OidcProtocolError("logout token expiration must follow issuance")
        if expires_at - issued_at > maximum_age:
            raise OidcProtocolError("logout token lifetime exceeds policy")
        if issued_at > now + clock_skew:
            raise OidcProtocolError("logout token issuance is in the future")
        if now - issued_at > maximum_age + clock_skew:
            raise OidcProtocolError("logout token is older than policy allows")
        if expires_at < now - clock_skew:
            raise OidcProtocolError("logout token is expired")

        token_type = _logout_token_type(
            header,
            require_explicit=self.config.require_logout_token_typ,
        )
        signing_key_id = _required_bounded_header(
            header,
            "kid",
            maximum_length=_MAX_SIGNING_KEY_ID_LENGTH,
            label="logout token signing key ID",
        )
        signing_algorithm = _required_bounded_header(
            header,
            "alg",
            maximum_length=_MAX_SIGNING_ALGORITHM_LENGTH,
            label="logout token signing algorithm",
        )
        retention_until = expires_at + timedelta(
            seconds=self.config.logout_replay_retention_seconds
        )
        return OidcLogoutIdentity(
            issuer=self.issuer,
            client_id=self.config.client_id,
            jti=jti,
            issued_at=issued_at,
            expires_at=expires_at,
            retention_until=retention_until,
            token_type=token_type,
            signing_key_id=signing_key_id,
            signing_algorithm=signing_algorithm,
            subject=subject,
            idp_session_id=sid,
        )

    def _get_discovery(self) -> dict[str, Any]:
        if self._discovery is not None:
            return self._discovery
        url = f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"
        try:
            response = self._http.get(url, headers=_json_headers())
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcProviderUnavailable("OIDC discovery failed") from exc
        if payload.get("issuer") != self.issuer:
            raise OidcProtocolError("OIDC discovery issuer mismatch")
        self._discovery = payload
        return payload

    def _get_jwks(self) -> dict[str, Any]:
        if self._jwks is not None:
            return self._jwks
        discovery = self._get_discovery()
        url = self._required_discovery_url(discovery, "jwks_uri")
        try:
            response = self._http.get(url, headers=_json_headers())
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OidcProviderUnavailable("OIDC JWKS fetch failed") from exc
        if not isinstance(payload.get("keys"), list):
            raise OidcProtocolError("OIDC JWKS response is invalid")
        self._jwks = payload
        return payload

    def _required_discovery_url(self, payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str):
            raise OidcProtocolError(f"OIDC discovery {key} must be a URL")
        parsed = urlparse(value)
        if parsed.scheme == "https" and parsed.hostname:
            return value
        if not self.config.allow_insecure_local_http or parsed.scheme != "http":
            raise OidcProtocolError(f"OIDC discovery {key} must be an HTTPS URL")
        issuer = urlparse(self.issuer)
        if not _is_private_host(parsed.hostname):
            raise OidcProtocolError(f"OIDC discovery {key} must use a private host")
        if (parsed.hostname, parsed.port) != (issuer.hostname, issuer.port):
            raise OidcProtocolError(f"OIDC discovery {key} must use the issuer origin")
        return value

    def _validate_jwt(
        self,
        encoded: str,
        *,
        require_nonce: bool,
        require_subject: bool,
        expected_nonce: str | None,
        leeway_seconds: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
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
                leeway=leeway_seconds,
                options={"require": required},
            )
        except jwt.PyJWTError as exc:
            raise OidcProtocolError("OIDC JWT validation failed") from exc
        if require_nonce and claims.get("nonce") != expected_nonce:
            raise OidcProtocolError("OIDC nonce mismatch")
        return dict(claims), dict(header)


def _required_bounded_claim(
    claims: dict[str, Any],
    key: str,
    *,
    maximum_length: int,
    label: str,
) -> str:
    value = claims.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OidcProtocolError(f"{label} is required")
    if len(value) > maximum_length:
        raise OidcProtocolError(f"{label} is too long")
    return value


def _optional_bounded_claim(
    claims: dict[str, Any],
    key: str,
    *,
    maximum_length: int,
    label: str,
) -> str | None:
    value = claims.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise OidcProtocolError(f"{label} is invalid")
    if len(value) > maximum_length:
        raise OidcProtocolError(f"{label} is too long")
    return value


def _required_bounded_header(
    header: dict[str, Any],
    key: str,
    *,
    maximum_length: int,
    label: str,
) -> str:
    value = header.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OidcProtocolError(f"{label} is required")
    if len(value) > maximum_length:
        raise OidcProtocolError(f"{label} is too long")
    return value


def _logout_token_type(
    header: dict[str, Any],
    *,
    require_explicit: bool,
) -> str:
    value = header.get("typ")
    if value is None:
        if require_explicit:
            raise OidcProtocolError("logout token typ must be logout+jwt")
        return "untyped"
    if not isinstance(value, str):
        raise OidcProtocolError("logout token typ is invalid")
    normalized = value.lower()
    if normalized == "logout+jwt":
        return "logout+jwt"
    if normalized == "jwt" and not require_explicit:
        return "legacy+jwt"
    raise OidcProtocolError("logout token typ must be logout+jwt")


def _numeric_date(
    claims: dict[str, Any],
    key: str,
    *,
    label: str,
) -> datetime:
    value = claims.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise OidcProtocolError(f"{label} is invalid")
    try:
        return datetime.fromtimestamp(value, tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise OidcProtocolError(f"{label} is invalid") from exc


def _validate_bounded_seconds(
    value: int,
    *,
    label: str,
    minimum: int,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum} seconds")


def _json_headers() -> dict[str, str]:
    return {
        "accept": "application/json",
        "user-agent": OIDC_HTTP_USER_AGENT,
    }


def pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _validate_configured_url(
    value: str,
    *,
    label: str,
    allow_insecure_local_http: bool,
) -> None:
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.hostname:
        return
    if (
        allow_insecure_local_http
        and parsed.scheme == "http"
        and parsed.hostname
        and _is_private_host(parsed.hostname)
    ):
        return
    if allow_insecure_local_http:
        raise ValueError(f"{label} must use HTTPS or private local-test HTTP")
    raise ValueError(f"{label} must use HTTPS")


def _is_private_host(hostname: str | None) -> bool:
    if hostname is None:
        return False
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


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
