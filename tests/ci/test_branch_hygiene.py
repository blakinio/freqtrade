from __future__ import annotations

import pytest

from tools.ci.branch_hygiene import (
    BranchFacts,
    _next_link,
    evaluate_branch,
    evaluate_live_revalidation,
)


def facts(**overrides: object) -> BranchFacts:
    values: dict[str, object] = {
        "name": "feature/merged-work",
        "head_sha": "a" * 40,
        "age_days": 30,
        "protected": False,
        "has_open_pull_request": False,
        "has_merged_pull_request_at_head": False,
        "unique_commits": 0,
    }
    values.update(overrides)
    return BranchFacts(**values)  # type: ignore[arg-type]


def test_old_branch_without_unique_commits_is_eligible() -> None:
    decision = evaluate_branch(facts(), default_branch="develop")
    assert decision.eligible is True
    assert decision.reasons == ()


def test_exact_merged_pr_head_allows_squash_branch_cleanup() -> None:
    decision = evaluate_branch(
        facts(unique_commits=3, has_merged_pull_request_at_head=True),
        default_branch="develop",
    )
    assert decision.eligible is True
    assert decision.reasons == ()


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"name": "develop"}, "default_branch"),
        ({"protected": True}, "protected"),
        ({"has_open_pull_request": True}, "open_pull_request"),
        ({"age_days": 13}, "younger_than_retention"),
        ({"unique_commits": 1}, "contains_unmerged_unique_commits"),
        ({"name": "release/2026.08"}, "keep_pattern"),
    ],
)
def test_each_safety_predicate_retains_branch(
    overrides: dict[str, object],
    reason: str,
) -> None:
    decision = evaluate_branch(
        facts(**overrides),
        default_branch="develop",
        stale_days=14,
    )
    assert decision.eligible is False
    assert reason in decision.reasons


def test_moved_branch_after_merge_remains_unmerged() -> None:
    decision = evaluate_branch(
        facts(unique_commits=1, has_merged_pull_request_at_head=False),
        default_branch="develop",
    )
    assert decision.reasons == ("contains_unmerged_unique_commits",)


def test_multiple_reasons_are_preserved() -> None:
    decision = evaluate_branch(
        facts(
            name="hotfix/active",
            protected=True,
            has_open_pull_request=True,
            unique_commits=2,
        ),
        default_branch="develop",
    )
    assert decision.reasons == (
        "protected",
        "open_pull_request",
        "contains_unmerged_unique_commits",
        "keep_pattern",
    )


def test_live_revalidation_passes_when_state_is_unchanged() -> None:
    decision = evaluate_live_revalidation(
        facts(),
        live_head_sha="a" * 40,
        live_protected=False,
        live_has_open_pull_request=False,
    )
    assert decision.eligible is True
    assert decision.reasons == ()


def test_live_revalidation_fails_closed_on_races() -> None:
    decision = evaluate_live_revalidation(
        facts(),
        live_head_sha="b" * 40,
        live_protected=True,
        live_has_open_pull_request=True,
    )
    assert decision.eligible is False
    assert decision.reasons == (
        "head_moved_after_inventory",
        "became_protected_after_inventory",
        "open_pull_request_after_inventory",
    )


def test_next_link_parser() -> None:
    header = (
        '<https://api.github.com/example?page=2>; rel="next", '
        '<https://api.github.com/example?page=4>; rel="last"'
    )
    assert _next_link(header) == "https://api.github.com/example?page=2"
    assert _next_link("") is None
