#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import repository_lifecycle as rl
import repository_lifecycle_destructive as destructive


def build_preflight(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    inventory = rl.build_inventory(client, policy, root)
    base_sha = client.get_ref_sha(policy["default_branch"])
    if base_sha is None:
        raise rl.LifecycleError("default branch missing during historical deletion preflight")
    base_directory, base_claims = destructive.claim_snapshot(client, base_sha)

    safe: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    already_absent: list[dict[str, Any]] = []
    for candidate in inventory["candidates"]:
        try:
            status = destructive.revalidate_candidate(
                client,
                policy,
                candidate,
                base_ref=policy["default_branch"],
                base_directory=base_directory,
                base_claims=base_claims,
            )
        except destructive.RetainBranch as exc:
            retained.append(
                {
                    "branch": candidate["branch"],
                    "classification": candidate["classification"],
                    "pr_numbers": candidate["pr_numbers"],
                    "reason": str(exc),
                    "sha": candidate["sha"],
                }
            )
            continue
        if status["status"] == "ALREADY_ABSENT":
            already_absent.append(candidate)
        else:
            safe.append(candidate)

    return {
        "schema_version": 1,
        "repository": client.repo,
        "base_sha": base_sha,
        "source_inventory_branch_count": inventory["branch_count"],
        "source_inventory_candidate_count": inventory["candidate_count"],
        "candidate_count": len(safe),
        "candidates": safe,
        "entries_sha256": rl.entries_sha256(safe),
        "policy_sha256": inventory["policy_sha256"],
        "retained_count": len(retained),
        "retained": retained,
        "already_absent_count": len(already_absent),
        "already_absent": already_absent,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--policy", default=str(rl.POLICY_PATH))
    p.add_argument("--output", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    policy = rl.load_json(root / args.policy)
    rl.validate_policy(policy)
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", policy["repository"])
    if not token:
        raise rl.LifecycleError("GITHUB_TOKEN is required")
    if repo.casefold() != policy["repository"].casefold():
        raise rl.LifecycleError(f"GITHUB_REPOSITORY mismatch: {repo}")
    client = rl.GitHubClient(repo, token, root=root)
    result = build_preflight(client, policy, root)
    Path(args.output).write_text(rl.canonical_json(result), encoding="utf-8")
    print(
        f"historical preflight: {result['candidate_count']} safe, "
        f"{result['retained_count']} retained, {result['already_absent_count']} absent"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (rl.LifecycleError, rl.ApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
