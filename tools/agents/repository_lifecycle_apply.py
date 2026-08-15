#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import repository_lifecycle as rl
import repository_lifecycle_destructive as destructive
import repository_lifecycle_preflight as preflight


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(rl.canonical_json(value), encoding="utf-8")


def apply_reviewed_safe_manifest(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
    output: Path,
) -> dict[str, Any]:
    manifest = preflight.build_preflight(client, policy, root)
    approval = rl.load_json(root / rl.APPROVAL_PATH)
    rl.validate_approval(approval, manifest, policy)
    if approval["apply_on_develop"] is not True:
        raise rl.LifecycleError("reviewed approval is not activated for develop")

    result: dict[str, Any] = {
        "schema_version": 1,
        "repository": client.repo,
        "reviewed_candidate_count": manifest["candidate_count"],
        "entries_sha256": manifest["entries_sha256"],
        "policy_sha256": manifest["policy_sha256"],
        "source_inventory_candidate_count": manifest["source_inventory_candidate_count"],
        "preflight_retained_count": manifest["retained_count"],
        "preflight_retained": manifest["retained"],
        "deleted": [],
        "already_absent": manifest["already_absent"],
        "retained_after_approval": [],
        "recovery_test": None,
        "result": "RUNNING",
    }
    _write(output, result)

    result["recovery_test"] = destructive.safe_recovery_test(
        client,
        policy["default_branch"],
        policy["issue"],
    )
    _write(output, result)

    for candidate in manifest["candidates"]:
        try:
            status = destructive.revalidate_candidate(
                client,
                policy,
                candidate,
                base_ref=policy["default_branch"],
            )
        except destructive.RetainBranch as exc:
            result["retained_after_approval"].append(
                {
                    "branch": candidate["branch"],
                    "sha": candidate["sha"],
                    "reason": str(exc),
                }
            )
            _write(output, result)
            continue
        if status["status"] == "ALREADY_ABSENT":
            result["already_absent"].append(candidate)
            _write(output, result)
            continue
        destructive.delete_branch_exact(client, candidate["branch"], candidate["sha"])
        result["deleted"].append(candidate)
        _write(output, result)

    result["result"] = "PASS"
    _write(output, result)
    return result


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
    result = apply_reviewed_safe_manifest(
        client,
        policy,
        root,
        Path(args.output),
    )
    print(
        f"apply PASS: {len(result['deleted'])} deleted, "
        f"{len(result['already_absent'])} already absent, "
        f"{len(result['retained_after_approval'])} retained after approval"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (rl.LifecycleError, rl.ApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
