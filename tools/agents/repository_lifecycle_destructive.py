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
        return base64.b64decode(content, validate=False).decode(
            "utf-8",
            errors="replace",
        )
    except Exception as exc:  # pragma: no cover
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


def claim_snapshot(
    client: rl.GitHubClient,
    ref: str,
) -> tuple[dict[str, str], set[str]]:
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


def branch_metadata(
    client: rl.GitHubClient,
    branch: str,
) -> dict[str, Any] | None:
    encoded = urllib.parse.quote(branch, safe="")
    try:
        payload, _ = client.request(
            "GET",
            f"/repos/{client.repo}/branches/{encoded}",
        )
    except rl.ApiError as exc:
        if exc.status == 404:
            return None
        raise
    if not isinstance(payload, dict):
        raise rl.LifecycleError("branch metadata response must be an object")
    return payload


def open_pulls_for_branch(
    client: rl.GitHubClient,
    branch: str,
) -> list[dict[str, Any]]:
    owner = client.repo.split("/", 1)[0]
    head = urllib.parse.quote(f"{owner}:{branch}", safe=":")
    payload, _ = client.request(
        "GET",
        f"/repos/{client.repo}/pulls?state=open&head={head}&per_page=100",
    )
    if not isinstance(payload, list):
        raise rl.LifecycleError("open-PR branch query must return a list")
    return [
        item
        for item in payload
        if isinstance(item, dict) and rl.same_repo_pull(item, client.repo)
    ]


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


def create_ref(client: rl.GitHubClient, branch: str, sha: str) -> None:
    client.request(
        "POST",
        f"/repos/{client.repo}/git/refs",
        data={"ref": f"refs/heads/{branch}", "sha": sha},
        expected=(201,),
    )


def _run_git(
    client: rl.GitHubClient,
    args: list[str],
    purpose: str,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=client.root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        raise rl.LifecycleError(f"{purpose}: git executable unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise rl.LifecycleError(f"{purpose}: timed out") from exc


def validate_remote(client: rl.GitHubClient) -> str:
    root = _run_git(
        client,
        ["git", "rev-parse", "--show-toplevel"],
        "validate git root",
    )
    if root.returncode != 0 or Path(root.stdout.strip()).resolve() != client.root:
        raise rl.LifecycleError("configured root is not the checked-out Git worktree")
    remote = _run_git(
        client,
        ["git", "remote", "get-url", "--push", "origin"],
        "validate origin",
    )
    if remote.returncode != 0:
        raise rl.LifecycleError("origin push remote unavailable")
    value = remote.stdout.strip().removesuffix(".git")
    expected = client.repo.casefold()
    if value.startswith("https://github.com/"):
        got = value.removeprefix("https://github.com/").casefold()
    elif value.startswith("git@github.com:"):
        got = value.removeprefix("git@github.com:").casefold()
    else:
        raise rl.LifecycleError("origin is not a supported GitHub remote")
    if got != expected:
        raise rl.LifecycleError(
            f"origin repository mismatch: expected {client.repo}, got {got}"
        )
    return "origin"


def remote_ref_sha(client: rl.GitHubClient, branch: str) -> str | None:
    remote = validate_remote(client)
    ref = f"refs/heads/{branch}"
    result = _run_git(
        client,
        ["git", "ls-remote", "--refs", remote, ref],
        f"verify remote ref {branch}",
    )
    if result.returncode != 0:
        raise rl.LifecycleError(f"git ls-remote failed for {branch}")
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if not rows:
        return None
    if (
        len(rows) != 1
        or len(rows[0]) != 2
        or rows[0][1] != ref
        or not rl.FULL_SHA_RE.fullmatch(rows[0][0])
    ):
        raise rl.LifecycleError(f"unexpected remote ref data for {branch}")
    return rows[0][0]


def delete_branch_exact(
    client: rl.GitHubClient,
    branch: str,
    expected_sha: str,
) -> None:
    current = client.get_ref_sha(branch)
    if current != expected_sha:
        raise rl.LifecycleError(
            f"pre-delete SHA drift for {branch}: expected {expected_sha}, got {current}"
        )
    remote = validate_remote(client)
    ref = f"refs/heads/{branch}"
    basic = base64.b64encode(f"x-access-token:{client.token}".encode()).decode("ascii")
    env = os.environ.copy()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {basic}"
    result = _run_git(
        client,
        [
            "git",
            "push",
            "--porcelain",
            f"--force-with-lease={ref}:{expected_sha}",
            remote,
            f":{ref}",
        ],
        f"delete branch {branch}",
        env=env,
    )
    if result.returncode != 0:
        remote_sha = remote_ref_sha(client, branch)
        if remote_sha is None:
            raise rl.LifecycleError(
                f"delete returned failure but {branch} is absent; ambiguous"
            )
        if remote_sha != expected_sha:
            raise rl.LifecycleError(
                f"delete lease rejected for {branch}: remote moved to {remote_sha}"
            )
        raise rl.LifecycleError(f"delete push rejected for {branch}")
    if remote_ref_sha(client, branch) is not None:
        raise rl.LifecycleError(
            f"post-delete git verification found {branch} still present"
        )


def _candidate_identity(
    policy: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[str, str, str, list[int]]:
    branch = candidate.get("branch")
    sha = candidate.get("sha")
    classification = candidate.get("classification")
    pr_numbers = candidate.get("pr_numbers")
    if not isinstance(branch, str) or not branch:
        raise rl.LifecycleError("candidate branch is invalid")
    if not isinstance(sha, str) or not rl.FULL_SHA_RE.fullmatch(sha):
        raise rl.LifecycleError(f"candidate {branch}: invalid SHA")
    if not isinstance(classification, str) or classification not in rl.DELETION_CLASSIFICATIONS:
        raise rl.LifecycleError(
            f"candidate {branch}: unapproved classification {classification!r}"
        )
    if (
        not isinstance(pr_numbers, list)
        or not pr_numbers
        or any(not isinstance(value, int) for value in pr_numbers)
    ):
        raise rl.LifecycleError(f"candidate {branch}: missing terminal PR numbers")
    if branch == policy["default_branch"] or branch in set(policy["integration_branches"]):
        raise RetainBranch(f"{branch}: integration/default branch")
    if rl.is_reserved(branch, policy["reserved_name_parts"]):
        raise RetainBranch(
            f"{branch}: reserved release/rollback/recovery/backup ref"
        )
    return branch, sha, classification, pr_numbers


def _validate_live_ownership(
    client: rl.GitHubClient,
    branch: str,
    sha: str,
) -> bool:
    metadata = branch_metadata(client, branch)
    if metadata is None:
        return False
    commit = metadata.get("commit")
    current_sha = commit.get("sha") if isinstance(commit, dict) else None
    if current_sha != sha:
        raise RetainBranch(
            f"{branch}: live SHA drifted from reviewed {sha} to {current_sha}"
        )
    if bool(metadata.get("protected")):
        raise RetainBranch(f"{branch}: branch is protected")
    if open_pulls_for_branch(client, branch):
        raise RetainBranch(
            f"{branch}: a same-repository open PR now owns the branch"
        )
    return True


def _validate_task_claims(
    client: rl.GitHubClient,
    *,
    branch: str,
    sha: str,
    classification: str,
    base_ref: str,
    base_directory: dict[str, str] | None,
    base_claims: set[str] | None,
) -> None:
    current_base_sha = client.get_ref_sha(base_ref)
    if current_base_sha is None:
        raise rl.LifecycleError(f"base ref {base_ref} is absent")
    if base_directory is None or base_claims is None:
        base_directory, base_claims = claim_snapshot(client, current_base_sha)
    if branch in base_claims:
        raise RetainBranch(f"{branch}: active task claim exists on current base")
    if classification != "TERMINAL_CLOSED_UNMERGED":
        return
    source_claims = source_only_claims(client, sha, base_directory, base_claims)
    if branch in source_claims:
        raise RetainBranch(f"{branch}: active task claim exists on exact source head")


def _terminal_matches_for_candidate(
    client: rl.GitHubClient,
    *,
    branch: str,
    sha: str,
    classification: str,
    pr_numbers: list[int],
) -> list[int]:
    matches: list[int] = []
    for number in pr_numbers:
        pull = pull_by_number(client, number)
        if rl.same_repo_pull(pull, client.repo) and _terminal_pull_matches(
            pull,
            branch=branch,
            sha=sha,
            classification=classification,
        ):
            matches.append(number)
    if not matches:
        raise RetainBranch(
            f"{branch}: no reviewed terminal PR remains exact and closed"
        )
    return matches


def revalidate_candidate(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    candidate: dict[str, Any],
    *,
    base_ref: str,
    base_directory: dict[str, str] | None = None,
    base_claims: set[str] | None = None,
) -> dict[str, Any]:
    branch, sha, classification, pr_numbers = _candidate_identity(policy, candidate)
    if not _validate_live_ownership(client, branch, sha):
        return {"branch": branch, "sha": sha, "status": "ALREADY_ABSENT"}
    _validate_task_claims(
        client,
        branch=branch,
        sha=sha,
        classification=classification,
        base_ref=base_ref,
        base_directory=base_directory,
        base_claims=base_claims,
    )
    terminal_matches = _terminal_matches_for_candidate(
        client,
        branch=branch,
        sha=sha,
        classification=classification,
        pr_numbers=pr_numbers,
    )
    return {
        "branch": branch,
        "sha": sha,
        "classification": classification,
        "terminal_prs": terminal_matches,
        "status": "DELETE_SAFE",
    }


def safe_recovery_test(
    client: rl.GitHubClient,
    default_branch: str,
    issue: int,
) -> dict[str, Any]:
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
        create_ref(client, branch, base_sha)
        evidence["create"] = "PASS"
        if client.get_ref_sha(branch) != base_sha:
            raise rl.LifecycleError("recovery-test create verification failed")
        delete_branch_exact(client, branch, base_sha)
        evidence["delete"] = "PASS"
        create_ref(client, branch, base_sha)
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
                        f"recovery test failed ({primary_error}); cleanup also failed "
                        f"({cleanup_exc})"
                    ) from cleanup_exc
            elif primary_error is None:
                raise rl.LifecycleError(
                    f"recovery test left {branch} at unexpected SHA {leftover}; "
                    "refusing deletion"
                )


def _write(path: Path | None, value: dict[str, Any]) -> None:
    if path is not None:
        path.write_text(rl.canonical_json(value), encoding="utf-8")


def _safe_manifest(
    inventory: dict[str, Any],
    safe_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "candidate_count": len(safe_candidates),
        "entries_sha256": rl.entries_sha256(safe_candidates),
        "policy_sha256": inventory["policy_sha256"],
    }


def apply_reviewed_cleanup(
    client: rl.GitHubClient,
    policy: dict[str, Any],
    root: Path,
    output: Path | None,
) -> dict[str, Any]:
    inventory = rl.build_inventory(client, policy, root)
    approval = rl.load_json(root / rl.APPROVAL_PATH)
    if approval["apply_on_develop"] is not True:
        raise rl.LifecycleError("reviewed approval is not activated for develop")

    result: dict[str, Any] = {
        "schema_version": 1,
        "repository": client.repo,
        "raw_terminal_candidate_count": inventory["candidate_count"],
        "reviewed_candidate_count": 0,
        "entries_sha256": None,
        "policy_sha256": inventory["policy_sha256"],
        "deleted": [],
        "already_absent": [],
        "retained_by_source_head_preflight": [],
        "retained_after_revalidation": [],
        "recovery_test": None,
        "result": "RUNNING",
    }
    _write(output, result)

    base_sha = client.get_ref_sha(policy["default_branch"])
    if base_sha is None:
        raise rl.LifecycleError("default branch missing before destructive preflight")
    base_directory, base_claims = claim_snapshot(client, base_sha)
    safe_candidates: list[dict[str, Any]] = []
    for candidate in inventory["candidates"]:
        try:
            status = revalidate_candidate(
                client,
                policy,
                candidate,
                base_ref=policy["default_branch"],
                base_directory=base_directory,
                base_claims=base_claims,
            )
        except RetainBranch as exc:
            result["retained_by_source_head_preflight"].append(
                {"branch": candidate["branch"], "reason": str(exc)}
            )
            continue
        if status["status"] == "ALREADY_ABSENT":
            result["already_absent"].append(candidate)
            continue
        safe_candidates.append(candidate)

    manifest = _safe_manifest(inventory, safe_candidates)
    rl.validate_approval(approval, manifest, policy)
    result["reviewed_candidate_count"] = manifest["candidate_count"]
    result["entries_sha256"] = manifest["entries_sha256"]
    _write(output, result)

    result["recovery_test"] = safe_recovery_test(
        client,
        policy["default_branch"],
        policy["issue"],
    )
    _write(output, result)
    for candidate in safe_candidates:
        try:
            status = revalidate_candidate(
                client,
                policy,
                candidate,
                base_ref=policy["default_branch"],
            )
        except RetainBranch as exc:
            result["retained_after_revalidation"].append(
                {
                    "branch": candidate["branch"],
                    "reason": str(exc),
                    "phase": "immediate",
                }
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
    del root
    event = json.loads(event_path.read_text(encoding="utf-8"))
    pull = event.get("pull_request")
    if not isinstance(pull, dict):
        raise rl.LifecycleError("pull_request event payload missing")
    if event.get("action") != "closed":
        return {"result": "NOT_APPLICABLE", "reason": "event action is not closed"}
    if not rl.same_repo_pull(pull, client.repo):
        return {
            "result": "NOT_APPLICABLE",
            "reason": "fork PR head is not repository-owned",
        }
    branch = rl.pull_head_ref(pull)
    sha = rl.pull_head_sha(pull)
    number = pull.get("number")
    if branch is None or sha is None or not isinstance(number, int):
        raise rl.LifecycleError("closed PR lacks exact same-repository head identity")
    classification = (
        "TERMINAL_MERGED"
        if pull.get("merged_at") or pull.get("merged")
        else "TERMINAL_CLOSED_UNMERGED"
    )
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
