from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
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
OTHER_ISSUER = "https://other-identity.example.test/application/o/portal"
CLIENT_ID = "portal-client"


@dataclass
class MutableClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class ReplayOidcClient:
    issuer = ISSUER

    def __init__(self, now: datetime) -> None:
        self.logout_identity = _logout_identity(now)

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


def _logout_identity(
    now: datetime,
    *,
    issuer: str = ISSUER,
    subject: str | None = "user-1",
    sid: str | None = "sid-1",
    jti: str = "logout-1",
    signing_key_id: str = "key-1",
    signing_algorithm: str = "RS256",
    jwt_typ: str = "logout+jwt",
    issued_at: datetime | None = None,
    expires_at: datetime | None = None,
    retention_until: datetime | None = None,
) -> OidcLogoutIdentity:
    issued = issued_at or now
    expires = expires_at or issued + timedelta(minutes=5)
    retention = retention_until or expires + timedelta(minutes=15)
    return OidcLogoutIdentity(
        issuer=issuer,
        client_id=CLIENT_ID,
        jti=jti,
        issued_at=issued,
        expires_at=expires,
        retention_until=retention,
        token_type=jwt_typ,
        signing_key_id=signing_key_id,
        signing_algorithm=signing_algorithm,
        subject=subject,
        idp_session_id=sid,
    )


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


def _seed_identity(
    service: IdentityService,
    now: datetime,
    *,
    issuer: str = ISSUER,
    subject: str = "user-1",
    session_id_hash: str = "session-hash",
    sid: str = "sid-1",
) -> tuple[str, str]:
    principal = service.bootstrap_principal(
        issuer=issuer,
        subject=subject,
        display_name="Portal User",
        email="portal@example.test",
    )
    membership = service.bootstrap_membership(
        principal_id=principal.principal_id,
        tenant_id=f"tenant-{principal.principal_id}",
        roles=(RoleName.ADMIN,),
    )
    _add_session(
        service,
        now,
        principal_id=principal.principal_id,
        membership_id=membership.membership_id,
        membership_version=membership.membership_version,
        session_id_hash=session_id_hash,
        sid=sid,
    )
    return principal.principal_id, membership.membership_id


def _add_session(
    service: IdentityService,
    now: datetime,
    *,
    principal_id: str,
    membership_id: str,
    membership_version: int,
    session_id_hash: str,
    sid: str,
) -> None:
    with service._session_factory() as session:
        IdentityRepository(session).create_session(
            session_id_hash=session_id_hash,
            csrf_token_hash=f"csrf-{session_id_hash}",
            principal_id=principal_id,
            membership_id=membership_id,
            membership_version=membership_version,
            idp_session_id=sid,
            authentication_time=now,
            mfa_satisfied=True,
            created_at=now,
            idle_expires_at=now + timedelta(minutes=15),
            absolute_expires_at=now + timedelta(hours=4),
        )
        session.commit()


def _event_count(service: IdentityService, action: str) -> int:
    with service._session_factory() as session:
        return int(
            session.scalar(
                select(func.count())
                .select_from(IdentityAuditEventRow)
                .where(IdentityAuditEventRow.action == action)
            )
            or 0
        )


def _counts(service: IdentityService) -> tuple[int, int, int]:
    with service._session_factory() as session:
        replay_count = int(
            session.scalar(select(func.count()).select_from(OidcLogoutReplayRow)) or 0
        )
        revocation_count = int(
            session.scalar(select(func.count()).select_from(SessionRevocationRow)) or 0
        )
        success_count = int(
            session.scalar(
                select(func.count())
                .select_from(IdentityAuditEventRow)
                .where(IdentityAuditEventRow.action == "identity.backchannel_logout")
            )
            or 0
        )
        return replay_count, revocation_count, success_count


def test_exact_logout_replay_returns_original_result_without_second_mutation(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient(now)
    service, engine = _service(tmp_path / "replay.db", oidc, clock)
    try:
        principal_id, membership_id = _seed_identity(service, now)

        first = service.handle_backchannel_logout("valid-logout-token")
        clock.value += timedelta(minutes=1)
        _add_session(
            service,
            clock.value,
            principal_id=principal_id,
            membership_id=membership_id,
            membership_version=1,
            session_id_hash="new-session-hash",
            sid="sid-1",
        )
        replay = service.handle_backchannel_logout("valid-logout-token")

        assert first.revoked_sessions == 1
        assert replay == first
        assert _counts(service) == (1, 1, 1)
        with service._session_factory() as session:
            new_session = IdentityRepository(session).get_session("new-session-hash")
            assert new_session is not None
            assert new_session.revoked_at is None
    finally:
        engine.dispose()


def test_logout_replay_survives_restart_and_signature_drift_conflicts(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "restart.db"
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient(now)
    service, engine = _service(database_path, oidc, clock)
    _seed_identity(service, now)
    first = service.handle_backchannel_logout("valid-logout-token")
    engine.dispose()

    restarted, restarted_engine = _service(database_path, oidc, clock)
    try:
        assert restarted.handle_backchannel_logout("valid-logout-token") == first
        assert _counts(restarted) == (1, 1, 1)

        oidc.logout_identity = _logout_identity(now, signing_key_id="rotated-key")
        with pytest.raises(IdentityReplayConflictError):
            restarted.handle_backchannel_logout("valid-logout-token")
        assert _counts(restarted) == (1, 1, 1)
        assert _event_count(restarted, "identity.backchannel_logout_conflict") == 1
    finally:
        restarted_engine.dispose()


def test_sid_and_issuer_scope_are_exact_while_subject_only_revokes_all_sessions(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient(now)
    service, engine = _service(tmp_path / "scope.db", oidc, clock)
    try:
        principal_id, membership_id = _seed_identity(service, now)
        _add_session(
            service,
            now,
            principal_id=principal_id,
            membership_id=membership_id,
            membership_version=1,
            session_id_hash="other-sid-session",
            sid="sid-2",
        )
        _seed_identity(
            service,
            now,
            issuer=OTHER_ISSUER,
            subject="other-user",
            session_id_hash="other-issuer-session",
            sid="sid-1",
        )

        sid_result = service.handle_backchannel_logout("valid-logout-token")
        assert sid_result.revoked_sessions == 1
        with service._session_factory() as session:
            repository = IdentityRepository(session)
            other_sid = repository.get_session("other-sid-session")
            other_issuer = repository.get_session("other-issuer-session")
            assert other_sid is not None and other_sid.revoked_at is None
            assert other_issuer is not None and other_issuer.revoked_at is None

        oidc.logout_identity = _logout_identity(
            clock.value,
            subject="user-1",
            sid=None,
            jti="logout-subject-1",
        )
        subject_result = service.handle_backchannel_logout("valid-logout-token")
        assert subject_result.revoked_sessions == 1
    finally:
        engine.dispose()


def test_replay_retention_purge_is_bounded_and_audited(tmp_path: Path) -> None:
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient(now)
    oidc.logout_identity = _logout_identity(
        now,
        expires_at=now + timedelta(seconds=30),
        retention_until=now + timedelta(minutes=1),
    )
    service, engine = _service(tmp_path / "retention.db", oidc, clock)
    try:
        _seed_identity(service, now)
        service.handle_backchannel_logout("valid-logout-token")

        clock.value = now + timedelta(minutes=2)
        oidc.logout_identity = _logout_identity(
            clock.value,
            jti="logout-2",
            subject="unknown-user",
            sid=None,
        )
        service.handle_backchannel_logout("valid-logout-token")

        assert _event_count(service, "identity.backchannel_logout_replay_expired") == 1
        with service._session_factory() as session:
            keys = set(session.scalars(select(OidcLogoutReplayRow.jti)).all())
            assert keys == {"logout-2"}
    finally:
        engine.dispose()


def test_logout_http_contract_is_non_enumerating_and_not_cached(tmp_path: Path) -> None:
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    clock = MutableClock(now)
    oidc = ReplayOidcClient(now)
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
        assert invalid.headers["cache-control"] == "no-store"
        assert _event_count(service, "identity.backchannel_logout_rejected") == 1

        first = client.post(
            "/v1/identity/backchannel-logout",
            content="logout_token=valid-logout-token",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert first.status_code == 200
        assert first.headers["cache-control"] == "no-store"

        oidc.logout_identity = _logout_identity(now, subject="different-user")
        conflict = client.post(
            "/v1/identity/backchannel-logout",
            content="logout_token=valid-logout-token",
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert conflict.status_code == 400
        assert conflict.json() == {"detail": "OIDC logout request is invalid"}
        assert conflict.headers["cache-control"] == "no-store"
    finally:
        engine.dispose()
