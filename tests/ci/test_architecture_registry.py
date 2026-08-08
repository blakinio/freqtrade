import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "ARCHITECTURE_REGISTRY.yaml"
DECISIONS_PATH = REPO_ROOT / "docs" / "ai_platform" / "portal" / "ARCHITECTURE_DECISIONS.md"
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _registry() -> dict[str, object]:
    payload = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_architecture_registry_resolved_findings_are_not_open() -> None:
    registry = _registry()
    review = registry["review"]
    assert isinstance(review, dict)
    resolved = review.get("resolved_findings", [])
    open_findings = registry.get("open_architecture_findings", [])
    assert isinstance(resolved, list)
    assert isinstance(open_findings, list)

    resolved_issues = {
        int(finding["issue"])
        for finding in resolved
        if isinstance(finding, dict) and "issue" in finding
    }
    open_issues = {
        int(finding["issue"])
        for finding in open_findings
        if isinstance(finding, dict) and "issue" in finding
    }

    assert resolved_issues.isdisjoint(open_issues)
    assert all(
        isinstance(finding, dict) and finding.get("status") == "open"
        for finding in open_findings
    )


def test_latest_accepted_architecture_decision_is_in_binding_log() -> None:
    registry = _registry()
    change = registry["latest_architecture_change"]
    assert isinstance(change, dict)
    assert change.get("status") == "accepted"

    decision = change.get("decision")
    assert isinstance(decision, str) and decision.startswith("ADR-")
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    marker = f"## {decision} —"
    start = decisions.find(marker)
    assert start >= 0
    next_section = decisions.find("\n## ADR-", start + len(marker))
    section = decisions[start:] if next_section < 0 else decisions[start:next_section]
    assert "Status: `accepted`" in section


def test_registry_keeps_review_provenance_separate_from_latest_change() -> None:
    registry = _registry()
    review = registry["review"]
    change = registry["latest_architecture_change"]
    assert isinstance(review, dict)
    assert isinstance(change, dict)

    assert review.get("status") == "completed"
    audited_base_sha = review.get("audited_base_sha")
    synchronized_base_sha = review.get("synchronized_base_sha")
    change_base_sha = change.get("base_sha")
    assert isinstance(audited_base_sha, str) and GIT_SHA_RE.fullmatch(audited_base_sha)
    assert isinstance(synchronized_base_sha, str) and GIT_SHA_RE.fullmatch(synchronized_base_sha)
    assert isinstance(change_base_sha, str) and GIT_SHA_RE.fullmatch(change_base_sha)

    # Preserve the proven historical #1251 review while that review remains the
    # registry's declared review identity. A later bounded review may replace
    # review_issue and its associated provenance together.
    if review.get("review_issue") == 1251:
        assert audited_base_sha == "cbf9f57ea8d5783f85d19fe0f8557dfe3178705a"

    assert change.get("issue") == 1358
    assert change.get("decision") == "ADR-020"
