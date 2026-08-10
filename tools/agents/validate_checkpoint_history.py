#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


TASK_ROOT_PREFIX = "docs/agents/tasks/"
CHECKPOINT_HEADING = "## Context checkpoint"
TASK_ID_RE = re.compile(r"(?m)^task_id:\s*([^\s#]+)\s*$")
CHECKPOINT_RE = re.compile(
    r"(?ms)^## Context checkpoint\s*\n.*?```(?:yaml|yml)\s*\n(.*?)\n```"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Snapshot:
    task_id: str
    path: str
    commit: str
    checkpoint_version: int
    observation_counters_by_sha: dict[str, dict[str, int]]


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _task_paths_between(base: str, head: str) -> tuple[str, ...]:
    paths: set[str] = set()
    for commit in _git("rev-list", "--reverse", f"{base}..{head}").splitlines():
        for path in _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines():
            if path.startswith(TASK_ROOT_PREFIX) and path.endswith(".md"):
                paths.add(path)
    return tuple(sorted(paths))


def _show(commit: str, path: str) -> str | None:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _parse_snapshot(text: str, *, path: str, commit: str) -> Snapshot:
    task_match = TASK_ID_RE.search(text)
    if task_match is None:
        raise ValueError(f"{commit}:{path}: task_id is missing")
    checkpoint_match = CHECKPOINT_RE.search(text)
    if checkpoint_match is None:
        raise ValueError(f"{commit}:{path}: missing {CHECKPOINT_HEADING}")
    payload = yaml.safe_load(checkpoint_match.group(1))
    if not isinstance(payload, dict):
        raise ValueError(f"{commit}:{path}: checkpoint payload must be a mapping")

    version = payload.get("checkpoint_version")
    if type(version) is not int:
        raise ValueError(f"{commit}:{path}: checkpoint_version must be an integer")

    raw_history = payload.get("observation_counters_by_sha", {})
    if version == 2 and not isinstance(raw_history, dict):
        raise ValueError(f"{commit}:{path}: v2 observation history must be a mapping")

    history: dict[str, dict[str, int]] = {}
    if isinstance(raw_history, dict):
        for sha, counters in raw_history.items():
            if not isinstance(sha, str) or SHA_RE.fullmatch(sha) is None:
                raise ValueError(f"{commit}:{path}: invalid observation SHA {sha!r}")
            if not isinstance(counters, dict) or set(counters) != {"ci", "review"}:
                raise ValueError(f"{commit}:{path}: invalid observation counters for {sha}")
            ci = counters.get("ci")
            review = counters.get("review")
            if type(ci) is not int or ci < 0 or type(review) is not int or review < 0:
                raise ValueError(f"{commit}:{path}: counters for {sha} must be non-negative integers")
            history[sha] = {"ci": ci, "review": review}

    return Snapshot(
        task_id=task_match.group(1),
        path=path,
        commit=commit,
        checkpoint_version=version,
        observation_counters_by_sha=history,
    )


def _assert_monotonic(previous: Snapshot, current: Snapshot) -> list[str]:
    errors: list[str] = []
    for sha, old in previous.observation_counters_by_sha.items():
        new = current.observation_counters_by_sha.get(sha)
        if new is None:
            errors.append(
                f"{current.commit}:{current.path}: task {current.task_id} removed prior observation history for {sha}"
            )
            continue
        for key in ("ci", "review"):
            if new[key] < old[key]:
                errors.append(
                    f"{current.commit}:{current.path}: task {current.task_id} decreased {key} observations for {sha} from {old[key]} to {new[key]}"
                )
    return errors


def validate_history(base: str, head: str) -> list[str]:
    commits = _git("rev-list", "--reverse", f"{base}..{head}").splitlines()
    paths = _task_paths_between(base, head)
    errors: list[str] = []
    previous_by_task: dict[str, Snapshot] = {}

    for commit in commits:
        current_by_task: dict[str, Snapshot] = {}
        for path in paths:
            text = _show(commit, path)
            if text is None:
                continue
            try:
                snapshot = _parse_snapshot(text, path=path, commit=commit)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            current_by_task[snapshot.task_id] = snapshot

        for task_id, current in current_by_task.items():
            previous = previous_by_task.get(task_id)
            if previous is not None:
                if previous.checkpoint_version == 2 and current.checkpoint_version != 2:
                    errors.append(
                        f"{current.commit}:{current.path}: task {task_id} regressed checkpoint v2 to v{current.checkpoint_version}"
                    )
                if previous.checkpoint_version == 2 and current.checkpoint_version == 2:
                    errors.extend(_assert_monotonic(previous, current))
            previous_by_task[task_id] = current

    # Migration discriminator: every task record touched by this PR and still present
    # at the final head must be v2. Untouched legacy v1 records remain readable.
    for path in paths:
        text = _show(head, path)
        if text is None:
            continue
        try:
            snapshot = _parse_snapshot(text, path=path, commit=head)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if snapshot.checkpoint_version != 2:
            errors.append(
                f"{head}:{path}: touched/new task {snapshot.task_id} must migrate to checkpoint_version 2"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate monotonic durable task observation history across a PR commit range"
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    errors = validate_history(args.base, args.head)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Checkpoint history is monotonic and all touched task records use v2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
