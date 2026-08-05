from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.http import create_identity_enabled_app
from ai_platform.portal.identity.models import (
    IdentityAuditEventRow,
    OidcLogoutReplayRow,
    SessionRevocationRow,
)
from ai_platform.portal.identity.oidc import OidcLogoutIdentity, OidcProtocolError
from ai_platform.portal.identity.repository import (
    IdentityReplayConflictError,
    IdentityRepository,
)
from ai_platform.portal.identity.schema import OidcIdentity
from ai_platform.portal.identity.service import IdentityService


ISSUER = "https://identity.example.test/application/o/portal"
CLIENT_ID = "portal-client"


@dataclass
class MutableClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class ReplayOidcClient:
    issuer = ISSUER

    def __init__(self) -> None:
        self.logout_identity = OidcLogoutIdentity(
            issuer=ISSUER,
            subject="user-1",
            idp_session_id="sid-1",
            client_id=CLIENT_ID,
            jti="logout-1",
        )

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        raise AssertionError((state, nonce, code_challenge))

    def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        expected_nonce: str,
    ) -> OidcIdentity:
        raise AssertionError((code, code_verifier, expected_nonce))

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity:
        if logout_token != "valid-logout-token":
            raise OidcProtocolError("synthetic invalid logout token")
        return self.logout_identity


def _service(
    database_path: Path,
    oidc: ReplayOidcClient,
    clock: MutableClock,
) -> tuple[IdentityService, Engine]:
    engine = build_engine(f"sqlite+pysqlite:///{database_path}")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    service = IdentityService(
        session_factory,
        oidc,
        IdentityCrypto(
            IdentitySecrets(
                session_hmac_key=b"s" * 32,
                flow_encryption_key=b"f" * 32,
            )
        ),
        clock=clock,
    )
    return service, engine


def _seed_active_session(service: IdentityService, now: datetime) -> None:
    principal = service.bootstrap_principal(
        issuer=ISSUER,
        subject="user-1",
        display_name="Portal User",
        email="portal@example.test",
    )
    membership = service.bootstrap_membership(
        principal_id=principal.principal_id,
        tenant_id="tenant-a",
        roles=(RoleName.ADMIN,),
    )
    with service._session_factory() as session:
        IdentityRepository(session).create_session(
            session_id_hash="session-hash",
            csrf_token_hash="csrf-hash",
            principal_id=principal.principal_id,
            membership_id=membership.membership_id,
            membership_version=membership.membership_version,
            idp_session_id="sid-1",
            authentication_time=now,
            mfa_satisfied=True,
            created_at=now,
            idle_expires_at=now + timedelta(minutes=15),
            absolute_expires_at=now + timedelta(hours=4),
        )
        session.commit()


def _counts(service: IdentityService) -> tuple[int, int, int]:
    with service._session_factory() as session:
        return (
            int(session.scalar(select(func.count()).select_from(OidcLogoutReplayRow)) or 0),
            int(session.scalar(select(func.count()).select_from(SessionRevocationRow)) or 0),
            int(
                session.scalar(
                    select(func.count())
                    .select_from(IdentityAuditEventRow)
                    .where(IdentityAuditEventRow.action == "identity.backchannel_logout")
                )
                or 0
            ),
        )


def test_exact_logout_replay_returns_original_result_without_second_mutation(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient()
    service, engine = _service(tmp_path / "replay.db", oidc, clock)
    try:
        _seed_active_session(service, now)

        first = service.handle_backchannel_logout("valid-logout-token")
        clock.value += timedelta(minutes=5)
        replay = service.handle_backchannel_logout("valid-logout-token")

        assert first.revoked_sessions == 1
        assert replay == first
        assert _counts(service) == (1, 1, 1)
    finally:
        engine.dispose()


def test_logout_replay_survives_restart_and_conflicting_semantics_fail_closed(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "restart.db"
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient()
    service, engine = _service(database_path, oidc, clock)
    _seed_active_session(service, now)
    first = service.handle_backchannel_logout("valid-logout-token")
    engine.dispose()

    restarted, restarted_engine = _service(database_path, oidc, clock)
    try:
        assert restarted.handle_backchannel_logout("valid-logout-token") == first
        assert _counts(restarted) == (1, 1, 1)

        oidc.logout_identity = OidcLogoutIdentity(
            issuer=ISSUER,
            subject="different-user",
            idp_session_id="sid-1",
            client_id=CLIENT_ID,
            jti="logout-1",
        )
        try:
            restarted.handle_backchannel_logout("valid-logout-token")
        except IdentityReplayConflictError:
            pass
        else:
            raise AssertionError("conflicting logout replay was accepted")
        assert _counts(restarted) == (1, 1, 1)
    finally:
        restarted_engine.dispose()


def test_logout_http_contract_is_non_enumerating(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 8, 5, 12, 0, tzinfo=UTC))
    oidc = ReplayOidcClient()
    service, engine = _service(tmp_path / "http.db", oidc, clock)
    client = TestClient(
        create_identity_enabled_app(service._session_factory, service),
        base_url="https://testserver",
    )
    try:
        invalid = client.post(
            "/v1/identity/backchannel-logout",
            content="logout_token=invalid",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert invalid.status_code == 400
        assert invalid.json() == {"detail": "OIDC protocol input is invalid"}

        first = client.post(
            "/v1/identity/backchannel-logout",
            content="logout_token=valid-logout-token",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert first.status_code == 200

        oidc.logout_identity = OidcLogoutIdentity(
            issuer=ISSUER,
            subject="different-user",
            idp_session_id="sid-1",
            client_id=CLIENT_ID,
            jti="logout-1",
        )
        conflict = client.post(
            "/v1/identity/backchannel-logout",
            content="logout_token=valid-logout-token",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert conflict.status_code == 409
        assert conflict.json() == {"detail": "OIDC logout replay conflict"}
    finally:
        engine.dispose()
