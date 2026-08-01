from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PUBLIC_RUNTIME = ROOT / "ai_platform" / "portal" / "identity" / "public_runtime.py"


def test_oidc_protocol_failure_is_mapped_to_generic_json_502() -> None:
    source = PUBLIC_RUNTIME.read_text(encoding="utf-8")

    assert "from ai_platform.portal.identity.oidc import" in source
    assert "OidcProtocolError" in source
    assert "@app.exception_handler(OidcProtocolError)" in source
    assert "status_code=status.HTTP_502_BAD_GATEWAY" in source
    assert 'content={"detail": "OIDC provider response failed validation"}' in source
    assert "str(_exc)" not in source
