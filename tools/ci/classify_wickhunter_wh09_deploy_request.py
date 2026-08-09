from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


CHANGE_FIELDS = ("added", "modified", "removed")
_SHA_RE = re.compile(r"[0-9a-f]{40}")


class DeployRequestClassificationError(RuntimeError):
    """Raised when the pushed revision range cannot be proven safely."""


def diagnostic_request_changed(event: dict[str, Any], target_path: str) -> bool:
    """Legacy pure helper retained for focused exact-element regression coverage.

    The workflow CLI does not trust these arrays because GitHub Actions omits them
    from the push payload exposed to workflows. Runtime classification is derived
    from the exact Git before/after range instead.
    """

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


def _required_sha(event: dict[str, Any], field: str) -> str:
    value = event.get(field)
    if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
        raise DeployRequestClassificationError(f"push event {field} must be a lowercase Git SHA")
    if value == "0" * 40:
        raise DeployRequestClassificationError(f"push event {field} cannot be the null Git SHA")
    return value


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        raise DeployRequestClassificationError(f"git command failed: {' '.join(args)}") from exc


def _commit_exists(repo_root: Path, sha: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise DeployRequestClassificationError("git command failed: cat-file") from exc
    return completed.returncode == 0


def _require_ancestor(repo_root: Path, before: str, after: str) -> None:
    try:
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", before, after],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise DeployRequestClassificationError("git command failed: merge-base") from exc
    if completed.returncode == 0:
        return
    if completed.returncode == 1:
        raise DeployRequestClassificationError(
            "push event before commit is not an ancestor of after commit"
        )
    raise DeployRequestClassificationError("git command failed: merge-base --is-ancestor")


def _ensure_push_range_available(repo_root: Path, before: str, after: str) -> None:
    head = _git(repo_root, "rev-parse", "HEAD").stdout.strip()
    if head != after:
        raise DeployRequestClassificationError(
            "checked-out HEAD does not match push event after SHA"
        )
    if not _commit_exists(repo_root, after):
        raise DeployRequestClassificationError("push event after commit is unavailable")
    if not _commit_exists(repo_root, before):
        shallow = _git(repo_root, "rev-parse", "--is-shallow-repository").stdout.strip()
        if shallow != "true":
            raise DeployRequestClassificationError("push event before commit is unavailable")
        _git(repo_root, "fetch", "--no-tags", "--prune", "--unshallow", "origin")
        if not _commit_exists(repo_root, before):
            raise DeployRequestClassificationError(
                "push event before commit is unavailable after unshallow"
            )
    if before == after:
        raise DeployRequestClassificationError("push event before and after commits are identical")
    _require_ancestor(repo_root, before, after)


def changed_paths_for_push(event: dict[str, Any], repo_root: Path) -> tuple[str, ...]:
    before = _required_sha(event, "before")
    after = _required_sha(event, "after")
    _ensure_push_range_available(repo_root, before, after)
    completed = _git(
        repo_root,
        "log",
        "--format=",
        "--name-only",
        "--no-renames",
        "--diff-merges=first-parent",
        "-z",
        f"{before}..{after}",
        "--",
    )
    return tuple(dict.fromkeys(item for item in completed.stdout.split("\0") if item))


def diagnostic_request_changed_in_push(
    event: dict[str, Any],
    target_path: str,
    *,
    repo_root: Path,
) -> bool:
    if not target_path or "\x00" in target_path:
        raise DeployRequestClassificationError("target path is invalid")
    return target_path in changed_paths_for_push(event, repo_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--target-path", required=True)
    parser.add_argument("--github-output", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path())
    args = parser.parse_args()

    event = json.loads(args.event.read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise SystemExit("GitHub event payload must be an object")
    try:
        changed = diagnostic_request_changed_in_push(
            event,
            args.target_path,
            repo_root=args.repo_root.resolve(),
        )
    except DeployRequestClassificationError as exc:
        raise SystemExit(f"unsafe WH09 deployment classification: {exc}") from exc
    with args.github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"diagnostic_v4={'true' if changed else 'false'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
