#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

import repository_lifecycle as rl
import repository_lifecycle_preflight as preflight


APPROVAL_WAVE_SIZE = 400


def _validate_preflight(manifest: dict[str, Any]) -> None:
    accounted = (
        manifest["candidate_count"]
        + manifest["retained_count"]
        + manifest["already_absent_count"]
    )
    if accounted != manifest["source_inventory_candidate_count"]:
        raise rl.LifecycleError("historical preflight accounting mismatch")
    if any(
        item["classification"] not in rl.DELETION_CLASSIFICATIONS
        for item in manifest["candidates"]
    ):
        raise rl.LifecycleError("historical preflight widened deletion classifications")


def approval_wave_manifest(
    manifest: dict[str, Any],
    candidate_count: int | None = None,
) -> dict[str, Any]:
    _validate_preflight(manifest)
    total_safe = manifest["candidate_count"]
    if not isinstance(total_safe, int) or total_safe < 0:
        raise rl.LifecycleError("preflight candidate_count is invalid")
    if total_safe == 0:
        raise rl.LifecycleError("no source-head-safe candidates remain for approval")
    count = min(APPROVAL_WAVE_SIZE, total_safe) if candidate_count is None else candidate_count
    if not isinstance(count, int) or count < 1 or count > APPROVAL_WAVE_SIZE:
        raise rl.LifecycleError(
            f"approval wave candidate_count must be between 1 and {APPROVAL_WAVE_SIZE}"
        )
    if count > total_safe:
        raise rl.LifecycleError(
            f"approval wave candidate_count {count} exceeds current safe set {total_safe}"
        )
    candidates = manifest["candidates"][:count]
    return {
        "candidate_count": count,
        "candidates": candidates,
        "entries_sha256": rl.entries_sha256(candidates),
        "policy_sha256": manifest["policy_sha256"],
    }


def build_approval_from_manifest(
    manifest: dict[str, Any],
    policy: dict[str, Any],
    *,
    run_id: str,
) -> dict[str, Any]:
    wave = approval_wave_manifest(manifest)
    base_sha = manifest["base_sha"]
    total_safe = manifest["candidate_count"]
    return {
        "apply_on_develop": True,
        "candidate_count": wave["candidate_count"],
        "confirmation": (
            f"DELETE_EXACT_REVIEWED_TERMINAL_BRANCHES_ISSUE_{policy['issue']}"
        ),
        "entries_sha256": wave["entries_sha256"],
        "issue": policy["issue"],
        "policy_sha256": wave["policy_sha256"],
        "repository": policy["repository"],
        "review_summary": (
            "Agent-authorized bounded wave from the exact source-head-safe historical "
            f"preflight; develop={base_sha}, workflow_run={run_id}, raw_terminal="
            f"{manifest['source_inventory_candidate_count']}, safe_total={total_safe}, "
            f"wave={wave['candidate_count']}, retained={manifest['retained_count']}, "
            f"already_absent={manifest['already_absent_count']}, wave_limit="
            f"{APPROVAL_WAVE_SIZE}. Merge remains gated by a fresh preflight and exact "
            "prefix digest validation."
        ),
        "reviewed_at": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "reviewed_by": "agent:FTAI-20260815-repository-lifecycle-hygiene",
        "schema_version": 1,
    }


def build_approval(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    manifest = preflight.build_preflight(client, policy, root)
    return build_approval_from_manifest(
        manifest,
        policy,
        run_id=os.environ.get("GITHUB_RUN_ID", "unknown"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--policy", default=str(rl.POLICY_PATH))
    parser.add_argument("--manifest")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    policy = rl.load_json(root / args.policy)
    rl.validate_policy(policy)

    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        approval = build_approval_from_manifest(
            manifest,
            policy,
            run_id=os.environ.get("GITHUB_RUN_ID", "unknown"),
        )
    else:
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
