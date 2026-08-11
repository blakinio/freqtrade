from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PORTAL_README = REPO_ROOT / "ai_platform" / "portal" / "README.md"
PORTAL_LEDGER = REPO_ROOT / "tools" / "portal_audit" / "ledger" / "index.json"
CODEOWNERS = REPO_ROOT / ".github" / "CODEOWNERS"
EXPECTED_PORTAL_OWNERS = ("@blakinio",)

REQUIRED_IMPLEMENTED_ROOTS = (
    "ai_platform/portal/control_plane",
    "ai_platform/portal/execution",
    "ai_platform/portal/identity",
    "ai_platform/portal/security",
    "ai_platform/portal/web",
    "ai_platform/portal/e2e",
)

PORTAL_OWNERSHIP_BLOCK_PATTERNS = {
    "/ai_platform/portal/",
    "/ai_platform/portal/control_plane/",
    "/ai_platform/portal/execution/",
    "/ai_platform/portal/execution_submission/",
    "/ai_platform/portal/bot_operations/",
    "/ai_platform/portal/exchange_connections/",
    "/ai_platform/portal/signal_control/",
    "/ai_platform/portal/identity/",
    "/ai_platform/portal/security/",
    "/ai_platform/portal/credentials/",
    "/ai_platform/portal/database/",
    "/ai_platform/portal/risk/",
    "/ai_platform/portal/deploy/",
    "/ai_platform/portal/contracts/",
    "/ai_platform/portal/web/",
}

REQUIRED_CODEOWNER_PATTERNS = PORTAL_OWNERSHIP_BLOCK_PATTERNS | {
    "/deploy/synology/",
}

STALE_PORTAL_CLAIMS = (
    "reserved for future ai trading portal implementation",
    "no portal runtime is implemented",
    "future fastapi modular backend",
    "future next.js/react portal",
)


def _codeowner_rules() -> list[tuple[str, tuple[str, ...]]]:
    rules: list[tuple[str, tuple[str, ...]]] = []
    for raw_line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        rules.append((fields[0], tuple(fields[1:])))
    return rules


def _assert_terminal_portal_ownership_block(
    rules: list[tuple[str, tuple[str, ...]]],
) -> None:
    patterns = [pattern for pattern, _ in rules]

    assert patterns.count("*") == 1
    wildcard_index = patterns.index("*")
    assert rules[wildcard_index][1] == EXPECTED_PORTAL_OWNERS

    assert patterns.count("/ai_platform/portal/") == 1
    portal_umbrella_index = patterns.index("/ai_platform/portal/")
    assert wildcard_index < portal_umbrella_index

    portal_block = rules[portal_umbrella_index:]
    portal_block_patterns = [pattern for pattern, _ in portal_block]
    assert len(portal_block_patterns) == len(PORTAL_OWNERSHIP_BLOCK_PATTERNS), (
        "Portal ownership block must be terminal; add unrelated CODEOWNERS rules above "
        "the /ai_platform/portal/ umbrella"
    )
    assert set(portal_block_patterns) == PORTAL_OWNERSHIP_BLOCK_PATTERNS, (
        "Portal ownership block contains an unexpected, missing or duplicate rule"
    )
    assert all(owners == EXPECTED_PORTAL_OWNERS for _, owners in portal_block)

    for required_pattern in REQUIRED_CODEOWNER_PATTERNS:
        assert patterns.count(required_pattern) == 1, required_pattern
        rule_index = patterns.index(required_pattern)
        assert rules[rule_index][1] == EXPECTED_PORTAL_OWNERS, required_pattern


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
    _assert_terminal_portal_ownership_block(_codeowner_rules())


def test_portal_ownership_guard_rejects_any_later_rule() -> None:
    # GitHub applies the last matching CODEOWNERS rule. The guard deliberately
    # avoids reimplementing GitHub's pattern language: once the Portal umbrella
    # begins, only the declared Portal rules may follow. Therefore globs,
    # slashless directory patterns, duplicate overrides and unrelated later
    # rules all fail closed before they can change effective Portal ownership.
    for later_rule in (
        "/ai_platform/portal/**",
        "/ai_platform/portal/execution",
        "/ai_platform/portal/control_plane/api*",
        "*.py",
        "/docs/**",
        "*",
    ):
        rules = _codeowner_rules()
        rules.append((later_rule, ("@other",)))
        try:
            _assert_terminal_portal_ownership_block(rules)
        except AssertionError:
            pass
        else:  # pragma: no cover - explicit regression sentinel
            raise AssertionError(f"later CODEOWNERS rule must fail closed: {later_rule}")
