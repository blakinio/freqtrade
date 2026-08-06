from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


ALLOWED_TYPES = (
    "feat",
    "fix",
    "docs",
    "refactor",
    "test",
    "perf",
    "build",
    "ci",
    "chore",
    "ops",
    "audit",
    "revert",
)
SCOPED_TYPES = frozenset({"feat", "fix", "ops", "audit"})
MAX_TITLE_LENGTH = 100
TITLE_RE = re.compile(
    rf"^(?P<type>{'|'.join(ALLOWED_TYPES)})"
    r"(?:\((?P<scope>[a-z0-9][a-z0-9._/-]*)\))?"
    r"(?P<breaking>!)?: (?P<summary>\S(?:.*\S)?)$"
)


class TitlePolicyError(ValueError):
    """Raised when a pull-request title violates repository policy."""


def validate_title(title: str) -> None:
    """Validate one pull-request title against the repository policy."""
    if title != title.strip():
        raise TitlePolicyError("title must not have leading or trailing whitespace")
    if len(title) > MAX_TITLE_LENGTH:
        raise TitlePolicyError(f"title is {len(title)} characters; maximum is {MAX_TITLE_LENGTH}")

    match = TITLE_RE.fullmatch(title)
    if match is None:
        allowed = ", ".join(ALLOWED_TYPES)
        raise TitlePolicyError(
            f"expected `type(scope): summary` or `type: summary`; allowed types: {allowed}"
        )

    title_type = match.group("type")
    scope = match.group("scope")
    summary = match.group("summary")

    if title_type in SCOPED_TYPES and scope is None:
        raise TitlePolicyError(f"`{title_type}` titles require a scope")
    if summary.endswith("."):
        raise TitlePolicyError("summary must not end with a period")
    if summary.startswith(("[", "#")):
        raise TitlePolicyError("summary must not begin with an issue or bracket prefix")


def _title_from_event(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TitlePolicyError(f"cannot read GitHub event payload: {exc}") from exc

    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        raise TitlePolicyError("event payload does not contain a pull request")
    title = pull_request.get("title")
    if not isinstance(title, str) or not title:
        raise TitlePolicyError("pull request title is missing from the event payload")
    return title


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the pull-request title.")
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--title", help="Title to validate directly.")
    source.add_argument(
        "--event",
        type=Path,
        help="GitHub event JSON containing pull_request.title.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    event_path = args.event
    if args.title is not None:
        title = args.title
    else:
        if event_path is None:
            raw_event_path = os.environ.get("GITHUB_EVENT_PATH")
            if not raw_event_path:
                print(
                    "PR title validation failed: provide --title, --event, or GITHUB_EVENT_PATH",
                    file=sys.stderr,
                )
                return 2
            event_path = Path(raw_event_path)
        try:
            title = _title_from_event(event_path)
        except TitlePolicyError as exc:
            print(f"PR title validation failed: {exc}", file=sys.stderr)
            return 2

    try:
        validate_title(title)
    except TitlePolicyError as exc:
        print(f"PR title validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"PR title policy passed: {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
