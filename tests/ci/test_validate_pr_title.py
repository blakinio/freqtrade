from __future__ import annotations

import json
import re

import pytest

from tools.ci.validate_pr_title import TitlePolicyError, main, validate_title


@pytest.mark.parametrize(
    "title",
    [
        "feat(portal): add deterministic session recovery",
        "fix(ci): bound online compatibility tests",
        "docs(architecture): record accepted decision",
        "ci(governance): enforce workflow lifecycle",
        "build(deps): bump pytest from 9.1.0 to 9.1.1",
        "revert: restore previous routing policy",
        "feat(protocol)!: remove legacy framing",
    ],
)
def test_valid_titles(title: str) -> None:
    validate_title(title)


@pytest.mark.parametrize(
    ("title", "message"),
    [
        ("fix: repair routing", "require a scope"),
        ("feature(portal): add page", "expected `type(scope): summary`"),
        ("Fix(ci): repair routing", "expected `type(scope): summary`"),
        ("fix(CI): repair routing", "expected `type(scope): summary`"),
        ("fix(ci): repair routing.", "must not end with a period"),
        (" fix(ci): repair routing", "leading or trailing whitespace"),
        ("fix(ci): #123 repair routing", "must not begin"),
        ("fix(ci): [WIP] repair routing", "must not begin"),
        ("fix(ci) repair routing", "expected `type(scope): summary`"),
    ],
)
def test_invalid_titles(title: str, message: str) -> None:
    with pytest.raises(TitlePolicyError, match=re.escape(message)):
        validate_title(title)


def test_title_length_limit() -> None:
    title = "docs(governance): " + ("a" * 90)
    with pytest.raises(TitlePolicyError, match="maximum"):
        validate_title(title)


def test_main_reads_github_event(tmp_path, capsys) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": {"title": "audit(repo): verify policy"}}),
        encoding="utf-8",
    )

    assert main(["--event", str(event_path)]) == 0
    assert "policy passed" in capsys.readouterr().out


def test_main_fails_closed_without_pull_request(tmp_path, capsys) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text("{}", encoding="utf-8")

    assert main(["--event", str(event_path)]) == 2
    assert "does not contain a pull request" in capsys.readouterr().err
