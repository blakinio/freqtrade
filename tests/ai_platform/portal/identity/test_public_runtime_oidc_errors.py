from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_platform.portal.identity.oidc import OidcProtocolError
from ai_platform.portal.identity.public_runtime import _register_identity_routes
from ai_platform.portal.identity.service import IdentityService


class _ProtocolFailureService:
    def complete_login(self, *, code: str, state: str):
        assert code == "code-1"
        assert state == "state-1"
        raise OidcProtocolError("internal validation detail")


def test_oidc_protocol_failure_returns_generic_json_502() -> None:
    app = FastAPI()
    service = cast(IdentityService, _ProtocolFailureService())
    _register_identity_routes(app, service)

    response = TestClient(app).get(
        "/v1/identity/callback",
        params={"code": "code-1", "state": "state-1"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "OIDC provider response failed validation"}
    assert "internal validation detail" not in response.text
