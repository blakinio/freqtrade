from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import UUID

from fastapi.testclient import TestClient

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, RoleName
from ai_platform.portal.contracts.strategy_closure import (
    CapabilityRequirement,
    ClosureRequestContext,
    PublicContractProvenance,
    SignalWizardFeatureSelection,
    SignalWizardPreviewCommand,
    SignalWizardSubmitCommand,
    StrategyCapability,
)
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.identity.crypto import IdentityCrypto, IdentitySecrets
from ai_platform.portal.identity.http import create_identity_enabled_app
from ai_platform.portal.identity.oidc import OidcLogoutIdentity
from ai_platform.portal.identity.schema import OidcIdentity
from ai_platform.portal.identity.service import CSRF_COOKIE_NAME, IdentityService


DUMMY_REQUEST_ID = UUID("10000000-0000-0000-0000-000000000001")
DUMMY_CORRELATION_ID = UUID("10000000-0000-0000-0000-000000000002")
NOW = datetime(2026, 7, 31, 7, 0, tzinfo=UTC)


@dataclass
class FixedClock:
    value: datetime = NOW

    def __call__(self) -> datetime:
        return self.value


class FakeOidcClient:
    issuer = "https://identity.example.test/application/o/portal"

    def __init__(self, clock: FixedClock) -> None:
        self._clock = clock
        self._nonce: str | None = None

    def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        self._nonce = nonce
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
        assert expected_nonce == self._nonce
        return OidcIdentity(
            issuer=self.issuer,
            subject="signal-wizard-user",
            display_name="Signal Wizard User",
            email="wizard@example.test",
            idp_session_id="signal-wizard-session",
            authentication_time=self._clock(),
            mfa_satisfied=True,
            authentication_methods=("webauthn",),
        )

    def validate_backchannel_logout(self, logout_token: str) -> OidcLogoutIdentity:
        raise AssertionError(f"unexpected back-channel logout: {logout_token}")


def _identity_client() -> tuple[TestClient, str]:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    clock = FixedClock()
    oidc = FakeOidcClient(clock)
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
    principal = service.bootstrap_principal(
        issuer=oidc.issuer,
        subject="signal-wizard-user",
        display_name="Signal Wizard User",
        email="wizard@example.test",
    )
    service.bootstrap_membership(
        principal_id=principal.principal_id,
        tenant_id="tenant-a",
        roles=(RoleName.ADMIN,),
    )
    client = TestClient(
        create_identity_enabled_app(session_factory, service),
        base_url="https://testserver",
    )
    login = client.get(
        "/v1/identity/login",
        params={"tenant_id": "tenant-a", "return_to": "/ai/signal-wizard"},
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
    csrf = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf
    return client, principal.principal_id


def _context(actor_id: str) -> ClosureRequestContext:
    return ClosureRequestContext(
        tenant_id="tenant-a",
        actor_id=actor_id,
        actor_type=ActorType.USER,
        resource_type="strategy",
        resource_id="signal-wizard-strategy",
        environment=Environment.RESEARCH,
        execution_mode=ExecutionMode.SIMULATED,
        correlation=CorrelationContext(
            request_id=DUMMY_REQUEST_ID,
            correlation_id=DUMMY_CORRELATION_ID,
        ),
        provenance=PublicContractProvenance(
            producer="signal-wizard-identity-http-test",
            artifact_id="identity-http-artifact",
            created_at=NOW,
            source_refs=("feature-registry:1.0.0",),
        ),
    )


def _capability(value: StrategyCapability) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability=value,
        authorization_decision_ref=f"identity-http:{value.value}",
    )


def _preview_command(actor_id: str) -> SignalWizardPreviewCommand:
    return SignalWizardPreviewCommand(
        context=_context(actor_id),
        idempotency_key="identity-preview-1",
        strategy_id="signal-wizard-strategy",
        feature_selections=(
            SignalWizardFeatureSelection(
                feature_id="atr.v1",
                timeframe="5m",
                parameters={"period": 14},
            ),
        ),
        condition_ast={"all": [{"feature": "atr.v1", "op": "gt", "value": 0}]},
        capability=_capability(StrategyCapability.STRATEGY_RESEARCH),
    )


def test_identity_enabled_signal_wizard_binds_stable_server_correlation() -> None:
    client, actor_id = _identity_client()
    csrf = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf
    headers = {"x-csrf-token": csrf}
    command = _preview_command(actor_id)

    first = client.post(
        "/v1/signal-wizard/preview",
        json=command.model_dump(mode="json"),
        headers=headers,
    )
    second = client.post(
        "/v1/signal-wizard/preview",
        json=command.model_dump(mode="json"),
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert second_payload == first_payload
    assert first_payload["preview_hash"] == second_payload["preview_hash"]
    assert first_payload["context"]["correlation"]["request_id"] != str(DUMMY_REQUEST_ID)
    assert first_payload["context"]["correlation"]["correlation_id"] != str(DUMMY_CORRELATION_ID)

    submit = SignalWizardSubmitCommand(
        context=_context(actor_id),
        idempotency_key="identity-submit-1",
        preview_hash=first_payload["preview_hash"],
        experiment_name="Identity-enabled research candidate",
        expected_strategy_version=first_payload["strategy_definition"]["version"],
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )
    first_submit = client.post(
        "/v1/signal-wizard/submit",
        json=submit.model_dump(mode="json"),
        headers=headers,
    )
    second_submit = client.post(
        "/v1/signal-wizard/submit",
        json=submit.model_dump(mode="json"),
        headers=headers,
    )

    assert first_submit.status_code == 201
    assert second_submit.status_code == 201
    assert second_submit.json() == first_submit.json()
    assert first_submit.json()["accepted"] is True
    assert first_submit.json()["execution_authority"] is False
    assert first_submit.json()["promotion_authority"] is False


def test_identity_enabled_signal_wizard_still_rejects_actor_mismatch() -> None:
    client, _actor_id = _identity_client()
    csrf = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf

    response = client.post(
        "/v1/signal-wizard/preview",
        json=_preview_command("different-actor").model_dump(mode="json"),
        headers={"x-csrf-token": csrf},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["reason_code"] == "SIGNAL_WIZARD_CONTEXT_MISMATCH"
