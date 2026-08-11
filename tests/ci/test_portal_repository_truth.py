from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PORTAL_README = REPO_ROOT / "ai_platform" / "portal" / "README.md"
PORTAL_LEDGER = REPO_ROOT / "tools" / "portal_audit" / "ledger" / "index.json"
CODEOWNERS = REPO_ROOT / ".github" / "CODEOWNERS"

REQUIRED_IMPLEMENTED_ROOTS = (
    "ai_platform/portal/control_plane",
    "ai_platform/portal/execution",
    "ai_platform/portal/identity",
    "ai_platform/portal/security",
    "ai_platform/portal/web",
    "ai_platform/portal/e2e",
)

REQUIRED_CODEOWNER_PATTERNS = {
    "/ai_platform/portal/control_plane/",
    "/ai_platform/portal/execution/",
    "/ai_platform/portal/identity/",
    "/ai_platform/portal/security/",
    "/ai_platform/portal/credentials/",
    "/ai_platform/portal/database/",
    "/ai_platform/portal/risk/",
    "/ai_platform/portal/contracts/",
    "/ai_platform/portal/web/",
    "/deploy/synology/",
}

STALE_PORTAL_CLAIMS = (
    "reserved for future ai trading portal implementation",
    "no portal runtime is implemented",
    "future fastapi modular backend",
    "future next.js/react portal",
)


def _codeowner_patterns() -> set[str]:
    patterns: set[str] = set()
    for raw_line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.add(line.split()[0])
    return patterns


def test_portal_readme_uses_current_repository_truth_sources() -> None:
    text = PORTAL_README.read_text(encoding="utf-8")
    lowered = text.lower()

    for stale_claim in STALE_PORTAL_CLAIMS:
        assert stale_claim not in lowered

    assert "partially implemented" in lowered
    assert "tools/portal_audit/ledger/index.json" in text
    assert "ARCHITECTURE_REGISTRY.yaml" in text
    assert "docs/ai_platform/portal/" in text
    assert "PAPER/dry-run is the only currently authorized operational trading mode" in text
    assert "LIVE remains unreachable/fail-closed" in text

    for relative_path in REQUIRED_IMPLEMENTED_ROOTS:
        assert (REPO_ROOT / relative_path).is_dir(), relative_path
        assert relative_path.removeprefix("ai_platform/portal/") + "/" in text


def test_portal_readme_points_to_living_exact_head_ledger() -> None:
    payload = json.loads(PORTAL_LEDGER.read_text(encoding="utf-8"))

    assert payload["mode"] == "living_exact_head_gate"
    assert payload["schema_version"] == "portal-completeness-ledger-v2"
    assert isinstance(payload.get("sections"), dict)
    assert {"backend_modules", "backend_routes", "frontend_pages", "runtime"}.issubset(
        payload["sections"]
    )


def test_codeowners_explicitly_covers_current_sensitive_portal_roots() -> None:
    patterns = _codeowner_patterns()

    assert "*" in patterns
    assert REQUIRED_CODEOWNER_PATTERNS.issubset(patterns)
