#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

POLICY_PATH = Path("docs/agents/REPOSITORY_LIFECYCLE_POLICY.json")
APPROVAL_PATH = Path("docs/agents/REPOSITORY_LIFECYCLE_APPROVAL.json")
ACTIVE_TASKS_PATH = Path("docs/agents/tasks/active")
SCHEMA_VERSION = 1
APPROVAL_SCHEMA_VERSION = 1
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_BRANCH_RE = re.compile(r"^\s*(?:branch|lock_branch):\s*([^\s#]+)\s*$", re.M)
TASK_STATUS_RE = re.compile(r"^\s*status:\s*([^\s#]+)\s*$", re.M)
DRAFT_WORDING_RE = re.compile(
    r"\b(?:remain|remains|keep|kept|stays?)\s+(?:this\s+pr\s+)?(?:as\s+)?draft\b|\bthis\s+pr\s+(?:is|remains)\s+draft\b",
    re.I,
)

CLASSIFICATIONS = {
    "PROTECTED",
    "OPEN_PR",
    "ACTIVE_CLAIM",
    "RESERVED",
    "TERMINAL_MERGED",
    "TERMINAL_CLOSED_UNMERGED",
    "UNMERGED_ORPHAN",
    "UNKNOWN",
}
DELETION_CLASSIFICATIONS = {"TERMINAL_MERGED", "TERMINAL_CLOSED_UNMERGED"}
PR_HEALTH = {
    "ACTIVE",
    "WAITING_OR_BLOCKED",
    "REQUEST_ONLY",
    "STALLED_SIGNAL",
    "METADATA_INCONSISTENT",
}


class LifecycleError(RuntimeError):
    pass


class ApiError(LifecycleError):
    def __init__(self, method: str, path: str, status: int, body: str) -> None:
        super().__init__(f"{method} {path}: GitHub API returned {status}: {body[:500]}")
        self.method = method
        self.path = path
        self.status = status
        self.body = body


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LifecycleError(f"missing JSON file: {path}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LifecycleError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"{path}: root must be an object")
    if raw != canonical_json(value):
        raise LifecycleError(f"{path}: JSON must be canonical (sorted, indent=2, trailing newline)")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "issue",
        "repository",
        "default_branch",
        "integration_branches",
        "reserved_name_parts",
        "stale_pr_days",
        "deletion_classifications",
    }
    if set(policy) != expected:
        raise LifecycleError(f"policy schema drift: {sorted(set(policy) ^ expected)}")
    if policy["schema_version"] != SCHEMA_VERSION:
        raise LifecycleError(f"policy.schema_version must be {SCHEMA_VERSION}")
    if not isinstance(policy["issue"], int) or policy["issue"] <= 0:
        raise LifecycleError("policy.issue must be a positive integer")
    if not isinstance(policy["repository"], str) or "/" not in policy["repository"]:
        raise LifecycleError("policy.repository must be owner/name")
    if not isinstance(policy["default_branch"], str) or not policy["default_branch"]:
        raise LifecycleError("policy.default_branch must be non-empty")
    if not isinstance(policy["integration_branches"], list) or policy["default_branch"] not in policy["integration_branches"]:
        raise LifecycleError("policy.integration_branches must contain default_branch")
    if any(not isinstance(item, str) or not item for item in policy["integration_branches"]):
        raise LifecycleError("policy.integration_branches entries must be non-empty strings")
    if not isinstance(policy["reserved_name_parts"], list) or any(
        not isinstance(item, str) or not item for item in policy["reserved_name_parts"]
    ):
        raise LifecycleError("policy.reserved_name_parts must be non-empty strings")
    if not isinstance(policy["stale_pr_days"], int) or policy["stale_pr_days"] < 1:
        raise LifecycleError("policy.stale_pr_days must be >= 1")
    if set(policy["deletion_classifications"]) != DELETION_CLASSIFICATIONS:
        raise LifecycleError("policy.deletion_classifications must match the approved terminal set")


def policy_sha256(policy: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(policy).encode("utf-8"))


def entries_sha256(entries: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_json(entries).encode("utf-8"))


def active_branch_claims(root: Path) -> set[str]:
    claims: set[str] = set()
    path = root / ACTIVE_TASKS_PATH
    if not path.exists():
        return claims
    for task in sorted(path.glob("*.md")):
        text = task.read_text(encoding="utf-8", errors="replace")
        status_match = TASK_STATUS_RE.search(text)
        if status_match and status_match.group(1).strip().lower() == "completed":
            continue
        for match in TASK_BRANCH_RE.finditer(text):
            claims.add(match.group(1).strip())
    return claims


def is_reserved(branch: str, parts: Iterable[str]) -> bool:
    lowered = branch.casefold()
    tokens = re.split(r"[/_.-]+", lowered)
    return any(part.casefold() in tokens for part in parts)


def same_repo_pull(pull: dict[str, Any], repo: str) -> bool:
    head = pull.get("head")
    if not isinstance(head, dict):
        return False
    head_repo = head.get("repo")
    if not isinstance(head_repo, dict):
        return False
    return str(head_repo.get("full_name", "")).casefold() == repo.casefold()


def pull_head_ref(pull: dict[str, Any]) -> str | None:
    head = pull.get("head")
    if not isinstance(head, dict):
        return None
    ref = head.get("ref")
    return ref if isinstance(ref, str) and ref else None


def pull_head_sha(pull: dict[str, Any]) -> str | None:
    head = pull.get("head")
    if not isinstance(head, dict):
        return None
    sha = head.get("sha")
    return sha if isinstance(sha, str) and FULL_SHA_RE.fullmatch(sha) else None


def parse_github_time(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


class GitHubClient:
    def __init__(self, repo: str, token: str, api_url: str = "https://api.github.com", root: Path | None = None) -> None:
        if "/" not in repo:
            raise LifecycleError("repository must be owner/name")
        self.repo = repo
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.root = (root or Path(".")).resolve()
        self.deleted_refs: set[str] = set()

    def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        expected: Iterable[int] = (200,),
    ) -> tuple[Any, dict[str, str]]:
        url = path if path.startswith("http") else f"{self.api_url}{path}"
        body = None if data is None else json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "freqtrade-repository-lifecycle/1",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw) if raw else None
                return payload, {k.lower(): v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if exc.code in set(expected):
                payload = json.loads(raw) if raw else None
                return payload, {k.lower(): v for k, v in exc.headers.items()}
            raise ApiError(method, path, exc.code, raw) from exc

    @staticmethod
    def _next_link(header: str) -> str | None:
        for part in header.split(","):
            if 'rel="next"' not in part:
                continue
            match = re.match(r"\s*<([^>]+)>", part)
            return match.group(1) if match else None
        return None

    def paginate(self, path: str) -> list[Any]:
        out: list[Any] = []
        next_url: str | None = path
        while next_url:
            payload, headers = self.request("GET", next_url)
            if not isinstance(payload, list):
                raise LifecycleError(f"paginated endpoint returned non-list: {next_url}")
            out.extend(payload)
            next_url = self._next_link(headers.get("link", ""))
        return out

    def repo_metadata(self) -> dict[str, Any]:
        payload, _ = self.request("GET", f"/repos/{self.repo}")
        if not isinstance(payload, dict):
            raise LifecycleError("repository metadata must be object")
        return payload

    def branches(self) -> list[dict[str, Any]]:
        raw = self.paginate(f"/repos/{self.repo}/branches?per_page=100")
        out = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
        return out

    def pulls(self, state: str = "all") -> list[dict[str, Any]]:
        raw = self.paginate(
            f"/repos/{self.repo}/pulls?state={urllib.parse.quote(state)}&per_page=100&sort=updated&direction=desc"
        )
        return [item for item in raw if isinstance(item, dict)]

    def get_ref_sha(self, branch: str) -> str | None:
        ref = "heads/" + urllib.parse.quote(branch, safe="/")
        try:
            payload, _ = self.request("GET", f"/repos/{self.repo}/git/ref/{ref}")
        except ApiError as exc:
            if exc.status == 404:
                return None
            raise
        if not isinstance(payload, dict):
            raise LifecycleError("ref payload must be object")
        obj = payload.get("object")
        if not isinstance(obj, dict):
            return None
        sha = obj.get("sha")
        return sha if isinstance(sha, str) and FULL_SHA_RE.fullmatch(sha) else None

    def create_ref(self, branch: str, sha: str) -> None:
        self.request(
            "POST",
            f"/repos/{self.repo}/git/refs",
            data={"ref": f"refs/heads/{branch}", "sha": sha},
            expected=(201,),
        )

    def _run_git(self, args: list[str], purpose: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                args,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise LifecycleError(f"{purpose}: git executable unavailable") from exc
        except subprocess.TimeoutExpired as exc:
            raise LifecycleError(f"{purpose}: timed out") from exc

    def _validate_remote(self) -> str:
        root = self._run_git(["git", "rev-parse", "--show-toplevel"], "validate git root", 15)
        if root.returncode != 0 or Path(root.stdout.strip()).resolve() != self.root:
            raise LifecycleError("configured root is not the checked-out Git worktree")
        remote = self._run_git(["git", "remote", "get-url", "--push", "origin"], "validate origin", 15)
        if remote.returncode != 0:
            raise LifecycleError("origin push remote unavailable")
        value = remote.stdout.strip()
        expected = self.repo.casefold()
        normalized = value.removesuffix(".git")
        if normalized.startswith("https://github.com/"):
            got = normalized.removeprefix("https://github.com/").casefold()
        elif normalized.startswith("git@github.com:"):
            got = normalized.removeprefix("git@github.com:").casefold()
        else:
            raise LifecycleError("origin is not a supported GitHub remote")
        if got != expected:
            raise LifecycleError(f"origin repository mismatch: expected {self.repo}, got {got}")
        return "origin"

    def remote_ref_sha(self, branch: str) -> str | None:
        remote = self._validate_remote()
        ref = f"refs/heads/{branch}"
        result = self._run_git(["git", "ls-remote", "--refs", remote, ref], f"verify remote ref {branch}")
        if result.returncode != 0:
            raise LifecycleError(f"git ls-remote failed for {branch}")
        rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
        if not rows:
            return None
        if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref or not FULL_SHA_RE.fullmatch(rows[0][0]):
            raise LifecycleError(f"unexpected remote ref data for {branch}")
        return rows[0][0]

    def delete_branch_exact(self, branch: str, expected_sha: str) -> None:
        current = self.get_ref_sha(branch)
        if current != expected_sha:
            raise LifecycleError(f"pre-delete SHA drift for {branch}: expected {expected_sha}, got {current}")
        remote = self._validate_remote()
        ref = f"refs/heads/{branch}"
        result = self._run_git(
            [
                "git",
                "push",
                "--porcelain",
                f"--force-with-lease={ref}:{expected_sha}",
                remote,
                f":{ref}",
            ],
            f"delete branch {branch}",
        )
        if result.returncode != 0:
            remote_sha = self.remote_ref_sha(branch)
            if remote_sha is None:
                raise LifecycleError(f"delete returned failure but {branch} is absent; ambiguous")
            if remote_sha != expected_sha:
                raise LifecycleError(f"delete lease rejected for {branch}: remote moved to {remote_sha}")
            raise LifecycleError(f"delete push rejected for {branch}")
        self.deleted_refs.add(branch)
        if self.remote_ref_sha(branch) is not None:
            raise LifecycleError(f"post-delete git verification found {branch} still present")


def build_pull_index(pulls: list[dict[str, Any]], repo: str) -> dict[str, list[dict[str, Any]]]:
    by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pull in pulls:
        if not same_repo_pull(pull, repo):
            continue
        branch = pull_head_ref(pull)
        if branch:
            by_branch[branch].append(pull)
    return by_branch


def classify_branch(
    *,
    branch: str,
    sha: str,
    protected: bool,
    policy: dict[str, Any],
    active_claims: set[str],
    pulls: list[dict[str, Any]],
) -> dict[str, Any]:
    if branch == policy["default_branch"] or branch in set(policy["integration_branches"]) or protected:
        classification, reason = "PROTECTED", "default/integration branch or GitHub-protected ref"
    elif any(pull.get("state") == "open" for pull in pulls):
        classification, reason = "OPEN_PR", "same-repository open PR owns branch"
    elif branch in active_claims:
        classification, reason = "ACTIVE_CLAIM", "active task record references branch"
    elif is_reserved(branch, policy["reserved_name_parts"]):
        classification, reason = "RESERVED", "release/rollback/recovery/backup naming is retained fail-closed"
    else:
        exact_terminal = [pull for pull in pulls if pull_head_sha(pull) == sha and pull.get("state") == "closed"]
        exact_merged = [pull for pull in exact_terminal if pull.get("merged_at")]
        exact_unmerged = [pull for pull in exact_terminal if not pull.get("merged_at")]
        if exact_merged:
            classification, reason = "TERMINAL_MERGED", "closed merged PR exact head SHA matches live branch"
        elif exact_unmerged:
            classification, reason = (
                "TERMINAL_CLOSED_UNMERGED",
                "closed unmerged PR exact head SHA matches live branch",
            )
        elif pulls:
            classification, reason = "UNKNOWN", "PR history exists but no terminal PR matches current branch SHA"
        else:
            classification, reason = "UNMERGED_ORPHAN", "no same-repository PR history found for branch"
    deletion_candidate = classification in DELETION_CLASSIFICATIONS
    pr_numbers = sorted(
        {
            int(pull["number"])
            for pull in pulls
            if isinstance(pull.get("number"), int)
        }
    )
    return {
        "branch": branch,
        "classification": classification,
        "deletion_candidate": deletion_candidate,
        "pr_numbers": pr_numbers,
        "protected": bool(protected),
        "reason": reason,
        "sha": sha,
    }


def build_inventory(client: GitHubClient, policy: dict[str, Any], root: Path) -> dict[str, Any]:
    validate_policy(policy)
    metadata = client.repo_metadata()
    if metadata.get("full_name", "").casefold() != policy["repository"].casefold():
        raise LifecycleError("repository identity differs from policy")
    if metadata.get("default_branch") != policy["default_branch"]:
        raise LifecycleError(
            f"default branch drift: policy={policy['default_branch']} live={metadata.get('default_branch')}"
        )
    # Repository-admin merge settings are not guaranteed to be visible to the
    # workflow GITHUB_TOKEN. They are recorded when present but are not a
    # deletion-safety dependency: terminal close-event cleanup below covers
    # both merged and closed-unmerged same-repository PRs at exact head SHA.
    observed_settings = {
        "delete_branch_on_merge": metadata.get("delete_branch_on_merge", "UNAVAILABLE_TOKEN_SCOPE"),
        "allow_squash_merge": metadata.get("allow_squash_merge", "UNAVAILABLE_TOKEN_SCOPE"),
        "allow_merge_commit": metadata.get("allow_merge_commit", "UNAVAILABLE_TOKEN_SCOPE"),
        "allow_rebase_merge": metadata.get("allow_rebase_merge", "UNAVAILABLE_TOKEN_SCOPE"),
    }

    pulls = client.pulls("all")
    by_branch = build_pull_index(pulls, client.repo)
    claims = active_branch_claims(root)
    entries: list[dict[str, Any]] = []
    for item in client.branches():
        name = item.get("name")
        commit = item.get("commit")
        if not isinstance(name, str) or not isinstance(commit, dict):
            raise LifecycleError("invalid branch inventory record")
        sha = commit.get("sha")
        if not isinstance(sha, str) or not FULL_SHA_RE.fullmatch(sha):
            raise LifecycleError(f"invalid branch SHA for {name}")
        entries.append(
            classify_branch(
                branch=name,
                sha=sha,
                protected=bool(item.get("protected")),
                policy=policy,
                active_claims=claims,
                pulls=by_branch.get(name, []),
            )
        )
    entries.sort(key=lambda item: item["branch"])
    counts = Counter(item["classification"] for item in entries)
    candidates = [
        {
            "branch": item["branch"],
            "classification": item["classification"],
            "pr_numbers": item["pr_numbers"],
            "sha": item["sha"],
        }
        for item in entries
        if item["deletion_candidate"]
    ]
    return {
        "schema_version": 1,
        "repository": client.repo,
        "default_branch": policy["default_branch"],
        "branch_count": len(entries),
        "classification_counts": dict(sorted(counts.items())),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "entries": entries,
        "entries_sha256": entries_sha256(candidates),
        "policy_sha256": policy_sha256(policy),
        "repository_merge_settings": observed_settings,
    }


def validate_approval(approval: dict[str, Any], inventory: dict[str, Any], policy: dict[str, Any]) -> None:
    expected = {
        "schema_version",
        "issue",
        "repository",
        "apply_on_develop",
        "confirmation",
        "candidate_count",
        "entries_sha256",
        "policy_sha256",
        "reviewed_at",
        "reviewed_by",
        "review_summary",
    }
    if set(approval) != expected:
        raise LifecycleError(f"approval schema drift: {sorted(set(approval) ^ expected)}")
    if approval["schema_version"] != APPROVAL_SCHEMA_VERSION:
        raise LifecycleError("approval schema_version mismatch")
    if approval["issue"] != policy["issue"]:
        raise LifecycleError("approval issue mismatch")
    if str(approval["repository"]).casefold() != policy["repository"].casefold():
        raise LifecycleError("approval repository mismatch")
    if approval["confirmation"] != f"DELETE_EXACT_REVIEWED_TERMINAL_BRANCHES_ISSUE_{policy['issue']}":
        raise LifecycleError("approval confirmation mismatch")
    if approval["candidate_count"] != inventory["candidate_count"]:
        raise LifecycleError("approval candidate_count drift")
    if approval["entries_sha256"] != inventory["entries_sha256"]:
        raise LifecycleError("approval candidate entries drift")
    if approval["policy_sha256"] != inventory["policy_sha256"]:
        raise LifecycleError("approval policy drift")
    if not isinstance(approval["reviewed_by"], str) or not approval["reviewed_by"].strip():
        raise LifecycleError("approval reviewed_by required")
    if not isinstance(approval["reviewed_at"], str) or parse_github_time(approval["reviewed_at"]) is None:
        raise LifecycleError("approval reviewed_at must be ISO timestamp")
    if not isinstance(approval["review_summary"], str) or not approval["review_summary"].strip():
        raise LifecycleError("approval review_summary required")


def write_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def recovery_test(client: GitHubClient, default_branch: str, issue: int) -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    branch = f"recovery-test/issue-{issue}-{run_id}"
    if client.get_ref_sha(branch) is not None:
        raise LifecycleError(f"recovery-test branch already exists: {branch}")
    base_sha = client.get_ref_sha(default_branch)
    if base_sha is None:
        raise LifecycleError("default branch ref missing for recovery test")
    client.create_ref(branch, base_sha)
    if client.get_ref_sha(branch) != base_sha:
        raise LifecycleError("recovery-test create verification failed")
    client.delete_branch_exact(branch, base_sha)
    client.create_ref(branch, base_sha)
    restored_sha = client.get_ref_sha(branch)
    if restored_sha != base_sha:
        raise LifecycleError("recovery-test restore verification failed")
    client.delete_branch_exact(branch, base_sha)
    return {
        "branch": branch,
        "base_sha": base_sha,
        "create": "PASS",
        "delete": "PASS",
        "restore": "PASS",
        "final_delete": "PASS",
    }


def apply_inventory(client: GitHubClient, inventory: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    if not APPROVAL_PATH.exists():
        raise LifecycleError("approval file missing")
    approval = load_json(APPROVAL_PATH)
    validate_approval(approval, inventory, policy)
    if approval["apply_on_develop"] is not True:
        raise LifecycleError("approval is not activated for develop")
    recovery = recovery_test(client, policy["default_branch"], policy["issue"])
    deleted: list[dict[str, Any]] = []
    for candidate in inventory["candidates"]:
        branch = candidate["branch"]
        sha = candidate["sha"]
        client.delete_branch_exact(branch, sha)
        deleted.append(candidate)
    return {
        "schema_version": 1,
        "repository": client.repo,
        "candidate_count": inventory["candidate_count"],
        "deleted_count": len(deleted),
        "deleted": deleted,
        "entries_sha256": inventory["entries_sha256"],
        "policy_sha256": inventory["policy_sha256"],
        "recovery_test": recovery,
        "result": "PASS",
    }


def classify_pr_health(pull: dict[str, Any], *, now: dt.datetime, stale_days: int) -> dict[str, Any]:
    number = pull.get("number")
    title = pull.get("title") if isinstance(pull.get("title"), str) else ""
    body = pull.get("body") if isinstance(pull.get("body"), str) else ""
    draft = bool(pull.get("draft"))
    updated = parse_github_time(pull.get("updated_at"))
    age_days = None if updated is None else max(0.0, (now - updated).total_seconds() / 86400)
    body_lower = body.casefold()
    request_only = any(
        token in body_lower
        for token in (
            "must not be merged",
            "must close without merge",
            "request-only",
            "request only",
            "close after terminal",
        )
    )
    waiting = any(token in body_lower for token in ("blocked", "waiting", "wait until", "remains mandatory"))
    prose_draft = bool(DRAFT_WORDING_RE.search(body))
    inconsistent = (prose_draft and not draft) or (draft and "ready for review" in body_lower)
    if inconsistent:
        health = "METADATA_INCONSISTENT"
        reason = "GitHub draft metadata conflicts with PR prose"
    elif request_only:
        health = "REQUEST_ONLY"
        reason = "PR prose explicitly marks request-only / close-without-merge lifecycle"
    elif waiting:
        health = "WAITING_OR_BLOCKED"
        reason = "PR prose explicitly records waiting/blocking semantics"
    elif age_days is not None and age_days >= stale_days:
        health = "STALLED_SIGNAL"
        reason = f"no PR metadata update for at least {stale_days} days; signal only, never auto-close by age"
    else:
        health = "ACTIVE"
        reason = "recent or no terminal/waiting signal detected"
    return {
        "number": number,
        "title": title,
        "draft": draft,
        "head": pull_head_ref(pull),
        "head_sha": pull_head_sha(pull),
        "base": (pull.get("base") or {}).get("ref") if isinstance(pull.get("base"), dict) else None,
        "updated_at": pull.get("updated_at"),
        "age_days": None if age_days is None else round(age_days, 2),
        "health": health,
        "reason": reason,
        "auto_close": False,
    }


def pr_audit(client: GitHubClient, policy: dict[str, Any]) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc)
    pulls = [pull for pull in client.pulls("open") if same_repo_pull(pull, client.repo)]
    entries = [classify_pr_health(pull, now=now, stale_days=policy["stale_pr_days"]) for pull in pulls]
    entries.sort(key=lambda item: int(item["number"]) if isinstance(item["number"], int) else -1)
    counts = Counter(item["health"] for item in entries)
    return {
        "schema_version": 1,
        "repository": client.repo,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "stale_pr_days": policy["stale_pr_days"],
        "open_pr_count": len(entries),
        "health_counts": dict(sorted(counts.items())),
        "entries": entries,
        "auto_close_by_age": False,
    }


def event_cleanup(client: GitHubClient, policy: dict[str, Any], root: Path, event_path: Path) -> dict[str, Any]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    pull = event.get("pull_request")
    if not isinstance(pull, dict):
        raise LifecycleError("pull_request event payload missing")
    if event.get("action") != "closed":
        return {"result": "NOT_APPLICABLE", "reason": "event action is not closed"}
    if not same_repo_pull(pull, client.repo):
        return {"result": "NOT_APPLICABLE", "reason": "fork PR head is not repository-owned"}
    branch = pull_head_ref(pull)
    sha = pull_head_sha(pull)
    if branch is None or sha is None:
        raise LifecycleError("closed PR lacks exact same-repo head ref/SHA")
    current = client.get_ref_sha(branch)
    if current is None:
        return {"result": "PASS", "reason": "branch already absent", "branch": branch, "sha": sha}
    if current != sha:
        return {
            "result": "RETAINED",
            "reason": "branch moved after PR head; exact SHA no longer matches",
            "branch": branch,
            "sha": current,
        }
    claims = active_branch_claims(root)
    classification = classify_branch(
        branch=branch,
        sha=current,
        protected=False,
        policy=policy,
        active_claims=claims,
        pulls=[pull],
    )
    if classification["classification"] not in DELETION_CLASSIFICATIONS:
        return {
            "result": "RETAINED",
            "reason": classification["reason"],
            "branch": branch,
            "classification": classification["classification"],
            "sha": current,
        }
    # Re-fetch complete live inventory protections before destructive event cleanup.
    live_branch = next((item for item in client.branches() if item.get("name") == branch), None)
    if live_branch is None:
        return {"result": "PASS", "reason": "branch became absent", "branch": branch, "sha": sha}
    if bool(live_branch.get("protected")):
        return {"result": "RETAINED", "reason": "branch is protected", "branch": branch, "sha": sha}
    open_pulls = [
        p for p in client.pulls("open")
        if same_repo_pull(p, client.repo) and pull_head_ref(p) == branch
    ]
    if open_pulls:
        return {"result": "RETAINED", "reason": "branch has another open PR", "branch": branch, "sha": sha}
    client.delete_branch_exact(branch, sha)
    return {
        "result": "PASS",
        "reason": "terminal same-repo PR branch deleted at exact unchanged SHA",
        "branch": branch,
        "sha": sha,
        "pr": pull.get("number"),
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("validate-policy", "inventory", "apply", "pr-audit", "event"), required=True)
    p.add_argument("--root", default=".")
    p.add_argument("--policy", default=str(POLICY_PATH))
    p.add_argument("--output")
    p.add_argument("--event")
    p.add_argument("--evidence")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    policy = load_json(root / args.policy)
    validate_policy(policy)
    if args.mode == "validate-policy":
        print("policy: PASS")
        return 0
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", policy["repository"])
    if not token:
        raise LifecycleError("GITHUB_TOKEN is required for live modes")
    if repo.casefold() != policy["repository"].casefold():
        raise LifecycleError(f"GITHUB_REPOSITORY mismatch: {repo}")
    client = GitHubClient(repo, token, root=root)

    if args.mode == "inventory":
        result = build_inventory(client, policy, root)
    elif args.mode == "pr-audit":
        result = pr_audit(client, policy)
    elif args.mode == "apply":
        inventory = build_inventory(client, policy, root)
        result = apply_inventory(client, inventory, policy)
    elif args.mode == "event":
        if not args.event:
            raise LifecycleError("--event is required for event mode")
        result = event_cleanup(client, policy, root, Path(args.event))
    else:
        raise AssertionError(args.mode)

    text = canonical_json(result)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.evidence:
        Path(args.evidence).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LifecycleError, ApiError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
