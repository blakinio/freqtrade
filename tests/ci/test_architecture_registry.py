from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "ARCHITECTURE_REGISTRY.yaml"
DECISIONS_PATH = REPO_ROOT / "docs" / "ai_platform" / "portal" / "ARCHITECTURE_DECISIONS.md"
TERMINAL_FINDING_STATUSES = {"closed", "completed", "resolved", "superseded"}
PINNED_TERMINAL_FINDINGS = frozenset(
    {
        (1251, "FTAI-ARCH-001"),
        (1252, "FTAI-CI-001"),
        (1353, "FTAI-ARCH-RUNTIME-TRUSTED-STATE"),
        (1356, "FTAI-ARCH-REGISTRY-LIFECYCLE-GUARD"),
        (1357, "FTAI-ARCH-BOT-REVISION-STATE"),
    }
)


def _registry() -> dict[str, object]:
    payload = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _finding_identity(finding: object) -> tuple[int, str]:
    assert isinstance(finding, dict)
    issue = finding.get("issue")
    finding_id = finding.get("id")
    assert type(issue) is int and issue > 0
    assert isinstance(finding_id, str) and finding_id
    return issue, finding_id


def test_architecture_registry_resolved_findings_are_not_open() -> None:
    registry = _registry()
    review = registry["review"]
    assert isinstance(review, dict)
    resolved = review.get("resolved_findings", [])
    open_findings = registry.get("open_architecture_findings", [])
    assert isinstance(resolved, list)
    assert isinstance(open_findings, list)

    resolved_identities = [_finding_identity(finding) for finding in resolved]
    open_identities = [_finding_identity(finding) for finding in open_findings]
    resolved_identity_set = set(resolved_identities)
    open_identity_set = set(open_identities)
    resolved_issues = {issue for issue, _ in resolved_identities}
    open_issues = {issue for issue, _ in open_identities}
    resolved_finding_ids = {finding_id for _, finding_id in resolved_identities}
    open_finding_ids = {finding_id for _, finding_id in open_identities}
    pinned_issues = {issue for issue, _ in PINNED_TERMINAL_FINDINGS}
    pinned_finding_ids = {finding_id for _, finding_id in PINNED_TERMINAL_FINDINGS}

    assert len(resolved_identity_set) == len(resolved)
    assert len(open_identity_set) == len(open_findings)
    assert len(resolved_issues) == len(resolved)
    assert len(open_issues) == len(open_findings)
    assert len(resolved_finding_ids) == len(resolved)
    assert len(open_finding_ids) == len(open_findings)
    assert resolved_issues.isdisjoint(open_issues)
    assert resolved_finding_ids.isdisjoint(open_finding_ids)
    assert resolved_identity_set == PINNED_TERMINAL_FINDINGS
    assert pinned_issues.isdisjoint(open_issues)
    assert pinned_finding_ids.isdisjoint(open_finding_ids)
    assert all(
        isinstance(finding, dict) and finding.get("status") == "open" for finding in open_findings
    )
    assert all(
        isinstance(finding, dict) and finding.get("status") in TERMINAL_FINDING_STATUSES
        for finding in resolved
    )


def test_domain_open_findings_are_backed_by_top_level_open_findings() -> None:
    registry = _registry()
    open_findings = registry.get("open_architecture_findings", [])
    system_domains = registry.get("system_domains", {})
    assert isinstance(open_findings, list)
    assert isinstance(system_domains, dict)

    top_level = {_finding_identity(finding) for finding in open_findings}
    for domain_name, domain in system_domains.items():
        assert isinstance(domain_name, str)
        assert isinstance(domain, dict)
        domain_findings = domain.get("open_findings", [])
        assert isinstance(domain_findings, list)
        for finding in domain_findings:
            assert _finding_identity(finding) in top_level


def test_latest_accepted_architecture_decision_is_in_binding_log() -> None:
    registry = _registry()
    change = registry["latest_architecture_change"]
    assert isinstance(change, dict)

    status = change.get("status")
    assert isinstance(status, str) and status.startswith("accepted")
    decision = change.get("decision")
    assert isinstance(decision, str) and decision.startswith("ADR-")

    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    marker = f"## {decision} —"
    start = decisions.find(marker)
    assert start >= 0
    next_section = decisions.find("\n## ADR-", start + len(marker))
    section = decisions[start:] if next_section < 0 else decisions[start:next_section]
    assert "Status: `accepted`" in section


def test_registry_keeps_historical_review_provenance_separate_from_latest_change() -> None:
    registry = _registry()
    review = registry["review"]
    change = registry["latest_architecture_change"]
    assert isinstance(review, dict)
    assert isinstance(change, dict)

    assert review.get("status") == "completed"
    assert review.get("review_issue") == 1251
    audited_base_sha = review.get("audited_base_sha")
    synchronized_base_sha = review.get("synchronized_base_sha")
    latest_base_sha = change.get("base_sha")
    assert isinstance(audited_base_sha, str) and len(audited_base_sha) == 40
    assert isinstance(synchronized_base_sha, str) and len(synchronized_base_sha) == 40
    assert isinstance(latest_base_sha, str) and len(latest_base_sha) == 40
    assert audited_base_sha != latest_base_sha
    assert synchronized_base_sha != latest_base_sha
