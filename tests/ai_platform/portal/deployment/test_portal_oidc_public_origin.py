from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PUBLIC_ORIGIN_PATH = ROOT / "ai_platform" / "portal" / "web" / "lib" / "public-origin.ts"
CALLBACK_ROUTE_PATH = (
    ROOT
    / "ai_platform"
    / "portal"
    / "web"
    / "app"
    / "api"
    / "identity"
    / "callback"
    / "route.ts"
)
LOGIN_ROUTE_PATH = (
    ROOT
    / "ai_platform"
    / "portal"
    / "web"
    / "app"
    / "api"
    / "identity"
    / "login"
    / "route.ts"
)
VERIFIER_PATH = (
    ROOT / "deploy" / "synology" / "portal-oidc" / "verify_provider_grant_types.py"
)


def test_production_redirect_origin_is_not_derived_from_container_request() -> None:
    helper = PUBLIC_ORIGIN_PATH.read_text(encoding="utf-8")
    callback = CALLBACK_ROUTE_PATH.read_text(encoding="utf-8")
    login = LOGIN_ROUTE_PATH.read_text(encoding="utf-8")

    assert 'FROZEN_PUBLIC_PORTAL_ORIGIN = "https://quant.molehill.cloud"' in helper
    assert "process.env.PORTAL_PUBLIC_ORIGIN" in helper
    assert 'process.env.PORTAL_ENVIRONMENT === "production"' in helper
    assert "PORTAL_PUBLIC_ORIGIN must use HTTPS outside local test mode" in helper
    assert "PORTAL_PUBLIC_ORIGIN must contain only scheme and authority" in helper

    expected_redirect = (
        'safeBackendReturnLocation(upstream.headers.get("location"), redirectOrigin)'
    )
    forbidden_redirect = (
        'safeBackendReturnLocation(upstream.headers.get("location"), '
        "request.nextUrl.origin)"
    )
    assert 'import { portalPublicOrigin } from "@/lib/public-origin";' in callback
    assert "const redirectOrigin = portalPublicOrigin(request.nextUrl.origin);" in callback
    assert expected_redirect in callback
    assert forbidden_redirect not in callback
    assert "new URL(returnTo, request.url)" not in callback

    assert 'import { portalPublicOrigin } from "@/lib/public-origin";' in login
    assert "new URL(returnTo, portalPublicOrigin(request.nextUrl.origin))" in login
    assert "new URL(returnTo, request.url)" not in login


def test_target_verifier_exercises_real_built_callback_route() -> None:
    verifier = VERIFIER_PATH.read_text(encoding="utf-8")

    assert 'PORTAL_ORIGIN = "https://quant.molehill.cloud"' in verifier
    assert "PORTAL_IDENTITY_FIXTURE_MODE=enabled" in verifier
    assert "PORTAL_PUBLIC_ORIGIN={PORTAL_ORIGIN}" in verifier
    assert "/api/identity/callback" in verifier
    assert "redirect:'manual'" in verifier
    assert 'payload != {"status": 303, "location": expected_location}' in verifier
    assert 'portal["public_callback_redirect_verified"] = True' in verifier
    assert 'portal["public_callback_redirect_location"] = callback_location' in verifier
