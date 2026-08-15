#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import repository_lifecycle as rl


class RetainBranch(rl.LifecycleError):
    """A reviewed branch is no longer safe to delete and must be retained."""


def _decode_content(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    encoding = payload.get("encoding")
    if not isinstance(content, str) or encoding != "base64":
        raise rl.LifecycleError("GitHub contents response lacks base64 file content")
    try:
        return base64.b64decode(content, validate=False).decode("utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover - defensive boundary
        raise rl.LifecycleError("unable to decode task record content") from exc


def _claims_from_text(text: str) -> set[str]:
    status_match = rl.TASK_STATUS_RE.search(text)
    if status_match and status_match.group(1).strip().lower() == "completed":
        return set()
    return {match.group(1).strip() for match in rl.TASK_BRANCH_RE.finditer(text)}


def task_directory(client: rl.GitHubClient, ref: str) -> dict[str, str]:
    if not rl.FULL_SHA_RE.fullmatch(ref):
        raise rl.LifecycleError("task-directory ref must be an immutable full SHA")
    path = urllib.parse.quote(str(rl.ACTIVE_TASKS_PATH), safe="/")
    try:
        payload, _ = client.request(
            "GET",
            f"/repos/{client.repo}/contents/{path}?ref={ref}",
        )
    except rl.ApiError as exc:
        if exc.status == 404:
            return {}
        raise
    if not isinstance(payload, list):
        raise rl.LifecycleError("active-task directory response must be a list")
    result: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict) or item.get("type") != "file":
            continue
        item_path = item.get("path")
        item_sha = item.get("sha")
        if (
            isinstance(item_path, str)
            and item_path.endswith(".md")
            and isinstance(item_sha, str)
            and rl.FULL_SHA_RE.fullmatch(item_sha)
        ):
            result[item_path] = item_sha
    return result


def task_file_claims(client: rl.GitHubClient, ref: str, path: str) -> set[str]:
    encoded = urllib.parse.quote(path, safe="/")
    payload, _ = client.request(
        "GET",
        f"/repos/{client.repo}/contents/{encoded}?ref={ref}",
    )
    if not isinstance(payload, dict):
        raise rl.LifecycleError("task record response must be an object")
    return _claims_from_text(_decode_content(payload))


def claim_snapshot(client: rl.GitHubClient, ref: str) -> tuple[dict[str, str], set[str]]:
    directory = task_directory(client, ref)
    claims: set[str] = set()
    for path in sorted(directory):
        claims.update(task_file_claims(client, ref, path))
    return directory, claims


def source_only_claims(
    client: rl.GitHubClient,
    source_ref: str,
    base_directory: dict[str, str],
    base_claims: set[str],
) -> set[str]:
    source_directory = task_directory(client, source_ref)
    claims = set(base_claims)
    for path, blob_sha in sorted(source_directory.items()):
        if base_directory.get(path) == blob_sha:
            continue
        claims.update(task_file_claims(client, source_ref, path))
    return claims


def branch_metadata(client: rl.GitHubClient, branch: str) -> dict[str, Any] | None:
    encoded = urllib.parse.quote(branch, safe="")
    try:
        payload, _ = client.request("GET", f"/repos/{client.repo}/branches/{encoded}")
    except rl.ApiError as exc:
        if exc.status == 404:
            return None
        raise
    if not isinstance(payload, dict):
        raise rl.LifecycleError("branch metadata response must be an object")
    return payload


def open_pulls_for_branch(client: rl.GitHubClient, branch: str) -> list[dict[str, Any]]:
    owner = client.repo.split("/", 1)[0]
    head = urllib.parse.quote(f"{owner}:{branch}", safe=":")
    payload, _ = client.request(
        "GET",
        f"/repos/{client.repo}/pulls?state=open&head={head}&per_page=100",
    )
    if not isinstance(payload, list):
        raise rl.LifecycleError("open-PR branch query must return a list")
    return [item for item in payload if isinstance(item, dict) and rl.same_repo_pull(item, client.repo)]


def pull_by_number(client: rl.GitHubClient, number: int) -> dict[str, Any]:
    payload, _ = client.request("GET", f"/repos/{client.repo}/pulls/{number}")
    if not isinstance(payload, dict):
        raise rl.LifecycleError(f"PR #{number} response must be an object")
    return payload


def _terminal_pull_matches(
    pull: dict[str, Any],
    *,
    branch: str,
    sha: str,
    classification: str,
) -> bool:
    if pull.get("state") != "closed":
        return False
    if rl.pull_head_ref(pull) != branch or rl.pull_head_sha(pull) != sha:
        return False
    merged = bool(pull.get("merged_at"))
    if classification == "TERMINAL_MERGED":
        return merged
    if classification == "TERMINAL_CLOSED_UNMERGED":
        return not merged
    return False


def delete_branch_exact(client: rl.GitHubClient, branch: str, expected_sha: str) -> None:
    current = client.get_ref_sha(branch)
    if current != expected_sha:
        raise rl.LifecycleError(
            f"pre-delete SHA drift for {branch}: expected {expected_sha}, got {current}"
        )
    remote = client._validate_remote()
    ref = f"refs/heads/{branch}"
    basic = base64.b64encode(f"x-access-token:{client.token}".encode("utf-8")).decode("ascii")
    env = os.environ.copy()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {basic}"
    try:
        result = subprocess.run(
            [
                "git",
                "push",
                "--porcelain",
                f"--force-with-lease={ref}:{expected_sha}",
                remote,
                f":{ref}",
            ],
            cwd=client.root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        raise rl.LifecycleError("delete branch: git executable unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise rl.LifecycleError(f"delete branch {branch}: timed out") from exc
    if result.returncode != 0:
        remote_sha = client.remote_ref_sha(branch)
        if remote_sha is None:
            raise rl.LifecycleError(f"delete returned failure but {branch} is absent; ambiguous")
        if remote_sha != expected_sha:
            raise rl.LifecycleError(
                f"delete lease rejected for {branch}: remote moved to {remote_sha}"
            )
        raise rl.LifecycleError(f"delete push rejected for {branch}")
    if client.remote_ref_sha(branch) is not None:
        raise rl.LifecycleError(f"post-delete git verification found {branch} still present")


def revalidate_candidate(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    candidate: dict[str, Any],
    *,
    base_ref: str,
    base_directory: dict[str, str] | None = None,
    base_claims: set[str] | None = None,
) -> dict[str, Any]:
    branch = candidate.get("branch")
    sha = candidate.get("sha")
    classification = candidate.get("classification")
    pr_numbers = candidate.get("pr_numbers")
    if not isinstance(branch, str) or not branch:
        raise rl.LifecycleError("candidate branch is invalid")
    if not isinstance(sha, str) or not rl.FULL_SHA_RE.fullmatch(sha):
        raise rl.LifecycleError(f"candidate {branch}: invalid SHA")
    if classification not in rl.DELETION_CLASSIFICATIONS:
        raise rl.LifecycleError(f"candidate {branch}: unapproved classification {classification!r}")
    if not isinstance(pr_numbers, list) or not pr_numbers or any(not isinstance(value, int) for value in pr_numbers):
        raise rl.LifecycleError(f"candidate {branch}: missing terminal PR numbers")
    if branch == policy["default_branch"] or branch in set(policy["integration_branches"]):
        raise RetainBranch(f"{branch}: integration/default branch")
    if rl.is_reserved(branch, policy["reserved_name_parts"]):
        raise RetainBranch(f"{branch}: reserved release/rollback/recovery/backup ref")

    metadata = branch_metadata(client, branch)
    if metadata is None:
        return {"branch": branch, "sha": sha, "status": "ALREADY_ABSENT"}
    commit = metadata.get("commit")
    current_sha = commit.get("sha") if isinstance(commit, dict) else None
    if current_sha != sha:
        raise RetainBranch(f"{branch}: live SHA drifted from reviewed {sha} to {current_sha}")
    if bool(metadata.get("protected")):
        raise RetainBranch(f"{branch}: branch is protected")
    if open_pulls_for_branch(client, branch):
        raise RetainBranch(f"{branch}: a same-repository open PR now owns the branch")

    current_base_sha = client.get_ref_sha(base_ref)
    if current_base_sha is None:
        raise rl.LifecycleError(f"base ref {base_ref} is absent")
    if base_directory is None or base_claims is None:
        base_directory, base_claims = claim_snapshot(client, current_base_sha)
    source_claims = source_only_claims(client, sha, base_directory, base_claims)
    if branch in source_claims:
        raise RetainBranch(f"{branch}: active task claim exists on base or exact source head")

    terminal_matches: list[int] = []
    for number in pr_numbers:
        pull = pull_by_number(client, number)
        if not rl.same_repo_pull(pull, client.repo):
            continue
        if _terminal_pull_matches(
            pull,
            branch=branch,
            sha=sha,
            classification=classification,
        ):
            terminal_matches.append(number)
    if not terminal_matches:
        raise RetainBranch(f"{branch}: no reviewed terminal PR remains exact and closed")

    return {
        "branch": branch,
        "sha": sha,
        "classification": classification,
        "terminal_prs": terminal_matches,
        "status": "DELETE_SAFE",
    }


def safe_recovery_test(client: rl.GitHubClient, default_branch: str, issue: int) -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    branch = f"recovery-test/issue-{issue}-{run_id}"
    base_sha = client.get_ref_sha(default_branch)
    if base_sha is None:
        raise rl.LifecycleError("default branch ref missing for recovery test")
    evidence: dict[str, Any] = {
        "branch": branch,
        "base_sha": base_sha,
        "create": "NOT_RUN",
        "delete": "NOT_RUN",
        "restore": "NOT_RUN",
        "final_delete": "NOT_RUN",
        "cleanup": "NOT_NEEDED",
    }
    primary_error: Exception | None = None
    try:
        existing = client.get_ref_sha(branch)
        if existing is not None:
            if existing != base_sha:
                raise rl.LifecycleError(
                    f"recovery branch {branch} already exists at unexpected SHA {existing}"
                )
            delete_branch_exact(client, branch, base_sha)
            evidence["cleanup"] = "REMOVED_PREEXISTING_EXACT_REF"
        client.create_ref(branch, base_sha)
        evidence["create"] = "PASS"
        if client.get_ref_sha(branch) != base_sha:
            raise rl.LifecycleError("recovery-test create verification failed")
        delete_branch_exact(client, branch, base_sha)
        evidence["delete"] = "PASS"
        client.create_ref(branch, base_sha)
        if client.get_ref_sha(branch) != base_sha:
            raise rl.LifecycleError("recovery-test restore verification failed")
        evidence["restore"] = "PASS"
        delete_branch_exact(client, branch, base_sha)
        evidence["final_delete"] = "PASS"
        return evidence
    except Exception as exc:
        primary_error = exc
        raise
    finally:
        leftover = client.get_ref_sha(branch)
        if leftover is not None:
            if leftover == base_sha:
                try:
                    delete_branch_exact(client, branch, base_sha)
                    evidence["cleanup"] = "PASS"
                except Exception as cleanup_exc:
                    if primary_error is None:
                        raise
                    raise rl.LifecycleError(
                        f"recovery test failed ({primary_error}); cleanup also failed ({cleanup_exc})"
                    ) from cleanup_exc
            elif primary_error is None:
                raise rl.LifecycleError(
                    f"recovery test left {branch} at unexpected SHA {leftover}; refusing deletion"
                )


def _write(path: Path | None, value: dict[str, Any]) -> None:
    if path is not None:
        path.write_text(rl.canonical_json(value), encoding="utf-8")


def apply_reviewed_cleanup(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
    output: Path | None,
) -> dict[str, Any]:
    inventory = rl.build_inventory(client, policy, root)
    approval = rl.load_json(root / rl.APPROVAL_PATH)
    rl.validate_approval(approval, inventory, policy)
    if approval["apply_on_develop"] is not True:
        raise rl.LifecycleError("reviewed approval is not activated for develop")

    candidates = inventory["candidates"]
    result: dict[str, Any] = {
        "schema_version": 1,
        "repository": client.repo,
        "reviewed_candidate_count": len(candidates),
        "entries_sha256": inventory["entries_sha256"],
        "policy_sha256": inventory["policy_sha256"],
        "deleted": [],
        "already_absent": [],
        "retained_after_revalidation": [],
        "recovery_test": None,
        "result": "RUNNING",
    }
    _write(output, result)

    base_sha = client.get_ref_sha(policy["default_branch"])
    if base_sha is None:
        raise rl.LifecycleError("default branch missing before destructive preflight")
    base_directory, base_claims = claim_snapshot(client, base_sha)

    for candidate in candidates:
        try:
            revalidate_candidate(
                client,
                policy,
                candidate,
                base_ref=policy["default_branch"],
                base_directory=base_directory,
                base_claims=base_claims,
            )
        except RetainBranch as exc:
            result["retained_after_revalidation"].append(
                {"branch": candidate["branch"], "reason": str(exc), "phase": "preflight"}
            )
    if result["retained_after_revalidation"]:
        result["result"] = "ABORTED_BEFORE_DELETE"
        _write(output, result)
        raise rl.LifecycleError(
            "reviewed candidate set no longer passes complete preflight; no historical branch was deleted"
        )

    result["recovery_test"] = safe_recovery_test(
        client, policy["default_branch"], policy["issue"]
    )
    _write(output, result)

    for candidate in candidates:
        try:
            status = revalidate_candidate(
                client,
                policy,
                candidate,
                base_ref=policy["default_branch"],
            )
        except RetainBranch as exc:
            result["retained_after_revalidation"].append(
                {"branch": candidate["branch"], "reason": str(exc), "phase": "immediate"}
            )
            _write(output, result)
            continue
        if status["status"] == "ALREADY_ABSENT":
            result["already_absent"].append(candidate)
            _write(output, result)
            continue
        delete_branch_exact(client, candidate["branch"], candidate["sha"])
        result["deleted"].append(candidate)
        _write(output, result)

    result["result"] = "PASS"
    _write(output, result)
    return result


def event_cleanup(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
    event_path: Path,
) -> dict[str, Any]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    pull = event.get("pull_request")
    if not isinstance(pull, dict):
        raise rl.LifecycleError("pull_request event payload missing")
    if event.get("action") != "closed":
        return {"result": "NOT_APPLICABLE", "reason": "event action is not closed"}
    if not rl.same_repo_pull(pull, client.repo):
        return {"result": "NOT_APPLICABLE", "reason": "fork PR head is not repository-owned"}
    branch = rl.pull_head_ref(pull)
    sha = rl.pull_head_sha(pull)
    number = pull.get("number")
    if branch is None or sha is None or not isinstance(number, int):
        raise rl.LifecycleError("closed PR lacks exact same-repository head identity")

    classification = "TERMINAL_MERGED" if pull.get("merged_at") or pull.get("merged") else "TERMINAL_CLOSED_UNMERGED"
    candidate = {
        "branch": branch,
        "sha": sha,
        "classification": classification,
        "pr_numbers": [number],
    }
    try:
        status = revalidate_candidate(
            client,
            policy,
            candidate,
            base_ref=policy["default_branch"],
        )
    except RetainBranch as exc:
        return {
            "result": "RETAINED",
            "branch": branch,
            "sha": sha,
            "pr": number,
            "reason": str(exc),
        }
    if status["status"] == "ALREADY_ABSENT":
        return {
            "result": "PASS",
            "branch": branch,
            "sha": sha,
            "pr": number,
            "reason": "branch already absent after terminal PR close",
        }
    delete_branch_exact(client, branch, sha)
    return {
        "result": "PASS",
        "branch": branch,
        "sha": sha,
        "pr": number,
        "reason": "terminal same-repository branch deleted at exact revalidated SHA",
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("apply", "event"), required=True)
    p.add_argument("--root", default=".")
    p.add_argument("--policy", default=str(rl.POLICY_PATH))
    p.add_argument("--event")
    p.add_argument("--output")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    policy = rl.load_json(root / args.policy)
    rl.validate_policy(policy)
    repo = os.environ.get("GITHUB_REPOSITORY", policy["repository"])
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise rl.LifecycleError("GITHUB_TOKEN is required")
    if repo.casefold() != policy["repository"].casefold():
        raise rl.LifecycleError(f"GITHUB_REPOSITORY mismatch: {repo}")
    client = rl.GitHubClient(repo, token, root=root)
    output = Path(args.output) if args.output else None
    if args.mode == "apply":
        result = apply_reviewed_cleanup(client, policy, root, output)
    else:
        if not args.event:
            raise rl.LifecycleError("--event is required for event mode")
        result = event_cleanup(client, policy, root, Path(args.event))
        _write(output, result)
    if output is None:
        print(rl.canonical_json(result), end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (rl.LifecycleError, rl.ApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
