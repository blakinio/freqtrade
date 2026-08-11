from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PORTAL_README = REPO_ROOT / "ai_platform" / "portal" / "README.md"
PORTAL_LEDGER = REPO_ROOT / "tools" / "portal_audit" / "ledger" / "index.json"
CODEOWNERS = REPO_ROOT / ".github" / "CODEOWNERS"
EXPECTED_PORTAL_OWNERS = ("@blakinio",)
_GLOB_META = "*?["

REQUIRED_IMPLEMENTED_ROOTS = (
    "ai_platform/portal/control_plane",
    "ai_platform/portal/execution",
    "ai_platform/portal/identity",
    "ai_platform/portal/security",
    "ai_platform/portal/web",
    "ai_platform/portal/e2e",
)

REQUIRED_CODEOWNER_PATTERNS = {
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


def _glob_literal_prefix(pattern: str) -> str:
    indexes = [pattern.find(marker) for marker in _GLOB_META if marker in pattern]
    return pattern[: min(indexes)] if indexes else pattern


def _unsupported_pattern_can_affect_root(pattern: str, protected_root: str) -> bool:
    # Unanchored CODEOWNERS rules may match at arbitrary path depth. Fail closed
    # instead of pretending to implement that matching language here.
    if not pattern.startswith("/"):
        return True

    prefix = _glob_literal_prefix(pattern)
    if prefix == pattern:
        return False
    # An anchored glob can affect the protected root if its literal prefix is
    # either an ancestor of the root or a descendant inside it. This catches
    # broad overrides (`/ai_platform/portal/**`) and child overrides such as
    # `/ai_platform/portal/control_plane/api*`.
    return protected_root.startswith(prefix) or prefix.startswith(protected_root)


def _matches_codeowner_rule(pattern: str, path: str, protected_root: str) -> bool:
    if pattern == "*":
        return True
    if any(marker in pattern for marker in _GLOB_META):
        if _unsupported_pattern_can_affect_root(pattern, protected_root):
            raise AssertionError(
                "unsupported CODEOWNERS glob may affect protected root: "
                f"{pattern} -> {protected_root}"
            )
        return False
    if not pattern.startswith("/"):
        raise AssertionError(
            f"unsupported unanchored CODEOWNERS rule may affect protected root: {pattern}"
        )
    if pattern.endswith("/"):
        return path.startswith(pattern)
    return path == pattern


def _effective_owners(
    rules: list[tuple[str, tuple[str, ...]]],
    path: str,
    protected_root: str,
) -> tuple[str, ...]:
    owners: tuple[str, ...] | None = None
    for pattern, rule_owners in rules:
        if _matches_codeowner_rule(pattern, path, protected_root):
            owners = rule_owners
    assert owners is not None, path
    return owners


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
    rules = _codeowner_rules()
    patterns = [pattern for pattern, _ in rules]

    assert patterns.count("*") == 1
    wildcard_index = patterns.index("*")
    assert patterns.count("/ai_platform/portal/") == 1
    portal_umbrella_index = patterns.index("/ai_platform/portal/")
    assert wildcard_index < portal_umbrella_index

    for required_pattern in REQUIRED_CODEOWNER_PATTERNS:
        assert patterns.count(required_pattern) == 1, required_pattern
        rule_index = patterns.index(required_pattern)
        assert wildcard_index < rule_index, required_pattern
        assert rules[rule_index][1] == EXPECTED_PORTAL_OWNERS, required_pattern

        probe_path = required_pattern + "__ownership_probe__"
        assert (
            _effective_owners(rules, probe_path, required_pattern) == EXPECTED_PORTAL_OWNERS
        ), required_pattern


def _assert_glob_fails_closed(pattern: str, protected_root: str) -> None:
    rules = _codeowner_rules()
    rules.append((pattern, ("@other",)))
    probe_path = protected_root + "__ownership_probe__"

    try:
        _effective_owners(rules, probe_path, protected_root)
    except AssertionError as exc:
        assert "unsupported CODEOWNERS glob may affect protected root" in str(exc)
    else:  # pragma: no cover - explicit regression sentinel
        raise AssertionError(f"protected-root glob must fail closed: {pattern}")


def test_effective_owner_guard_rejects_portal_overriding_globs() -> None:
    _assert_glob_fails_closed("/ai_platform/portal/**", "/ai_platform/portal/execution/")
    _assert_glob_fails_closed(
        "/ai_platform/portal/control_plane/api*",
        "/ai_platform/portal/control_plane/",
    )
