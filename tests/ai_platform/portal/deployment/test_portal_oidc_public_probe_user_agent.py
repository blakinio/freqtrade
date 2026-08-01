from __future__ import annotations

import importlib.util
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DIAGNOSTIC_PATH = ROOT / "deploy" / "synology" / "portal-oidc" / "diagnose_discovery.py"
SPEC = importlib.util.spec_from_file_location("portal_oidc_discovery_public_probe", DIAGNOSTIC_PATH)
assert SPEC and SPEC.loader
diagnostic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostic)


def test_public_portal_probe_gets_stable_machine_user_agent(monkeypatch) -> None:
    original_request = urllib.request.Request
    monkeypatch.setattr(diagnostic.urllib.request, "Request", original_request)

    diagnostic._install_public_portal_probe_user_agent()

    request = diagnostic.urllib.request.Request(
        f"{diagnostic.PUBLIC_PORTAL_LOGIN_PREFIX}?return_to=%2F",
        headers={"Accept": "text/html"},
    )
    assert request.get_header("User-agent") == diagnostic.OIDC_HTTP_USER_AGENT
    assert request.get_header("Accept") == "text/html"

    explicit = diagnostic.urllib.request.Request(
        f"{diagnostic.PUBLIC_PORTAL_LOGIN_PREFIX}?return_to=%2F",
        headers={"User-Agent": "Explicit-Test-Agent/1.0"},
    )
    assert explicit.get_header("User-agent") == "Explicit-Test-Agent/1.0"

    unrelated = diagnostic.urllib.request.Request("https://example.com/")
    assert unrelated.get_header("User-agent") is None

    installed_request = diagnostic.urllib.request.Request
    diagnostic._install_public_portal_probe_user_agent()
    assert diagnostic.urllib.request.Request is installed_request


def test_deployment_probe_installs_public_probe_identity_after_oidc_validation(monkeypatch) -> None:
    installed = False

    monkeypatch.setattr(
        diagnostic,
        "diagnose",
        lambda: {
            "issuer": diagnostic.ISSUER,
            "discovery": 200,
            "jwks_uri": 200,
        },
    )

    def install() -> None:
        nonlocal installed
        installed = True

    monkeypatch.setattr(diagnostic, "_install_public_portal_probe_user_agent", install)

    discovery, statuses = diagnostic.deployment_probe(RuntimeError)

    assert installed is True
    assert discovery == {"issuer": diagnostic.ISSUER}
    assert statuses == {"discovery": 200, "jwks_uri": 200}
