from pathlib import Path

import httpx
import pytest

from ai_platform.portal.deploy.cloudflare.policy import load_policy
from ai_platform.portal.deploy.cloudflare.probe import ProbeOutcome, run_probes


POLICY = Path("ai_platform/portal/deploy/cloudflare/staging-policy.example.json")


def _set_env(monkeypatch) -> None:
    env = {
        "PORTAL_STAGING_BASE_URL": "https://portal.example.test/",
        "PORTAL_STAGING_PRIVILEGED_PATH": "/admin",
        "PORTAL_STAGING_ORIGIN_PROBE_URL": "https://origin.example.test/",
        "PORTAL_STAGING_FREQTRADE_PROBE_URL": "https://freqtrade.example.test/",
        "PORTAL_STAGING_CF_ACCESS_CLIENT_ID": "service-id",
        "PORTAL_STAGING_CF_ACCESS_CLIENT_SECRET": "service-secret",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)


def test_external_probe_proves_cloudflare_access_and_direct_path_denials(monkeypatch) -> None:
    policy = load_policy(POLICY)
    _set_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == "portal.example.test" and request.url.path == "/":
            return httpx.Response(200)
        if host == "portal.example.test" and request.url.path == "/admin":
            if request.headers.get("CF-Access-Client-Id") == "service-id":
                return httpx.Response(200)
            return httpx.Response(
                302,
                headers={"location": "https://example.cloudflareaccess.com/cdn-cgi/access/login"},
            )
        if host in {"origin.example.test", "freqtrade.example.test"}:
            return httpx.Response(403)
        return httpx.Response(500)

    results = run_probes(policy, transport=httpx.MockTransport(handler))

    assert results
    assert all(result.outcome is ProbeOutcome.SUCCESS for result in results)
    assert {result.name for result in results} == {
        "cloudflare-public-ingress",
        "access-anonymous-denial",
        "access-service-identity",
        "origin-direct-denial",
        "freqtrade-direct-denial",
    }


def test_external_probe_fails_when_service_identity_is_not_authorized(monkeypatch) -> None:
    policy = load_policy(POLICY)
    _set_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "portal.example.test" and request.url.path == "/":
            return httpx.Response(200)
        if request.url.host == "portal.example.test":
            return httpx.Response(403)
        return httpx.Response(403)

    results = run_probes(policy, transport=httpx.MockTransport(handler))
    by_name = {result.name: result for result in results}

    assert by_name["access-service-identity"].outcome is ProbeOutcome.FAILURE


def test_probe_evidence_never_contains_endpoint_or_service_secret(monkeypatch) -> None:
    policy = load_policy(POLICY)
    _set_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "portal.example.test" and request.url.path == "/":
            return httpx.Response(200)
        if request.url.host == "portal.example.test":
            if request.headers.get("CF-Access-Client-Secret") == "service-secret":
                return httpx.Response(204)
            return httpx.Response(403)
        return httpx.Response(403)

    results = run_probes(policy, transport=httpx.MockTransport(handler))
    evidence = " ".join(result.evidence for result in results)

    assert "service-secret" not in evidence
    assert "portal.example.test" not in evidence
    assert "origin.example.test" not in evidence
    assert "freqtrade.example.test" not in evidence


def test_external_probe_rejects_non_url_endpoint_reference(monkeypatch) -> None:
    policy = load_policy(POLICY)
    _set_env(monkeypatch)
    monkeypatch.setenv("PORTAL_STAGING_ORIGIN_PROBE_URL", "not-a-url")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request)

    with pytest.raises(RuntimeError, match="invalid URL"):
        run_probes(policy, transport=httpx.MockTransport(handler))
