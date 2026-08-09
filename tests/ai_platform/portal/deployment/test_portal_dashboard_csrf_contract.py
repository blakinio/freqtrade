from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DASHBOARD_API = ROOT / "ai_platform" / "portal" / "web" / "lib" / "dashboard-api.ts"


def test_dashboard_post_read_forwards_identity_csrf_token() -> None:
    source = DASHBOARD_API.read_text(encoding="utf-8")

    assert 'const CSRF_COOKIE_NAME = "__Host-portal_csrf"' in source
    assert 'const CSRF_HEADER_NAME = "x-csrf-token"' in source
    assert "function csrfHeader(cookieHeader?: string | null)" in source
    assert "decodeURIComponent(encoded)" in source
    assert "PORTAL_DASHBOARD_CSRF_MISSING" in source
    assert 'method: "POST"' in source
    assert "...csrfHeader(cookieHeader)" in source
