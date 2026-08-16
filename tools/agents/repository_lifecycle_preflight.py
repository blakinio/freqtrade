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


FETCH_BATCH_SIZE = 100
LOCAL_REF_ROOT = "refs/lifecycle-preflight"


def _git_auth_env(client: rl.GitHubClient) -> dict[str, str]:
    basic = base64.b64encode(f"x-access-token:{client.token}".encode()).decode("ascii")
    env = os.environ.copy()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {basic}"
    return env


def _git(
    client: rl.GitHubClient,
    args: list[str],
    purpose: str,
    *,
    env: dict[str, str] | None = None,
) -> str:
    result = destructive._run_git(client, args, purpose, env=env)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-500:]
        raise rl.LifecycleError(f"{purpose} failed: {detail}")
    return result.stdout


def _task_tree(client: rl.GitHubClient, ref: str) -> dict[str, str]:
    output = _git(
        client,
        ["git", "ls-tree", "-r", "--full-tree", ref, "--", str(rl.ACTIVE_TASKS_PATH)],
        f"list active task tree at {ref}",
    )
    result: dict[str, str] = {}
    for line in output.splitlines():
        try:
            metadata, path = line.split("\t", 1)
        except ValueError as exc:
            raise rl.LifecycleError(f"unexpected git ls-tree row: {line!r}") from exc
        parts = metadata.split()
        if len(parts) != 3 or parts[1] != "blob":
            continue
        blob_sha = parts[2]
        if path.endswith(".md") and rl.FULL_SHA_RE.fullmatch(blob_sha):
            result[path] = blob_sha
    return result


def _blob_claims(client: rl.GitHubClient, blob_sha: str) -> set[str]:
    text = _git(
        client,
        ["git", "cat-file", "blob", blob_sha],
        f"read active task blob {blob_sha}",
    )
    return destructive._claims_from_text(text)


def _tree_claims(client: rl.GitHubClient, directory: dict[str, str]) -> set[str]:
    claims: set[str] = set()
    for blob_sha in sorted(set(directory.values())):
        claims.update(_blob_claims(client, blob_sha))
    return claims


def _source_only_claims(
    client: rl.GitHubClient,
    source_directory: dict[str, str],
    base_directory: dict[str, str],
    base_claims: set[str],
) -> set[str]:
    claims = set(base_claims)
    for path, blob_sha in sorted(source_directory.items()):
        if base_directory.get(path) == blob_sha:
            continue
        claims.update(_blob_claims(client, blob_sha))
    return claims


def _develop_entry(inventory: dict[str, Any], branch: str) -> dict[str, Any]:
    for item in inventory["entries"]:
        if item.get("branch") == branch:
            return item
    raise rl.LifecycleError(f"default branch {branch} missing from inventory")


def _fetch_snapshot_refs(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    inventory: dict[str, Any],
) -> tuple[str, dict[str, str], list[str]]:
    remote = destructive.validate_remote(client)
    env = _git_auth_env(client)
    base = _develop_entry(inventory, policy["default_branch"])
    base_sha = base.get("sha")
    if not isinstance(base_sha, str) or not rl.FULL_SHA_RE.fullmatch(base_sha):
        raise rl.LifecycleError("default branch inventory SHA is invalid")

    mappings: list[tuple[str, str, str]] = [
        (f"refs/heads/{policy['default_branch']}", f"{LOCAL_REF_ROOT}/base", base_sha)
    ]
    source_refs: dict[str, str] = {}
    index = 0
    for candidate in inventory["candidates"]:
        if candidate["classification"] != "TERMINAL_CLOSED_UNMERGED":
            continue
        local_ref = f"{LOCAL_REF_ROOT}/source-{index:04d}"
        mappings.append((f"refs/heads/{candidate['branch']}", local_ref, candidate["sha"]))
        source_refs[candidate["branch"]] = local_ref
        index += 1

    local_refs = [local_ref for _, local_ref, _ in mappings]
    for local_ref in local_refs:
        destructive._run_git(
            client,
            ["git", "update-ref", "-d", local_ref],
            f"clear local preflight ref {local_ref}",
        )

    for offset in range(0, len(mappings), FETCH_BATCH_SIZE):
        batch = mappings[offset : offset + FETCH_BATCH_SIZE]
        refspecs = [f"+{remote_ref}:{local_ref}" for remote_ref, local_ref, _ in batch]
        _git(
            client,
            [
                "git",
                "fetch",
                "--no-tags",
                "--no-recurse-submodules",
                "--no-write-fetch-head",
                "--depth=1",
                remote,
                *refspecs,
            ],
            f"fetch immutable lifecycle snapshot batch {offset // FETCH_BATCH_SIZE + 1}",
            env=env,
        )
        for _, local_ref, expected_sha in batch:
            actual_sha = _git(
                client,
                ["git", "rev-parse", "--verify", f"{local_ref}^{{commit}}"],
                f"verify local snapshot {local_ref}",
            ).strip()
            if actual_sha != expected_sha:
                raise rl.LifecycleError(
                    f"source ref drift during preflight: {local_ref} expected {expected_sha}, got {actual_sha}"
                )

    return base_sha, source_refs, local_refs


def _cleanup_local_refs(client: rl.GitHubClient, refs: list[str]) -> None:
    for local_ref in refs:
        destructive._run_git(
            client,
            ["git", "update-ref", "-d", local_ref],
            f"cleanup local preflight ref {local_ref}",
        )


def build_preflight(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    inventory = rl.build_inventory(client, policy, root)
    base_sha, source_refs, local_refs = _fetch_snapshot_refs(client, policy, inventory)

    safe: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    try:
        base_directory = _task_tree(client, f"{LOCAL_REF_ROOT}/base")
        base_claims = _tree_claims(client, base_directory)

        for candidate in inventory["candidates"]:
            branch = candidate["branch"]
            if branch in base_claims:
                retained.append(
                    {
                        "branch": branch,
                        "classification": candidate["classification"],
                        "pr_numbers": candidate["pr_numbers"],
                        "reason": "active task claim exists on current default branch snapshot",
                        "sha": candidate["sha"],
                    }
                )
                continue

            if candidate["classification"] == "TERMINAL_CLOSED_UNMERGED":
                source_ref = source_refs.get(branch)
                if source_ref is None:
                    raise rl.LifecycleError(f"missing immutable source snapshot for {branch}")
                source_directory = _task_tree(client, source_ref)
                source_claims = _source_only_claims(
                    client,
                    source_directory,
                    base_directory,
                    base_claims,
                )
                if branch in source_claims:
                    retained.append(
                        {
                            "branch": branch,
                            "classification": candidate["classification"],
                            "pr_numbers": candidate["pr_numbers"],
                            "reason": "active task claim exists on exact immutable source head",
                            "sha": candidate["sha"],
                        }
                    )
                    continue
            safe.append(candidate)

        final_inventory = rl.build_inventory(client, policy, root)
        if final_inventory["candidate_count"] != inventory["candidate_count"]:
            raise rl.LifecycleError("raw candidate count drifted during historical preflight")
        if final_inventory["entries_sha256"] != inventory["entries_sha256"]:
            raise rl.LifecycleError("raw candidate digest drifted during historical preflight")
        final_base_sha = destructive.remote_ref_sha(client, policy["default_branch"])
        if final_base_sha != base_sha:
            raise rl.LifecycleError(
                f"default branch moved during historical preflight: expected {base_sha}, got {final_base_sha}"
            )
    finally:
        _cleanup_local_refs(client, local_refs)

    return {
        "schema_version": 2,
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
        "already_absent_count": 0,
        "already_absent": [],
        "snapshot_transport": "git-immutable-refs",
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
        f"{result['retained_count']} retained, {result['already_absent_count']} absent, "
        f"transport={result['snapshot_transport']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (rl.LifecycleError, rl.ApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
