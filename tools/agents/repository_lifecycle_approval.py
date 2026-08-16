#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Any

import repository_lifecycle as rl
import repository_lifecycle_preflight as preflight


def build_approval(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    manifest = preflight.build_preflight(client, policy, root)
    accounted = (
        manifest["candidate_count"] + manifest["retained_count"] + manifest["already_absent_count"]
    )
    if accounted != manifest["source_inventory_candidate_count"]:
        raise rl.LifecycleError("historical preflight accounting mismatch")
    if any(
        item["classification"] not in rl.DELETION_CLASSIFICATIONS for item in manifest["candidates"]
    ):
        raise rl.LifecycleError("historical preflight widened deletion classifications")
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown")
    base_sha = manifest["base_sha"]
    return {
        "apply_on_develop": True,
        "candidate_count": manifest["candidate_count"],
        "confirmation": (f"DELETE_EXACT_REVIEWED_TERMINAL_BRANCHES_ISSUE_{policy['issue']}"),
        "entries_sha256": manifest["entries_sha256"],
        "issue": policy["issue"],
        "policy_sha256": manifest["policy_sha256"],
        "repository": policy["repository"],
        "review_summary": (
            "Agent-authorized proposal from the exact source-head-safe historical "
            f"preflight; develop={base_sha}, workflow_run={run_id}, raw_terminal="
            f"{manifest['source_inventory_candidate_count']}, safe="
            f"{manifest['candidate_count']}, retained={manifest['retained_count']}, "
            f"already_absent={manifest['already_absent_count']}. Merge remains gated "
            "by a fresh preflight and exact digest validation."
        ),
        "reviewed_at": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "reviewed_by": "agent:FTAI-20260815-repository-lifecycle-hygiene",
        "schema_version": 1,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--policy", default=str(rl.POLICY_PATH))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
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
    approval = build_approval(client, policy, root)
    Path(args.output).write_text(rl.canonical_json(approval), encoding="utf-8")
    print(
        f"approval proposal: {approval['candidate_count']} candidates, "
        f"digest={approval['entries_sha256']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (rl.LifecycleError, rl.ApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
