#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import Any

import repository_lifecycle as rl
import repository_lifecycle_destructive as destructive
import repository_lifecycle_preflight as preflight


MAX_LIVE_OPEN_PR_REVALIDATIONS = 750


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(rl.canonical_json(value), encoding="utf-8")


def _git_auth_env(client: rl.GitHubClient) -> dict[str, str]:
    basic = base64.b64encode(f"x-access-token:{client.token}".encode()).decode("ascii")
    env = os.environ.copy()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {basic}"
    return env


def _revalidate_immediately_before_delete(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    candidate: dict[str, Any],
    *,
    approved_base_sha: str,
) -> dict[str, Any]:
    current_base_sha = destructive.remote_ref_sha(client, policy["default_branch"])
    if current_base_sha != approved_base_sha:
        raise rl.LifecycleError(
            f"default branch moved during apply: expected {approved_base_sha}, got {current_base_sha}"
        )

    branch = candidate["branch"]
    expected_sha = candidate["sha"]
    current_sha = destructive.remote_ref_sha(client, branch)
    if current_sha is None:
        return {"status": "ALREADY_ABSENT", "branch": branch, "sha": expected_sha}
    if current_sha != expected_sha:
        raise destructive.RetainBranch(
            f"{branch}: remote SHA drifted from approved {expected_sha} to {current_sha}"
        )
    if destructive.open_pulls_for_branch(client, branch):
        raise destructive.RetainBranch(
            f"{branch}: a same-repository open PR now owns the branch"
        )
    return {"status": "DELETE_SAFE", "branch": branch, "sha": expected_sha}


def _delete_git_exact(
    client: rl.GitHubClient,
    branch: str,
    expected_sha: str,
) -> str:
    current_sha = destructive.remote_ref_sha(client, branch)
    if current_sha is None:
        return "ALREADY_ABSENT"
    if current_sha != expected_sha:
        raise destructive.RetainBranch(
            f"{branch}: remote SHA drifted before delete from {expected_sha} to {current_sha}"
        )

    remote = destructive.validate_remote(client)
    ref = f"refs/heads/{branch}"
    result = destructive._run_git(
        client,
        [
            "git",
            "push",
            "--porcelain",
            f"--force-with-lease={ref}:{expected_sha}",
            remote,
            f":{ref}",
        ],
        f"delete approved branch {branch}",
        env=_git_auth_env(client),
    )
    if result.returncode != 0:
        remote_sha = destructive.remote_ref_sha(client, branch)
        detail = (result.stderr or result.stdout).strip()[-500:]
        if remote_sha is None:
            raise rl.LifecycleError(
                f"delete returned failure but {branch} is absent; ambiguous: {detail}"
            )
        if remote_sha != expected_sha:
            raise destructive.RetainBranch(
                f"{branch}: delete lease rejected after remote moved to {remote_sha}"
            )
        protected_markers = (
            "protected branch hook declined",
            "gh006",
            "gh013",
            "repository rule",
            "cannot delete this protected branch",
        )
        if any(marker in detail.casefold() for marker in protected_markers):
            raise destructive.RetainBranch(
                f"{branch}: GitHub protection/rules rejected deletion"
            )
        raise rl.LifecycleError(f"delete push rejected for {branch}: {detail}")

    if destructive.remote_ref_sha(client, branch) is not None:
        raise rl.LifecycleError(f"post-delete Git verification found {branch} still present")
    return "DELETED"


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
    if manifest["candidate_count"] > MAX_LIVE_OPEN_PR_REVALIDATIONS:
        raise rl.LifecycleError(
            "source-head-safe candidate count exceeds the single-run live open-PR "
            f"revalidation budget ({manifest['candidate_count']} > "
            f"{MAX_LIVE_OPEN_PR_REVALIDATIONS}); split approval into bounded waves"
        )

    approved_base_sha = manifest["base_sha"]
    result: dict[str, Any] = {
        "schema_version": 2,
        "repository": client.repo,
        "approved_base_sha": approved_base_sha,
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
        "live_open_pr_revalidation_budget": MAX_LIVE_OPEN_PR_REVALIDATIONS,
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
            status = _revalidate_immediately_before_delete(
                client,
                policy,
                candidate,
                approved_base_sha=approved_base_sha,
            )
            if status["status"] == "ALREADY_ABSENT":
                result["already_absent"].append(candidate)
                _write(output, result)
                continue
            delete_status = _delete_git_exact(
                client,
                candidate["branch"],
                candidate["sha"],
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

        if delete_status == "ALREADY_ABSENT":
            result["already_absent"].append(candidate)
        else:
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
