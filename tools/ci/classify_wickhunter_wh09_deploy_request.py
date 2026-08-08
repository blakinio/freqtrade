from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CHANGE_FIELDS = ("added", "modified", "removed")


def diagnostic_request_changed(event: dict[str, Any], target_path: str) -> bool:
    """Return true only when target_path is an exact changed-file array element."""

    commits = event.get("commits")
    if not isinstance(commits, list):
        return False
    for commit in commits:
        if not isinstance(commit, dict):
            continue
        for field in CHANGE_FIELDS:
            paths = commit.get(field)
            if isinstance(paths, list) and target_path in paths:
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--target-path", required=True)
    parser.add_argument("--github-output", required=True, type=Path)
    args = parser.parse_args()

    event = json.loads(args.event.read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise SystemExit("GitHub event payload must be an object")
    changed = diagnostic_request_changed(event, args.target_path)
    with args.github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"diagnostic_v4={'true' if changed else 'false'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
