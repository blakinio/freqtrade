from __future__ import annotations

import pytest

from tools.ci.branch_hygiene import BranchFacts, _next_link, evaluate_branch


def facts(**overrides: object) -> BranchFacts:
    values: dict[str, object] = {
        "name": "feature/merged-work",
        "age_days": 30,
        "protected": False,
        "has_open_pull_request": False,
        "unique_commits": 0,
    }
    values.update(overrides)
    return BranchFacts(**values)  # type: ignore[arg-type]


def test_only_old_fully_merged_unowned_branch_is_eligible() -> None:
    decision = evaluate_branch(facts(), default_branch="develop")
    assert decision.eligible is True
    assert decision.reasons == ()


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"name": "develop"}, "default_branch"),
        ({"protected": True}, "protected"),
        ({"has_open_pull_request": True}, "open_pull_request"),
        ({"age_days": 13}, "younger_than_retention"),
        ({"unique_commits": 1}, "contains_unique_commits"),
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
        "contains_unique_commits",
        "keep_pattern",
    )


def test_next_link_parser() -> None:
    header = (
        '<https://api.github.com/example?page=2>; rel="next", '
        '<https://api.github.com/example?page=4>; rel="last"'
    )
    assert _next_link(header) == "https://api.github.com/example?page=2"
    assert _next_link("") is None
