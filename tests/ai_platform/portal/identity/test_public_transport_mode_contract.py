from pathlib import Path

from ai_platform.portal.identity import runtime


ROOT = Path(__file__).resolve().parents[4]
DEPLOYER = ROOT / "deploy" / "synology" / "portal-oidc" / "deploy.py"
RUNTIME = ROOT / "ai_platform" / "portal" / "identity" / "runtime.py"
PUBLIC_RUNTIME = ROOT / "ai_platform" / "portal" / "identity" / "public_runtime.py"


def test_public_https_transport_normalizes_to_secure_https(monkeypatch) -> None:
    monkeypatch.setenv("PORTAL_IDENTITY_TRANSPORT_MODE", "https")

    assert runtime._transport_mode() == "secure_https"


def test_explicit_secure_https_transport_remains_supported(monkeypatch) -> None:
    monkeypatch.setenv("PORTAL_IDENTITY_TRANSPORT_MODE", "secure_https")

    assert runtime._transport_mode() == "secure_https"


def test_public_deployment_and_runtime_share_normalized_transport_contract() -> None:
    deployer = DEPLOYER.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    public_runtime = PUBLIC_RUNTIME.read_text(encoding="utf-8")

    assert '"PORTAL_IDENTITY_TRANSPORT_MODE": "https"' in deployer
    assert 'if value == "https":' in runtime_source
    assert 'value = "secure_https"' in runtime_source
    assert 'config.transport_mode != "secure_https"' in public_runtime
    assert 'config.transport_mode != "https"' not in public_runtime
