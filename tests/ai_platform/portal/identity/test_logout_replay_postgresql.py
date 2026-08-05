from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import func, select

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.database.schema import migrate_database
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.models import (
    IdentityAuditEventRow,
    OidcLogoutReplayRow,
    SessionRevocationRow,
)
from ai_platform.portal.identity.oidc import OidcLogoutIdentity
from ai_platform.portal.identity.repository import IdentityRepository
from ai_platform.portal.identity.schema import OidcIdentity
from ai_platform.portal.identity.service import IdentityService


POSTGRES_URL = os.environ.get("PORTAL_TEST_POSTGRES_URL")
ISSUER = "https://identity.example.test/application/o/portal"
CLIENT_ID = "portal-client"
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PORTAL_TEST_POSTGRES_URL is required for PostgreSQL replay tests",
)


class ConcurrentOidcClient:
    issuer = ISSUER

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
        assert logout_token == "valid-logout-token"
        return OidcLogoutIdentity(
            issuer=ISSUER,
            subject="user-1",
            idp_session_id="sid-1",
            client_id=CLIENT_ID,
            jti="logout-concurrent-1",
        )


@pytest.fixture(autouse=True)
def clean_postgres_schema() -> Iterator[None]:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")
    engine.dispose()
    yield
    engine = build_engine(POSTGRES_URL)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")
    engine.dispose()


def test_concurrent_logout_replay_has_exactly_one_mutation_owner() -> None:
    assert POSTGRES_URL is not None
    engine = build_engine(POSTGRES_URL)
    migrate_database(engine)
    session_factory = build_session_factory(engine)
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    service = IdentityService(
        session_factory,
        ConcurrentOidcClient(),
        IdentityCrypto(
            IdentitySecrets(
                session_hmac_key=b"s" * 32,
                flow_encryption_key=b"f" * 32,
            )
        ),
        clock=lambda: now,
    )
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
    with session_factory() as session:
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

    start = Barrier(2)

    def deliver() -> tuple[int, datetime]:
        start.wait(timeout=5)
        result = service.handle_backchannel_logout("valid-logout-token")
        return result.revoked_sessions, result.processed_at

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = tuple(executor.map(lambda _index: deliver(), range(2)))

        assert outcomes[0] == outcomes[1] == (1, now)
        with session_factory() as session:
            assert session.scalar(select(func.count()).select_from(OidcLogoutReplayRow)) == 1
            assert session.scalar(select(func.count()).select_from(SessionRevocationRow)) == 1
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(IdentityAuditEventRow)
                    .where(IdentityAuditEventRow.action == "identity.backchannel_logout")
                )
                == 1
            )
    finally:
        engine.dispose()
