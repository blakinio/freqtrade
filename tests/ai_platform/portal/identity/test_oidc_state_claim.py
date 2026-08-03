from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Lock
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.models import (
    IdentityAuditEventRow,
    OidcLoginFlowRow,
    PortalSessionRow,
)
from ai_platform.portal.identity.oidc import OidcLogoutIdentity
from ai_platform.portal.identity.repository import IdentityNotFoundError, IdentityRepository
from ai_platform.portal.identity.schema import OidcIdentity
from ai_platform.portal.identity.service import (
    IdentityAuthenticationError,
    IdentityService,
)


_CALLBACK_ACTIONS = {
    "identity.login_state_claimed",
    "identity.login_state_rejected",
    "identity.login_denied",
    "identity.login_succeeded",
}


@dataclass
class FixedClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class CountingOidcClient:
    issuer = "https://identity.example.test/application/o/portal"

    def __init__(self, clock: FixedClock, *, fail_exchange: bool = False) -> None:
        self._clock = clock
        self._fail_exchange = fail_exchange
        self._lock = Lock()
        self.exchange_count = 0
        self.exchange_started = Event()
        self.release_exchange = Event()
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
        assert code in {"code-a", "code-b"}
        assert len(code_verifier) >= 43
        assert expected_nonce == self.last_nonce
        with self._lock:
            self.exchange_count += 1
        self.exchange_started.set()
        if self._fail_exchange:
            raise RuntimeError("synthetic provider failure")
        assert self.release_exchange.wait(timeout=5)
        return OidcIdentity(
            issuer=self.issuer,
            subject="user-1",
            display_name="Portal User",
            email="portal@example.test",
            idp_session_id="sid-1",
            authentication_time=self._clock(),
            mfa_satisfied=True,
            authentication_methods=("webauthn",),
        )

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity:
        raise AssertionError(f"unexpected back-channel logout: {logout_token}")


class _ScalarResult:
    def __init__(self, row: object) -> None:
        self._row = row

    def one_or_none(self) -> object:
        return self._row


class _CapturingSession:
    def __init__(self) -> None:
        self.statement: Any | None = None

    def scalars(self, statement: Any) -> _ScalarResult:
        self.statement = statement
        return _ScalarResult(object())


def _crypto() -> IdentityCrypto:
    return IdentityCrypto(
        IdentitySecrets(
            session_hmac_key=b"s" * 32,
            flow_encryption_key=b"f" * 32,
        )
    )


def _service(
    session_factory: SessionFactory,
    oidc: CountingOidcClient,
    clock: FixedClock,
) -> IdentityService:
    service = IdentityService(session_factory, oidc, _crypto(), clock=clock)
    principal = service.bootstrap_principal(
        issuer=oidc.issuer,
        subject="user-1",
        display_name="Portal User",
        email="portal@example.test",
    )
    service.bootstrap_membership(
        principal_id=principal.principal_id,
        tenant_id="tenant-a",
        roles=(RoleName.ADMIN,),
    )
    return service


def _state(service: IdentityService) -> str:
    login = service.begin_login(requested_tenant_id="tenant-a", return_to="/bots")
    return parse_qs(urlparse(login.authorization_url).query)["state"][0]


def _file_session_factory(tmp_path: Path) -> tuple[SessionFactory, Any]:
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'identity.db'}")
    create_schema(engine)
    return build_session_factory(engine), engine


def _callback_events(session_factory: SessionFactory) -> tuple[IdentityAuditEventRow, ...]:
    with session_factory() as session:
        return tuple(
            session.scalars(
                select(IdentityAuditEventRow)
                .where(IdentityAuditEventRow.action.in_(_CALLBACK_ACTIONS))
                .order_by(IdentityAuditEventRow.occurred_at, IdentityAuditEventRow.event_id)
            ).all()
        )


def _assert_safe_claim_correlation(
    events: tuple[IdentityAuditEventRow, ...],
    *,
    state: str,
) -> str:
    correlations = {event.correlation_id for event in events}
    assert len(correlations) == 1
    claim_id = correlations.pop()
    assert claim_id is not None
    assert claim_id == _crypto().hash_token(state)
    assert claim_id != state
    rendered = "|".join(
        str(value)
        for event in events
        for value in (
            event.action,
            event.actor_id,
            event.reason,
            event.correlation_id,
        )
    )
    assert state not in rendered
    assert "code-a" not in rendered
    assert "code-b" not in rendered
    assert "verifier" not in rendered.casefold()
    return claim_id


def test_claim_statement_is_compare_and_swap_on_postgresql() -> None:
    session = _CapturingSession()
    repository = IdentityRepository(session)
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)

    repository.consume_login_flow("state-hash", now)

    assert session.statement is not None
    compiled = str(
        session.statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    ).casefold()
    assert "update portal_oidc_login_flows" in compiled
    assert "state_hash" in compiled
    assert "consumed_at is null" in compiled
    assert "expires_at >" in compiled
    assert "returning" in compiled


def test_two_independent_sqlite_connections_claim_exactly_once(tmp_path: Path) -> None:
    session_factory, engine = _file_session_factory(tmp_path)
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    with session_factory() as session:
        IdentityRepository(session).store_login_flow(
            state_hash="state-hash",
            nonce="nonce",
            verifier_ciphertext="ciphertext",
            requested_tenant_id="tenant-a",
            return_to="/bots",
            created_at=now,
            expires_at=now + timedelta(minutes=10),
        )
        session.commit()

    def claim() -> str:
        with session_factory() as session:
            try:
                IdentityRepository(session).consume_login_flow("state-hash", now)
                session.commit()
                return "claimed"
            except IdentityNotFoundError:
                session.rollback()
                return "rejected"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = tuple(executor.map(lambda _: claim(), range(2)))
        assert sorted(outcomes) == ["claimed", "rejected"]
        with session_factory() as session:
            flow = session.get(OidcLoginFlowRow, "state-hash")
            assert flow is not None
            assert flow.consumed_at is not None
    finally:
        engine.dispose()


def test_rollback_before_commit_does_not_create_a_durable_claim(tmp_path: Path) -> None:
    session_factory, engine = _file_session_factory(tmp_path)
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    with session_factory() as session:
        IdentityRepository(session).store_login_flow(
            state_hash="state-hash",
            nonce="nonce",
            verifier_ciphertext="ciphertext",
            requested_tenant_id=None,
            return_to="/",
            created_at=now,
            expires_at=now + timedelta(minutes=10),
        )
        session.commit()

    try:
        with session_factory() as first:
            IdentityRepository(first).consume_login_flow("state-hash", now)
            first.rollback()
        with session_factory() as second:
            claimed = IdentityRepository(second).consume_login_flow("state-hash", now)
            second.commit()
            assert claimed.consumed_at is not None
    finally:
        engine.dispose()


def test_expired_state_cannot_be_claimed(tmp_path: Path) -> None:
    session_factory, engine = _file_session_factory(tmp_path)
    now = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
    with session_factory() as session:
        IdentityRepository(session).store_login_flow(
            state_hash="state-hash",
            nonce="nonce",
            verifier_ciphertext="ciphertext",
            requested_tenant_id=None,
            return_to="/",
            created_at=now - timedelta(minutes=20),
            expires_at=now - timedelta(minutes=10),
        )
        session.commit()

    try:
        with (
            session_factory() as session,
            pytest.raises(
                IdentityNotFoundError,
                match="invalid or expired",
            ),
        ):
            IdentityRepository(session).consume_login_flow("state-hash", now)
    finally:
        engine.dispose()


def test_overlapping_callbacks_have_one_provider_owner_session_and_attribution(
    tmp_path: Path,
) -> None:
    session_factory, engine = _file_session_factory(tmp_path)
    clock = FixedClock(datetime(2026, 8, 3, 12, 0, tzinfo=UTC))
    oidc = CountingOidcClient(clock)
    service = _service(session_factory, oidc, clock)
    state = _state(service)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            winner = executor.submit(service.complete_login, code="code-a", state=state)
            assert oidc.exchange_started.wait(timeout=5)
            loser = executor.submit(service.complete_login, code="code-b", state=state)
            with pytest.raises(IdentityAuthenticationError, match="invalid or expired"):
                loser.result(timeout=5)
            oidc.release_exchange.set()
            completed = winner.result(timeout=5)

        assert completed.return_to == "/bots"
        assert oidc.exchange_count == 1
        with session_factory() as session:
            assert session.scalar(select(func.count()).select_from(PortalSessionRow)) == 1
        events = _callback_events(session_factory)
        assert [event.action for event in events].count("identity.login_state_claimed") == 1
        assert [event.action for event in events].count("identity.login_state_rejected") == 1
        assert [event.action for event in events].count("identity.login_succeeded") == 1
        assert [event.action for event in events].count("identity.login_denied") == 0
        _assert_safe_claim_correlation(events, state=state)
    finally:
        oidc.release_exchange.set()
        engine.dispose()


def test_provider_failure_is_terminal_attributable_and_cannot_be_retried(tmp_path: Path) -> None:
    session_factory, engine = _file_session_factory(tmp_path)
    clock = FixedClock(datetime(2026, 8, 3, 12, 0, tzinfo=UTC))
    oidc = CountingOidcClient(clock, fail_exchange=True)
    service = _service(session_factory, oidc, clock)
    state = _state(service)

    try:
        with pytest.raises(RuntimeError, match="synthetic provider failure"):
            service.complete_login(code="code-a", state=state)
        with pytest.raises(IdentityAuthenticationError, match="invalid or expired"):
            service.complete_login(code="code-b", state=state)
        assert oidc.exchange_count == 1
        with session_factory() as session:
            assert session.scalar(select(func.count()).select_from(PortalSessionRow)) == 0
        events = _callback_events(session_factory)
        assert [event.action for event in events] == [
            "identity.login_state_claimed",
            "identity.login_denied",
            "identity.login_state_rejected",
        ]
        assert [event.reason for event in events] == [
            "claimed",
            "provider_exchange_failed",
            "invalid_or_replayed",
        ]
        _assert_safe_claim_correlation(events, state=state)
    finally:
        engine.dispose()


def test_provider_success_without_membership_has_terminal_denial_and_no_retry(
    tmp_path: Path,
) -> None:
    session_factory, engine = _file_session_factory(tmp_path)
    clock = FixedClock(datetime(2026, 8, 3, 12, 0, tzinfo=UTC))
    oidc = CountingOidcClient(clock)
    oidc.release_exchange.set()
    service = IdentityService(session_factory, oidc, _crypto(), clock=clock)
    service.bootstrap_principal(
        issuer=oidc.issuer,
        subject="user-1",
        display_name="Portal User",
        email="portal@example.test",
    )
    state = _state(service)

    try:
        with pytest.raises(IdentityAuthenticationError, match="membership"):
            service.complete_login(code="code-a", state=state)
        with pytest.raises(IdentityAuthenticationError, match="invalid or expired"):
            service.complete_login(code="code-b", state=state)
        assert oidc.exchange_count == 1
        with session_factory() as session:
            assert session.scalar(select(func.count()).select_from(PortalSessionRow)) == 0
        events = _callback_events(session_factory)
        assert [event.action for event in events] == [
            "identity.login_state_claimed",
            "identity.login_denied",
            "identity.login_state_rejected",
        ]
        assert [event.reason for event in events] == [
            "claimed",
            "membership_unavailable",
            "invalid_or_replayed",
        ]
        _assert_safe_claim_correlation(events, state=state)
    finally:
        engine.dispose()
