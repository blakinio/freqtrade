from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.http import create_identity_enabled_app
from ai_platform.portal.identity.oidc import OidcLogoutIdentity
from ai_platform.portal.identity.schema import OidcIdentity
from ai_platform.portal.identity.service import (
    CSRF_COOKIE_NAME,
    IdentityPolicy,
    IdentityService,
)


@dataclass
class MutableClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value

    def advance(self, delta: timedelta) -> None:
        self.value += delta


class FakeOidcClient:
    issuer = "https://identity.example.test/application/o/portal"

    def __init__(self, clock: MutableClock):
        self.clock = clock
        self.subject = "user-1"
        self.sid = "sid-1"
        self.mfa = True
        self.last_nonce: str | None = None

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        self.last_nonce = nonce
        return "https://identity.example.test/authorize?" + urlencode(
            {
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )

    def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        expected_nonce: str,
    ) -> OidcIdentity:
        assert code == "valid-code"
        assert len(code_verifier) >= 43
        assert expected_nonce == self.last_nonce
        return OidcIdentity(
            issuer=self.issuer,
            subject=self.subject,
            display_name="Portal User",
            email="portal@example.test",
            idp_session_id=self.sid,
            authentication_time=self.clock(),
            mfa_satisfied=self.mfa,
            authentication_methods=("webauthn",),
        )

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity:
        assert logout_token == "valid-logout-token"
        return OidcLogoutIdentity(
            issuer=self.issuer,
            subject=self.subject,
            idp_session_id=self.sid,
        )


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock(datetime(2026, 7, 26, 8, 0, tzinfo=UTC))


@pytest.fixture
def identity(
    session_factory: SessionFactory,
    clock: MutableClock,
) -> tuple[IdentityService, FakeOidcClient]:
    oidc = FakeOidcClient(clock)
    crypto = IdentityCrypto(
        IdentitySecrets(
            session_hmac_key=b"s" * 32,
            flow_encryption_key=b"f" * 32,
        )
    )
    service = IdentityService(
        session_factory,
        oidc,
        crypto,
        policy=IdentityPolicy(),
        clock=clock,
    )
    principal = service.bootstrap_principal(
        issuer=oidc.issuer,
        subject=oidc.subject,
        display_name="Portal User",
        email="portal@example.test",
    )
    service.bootstrap_membership(
        principal_id=principal.principal_id,
        tenant_id="tenant-a",
        roles=(RoleName.ADMIN,),
    )
    return service, oidc


def _login(client: TestClient, tenant_id: str = "tenant-a") -> str:
    login = client.get(
        "/v1/identity/login",
        params={"tenant_id": tenant_id, "return_to": "/bots"},
        follow_redirects=False,
    )
    assert login.status_code == 307
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    callback = client.get(
        "/v1/identity/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 303
    assert callback.headers["location"] == "/bots"
    csrf = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf
    return csrf


def test_identity_app_rejects_missing_session_and_protects_all_mutations(
    session_factory: SessionFactory,
    identity: tuple[IdentityService, FakeOidcClient],
) -> None:
    service, _ = identity
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )

    assert client.get("/v1/bots").status_code == 401
    csrf = _login(client)
    assert client.get("/v1/identity/session").json()["tenant_id"] == "tenant-a"

    missing_csrf = client.post("/v1/bots", json={})
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["detail"] == "CSRF token is missing"

    invalid_payload = client.post(
        "/v1/bots",
        json={},
        headers={"x-csrf-token": csrf},
    )
    assert invalid_payload.status_code == 422


def test_login_state_is_single_use(
    session_factory: SessionFactory,
    identity: tuple[IdentityService, FakeOidcClient],
) -> None:
    service, _ = identity
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )
    login = client.get("/v1/identity/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    first = client.get(
        "/v1/identity/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )
    second = client.get(
        "/v1/identity/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert first.status_code == 303
    assert second.status_code == 401
    assert "invalid or expired" in second.json()["detail"]


def test_membership_role_change_revokes_existing_session(
    session_factory: SessionFactory,
    identity: tuple[IdentityService, FakeOidcClient],
) -> None:
    service, _ = identity
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )
    csrf = _login(client)
    current = client.get("/v1/identity/session").json()

    changed = client.put(
        f"/v1/identity/memberships/{current['membership_id']}/roles",
        json={"roles": ["user"]},
        headers={"x-csrf-token": csrf},
    )
    assert changed.status_code == 200
    assert changed.json()["membership_version"] == 2
    assert client.get("/v1/bots").status_code == 401


def test_idle_expiry_and_backchannel_logout_fail_closed(
    session_factory: SessionFactory,
    identity: tuple[IdentityService, FakeOidcClient],
    clock: MutableClock,
) -> None:
    service, _ = identity
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )
    _login(client)
    clock.advance(timedelta(minutes=16))
    assert client.get("/v1/bots").status_code == 401

    client.cookies.clear()
    _login(client)
    response = client.post(
        "/v1/identity/backchannel-logout",
        content="logout_token=valid-logout-token",
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert response.json()["revoked_sessions"] == 1
    assert client.get("/v1/bots").status_code == 401


def test_privileged_membership_requires_mfa(
    session_factory: SessionFactory,
    identity: tuple[IdentityService, FakeOidcClient],
) -> None:
    service, oidc = identity
    oidc.mfa = False
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )
    login = client.get("/v1/identity/login", follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]

    response = client.get(
        "/v1/identity/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "MFA is required for this membership"


def test_open_redirect_is_rejected(
    session_factory: SessionFactory,
    identity: tuple[IdentityService, FakeOidcClient],
) -> None:
    service, _ = identity
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )

    response = client.get(
        "/v1/identity/login",
        params={"return_to": "https://evil.example"},
        follow_redirects=False,
    )

    assert response.status_code == 422
