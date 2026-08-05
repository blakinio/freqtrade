from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import fnmatch
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any

DEFAULT_STALE_DAYS = 14
DEFAULT_KEEP_PATTERNS = (
    "release/*",
    "hotfix/*",
    "archive/*",
)


@dataclasses.dataclass(frozen=True)
class BranchFacts:
    """Facts required to decide whether a branch may be deleted safely."""

    name: str
    head_sha: str
    age_days: int
    protected: bool
    has_open_pull_request: bool
    has_merged_pull_request_at_head: bool
    unique_commits: int


@dataclasses.dataclass(frozen=True)
class BranchDecision:
    """Deletion decision and its deterministic reasons."""

    eligible: bool
    reasons: tuple[str, ...]


def evaluate_branch(
    facts: BranchFacts,
    *,
    default_branch: str,
    stale_days: int = DEFAULT_STALE_DAYS,
    keep_patterns: Iterable[str] = DEFAULT_KEEP_PATTERNS,
) -> BranchDecision:
    """Return whether a branch satisfies every safe-deletion predicate."""
    reasons: list[str] = []

    if facts.name == default_branch:
        reasons.append("default_branch")
    if facts.protected:
        reasons.append("protected")
    if facts.has_open_pull_request:
        reasons.append("open_pull_request")
    if facts.age_days < stale_days:
        reasons.append("younger_than_retention")
    if facts.unique_commits != 0 and not facts.has_merged_pull_request_at_head:
        reasons.append("contains_unmerged_unique_commits")
    if any(fnmatch.fnmatchcase(facts.name, pattern) for pattern in keep_patterns):
        reasons.append("keep_pattern")

    return BranchDecision(eligible=not reasons, reasons=tuple(reasons))


class GitHubApi:
    """Minimal GitHub REST client used by the bounded hygiene command."""

    def __init__(self, repository: str, token: str) -> None:
        self.repository = repository
        self.base_url = f"https://api.github.com/repos/{repository}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "freqtrade-branch-hygiene",
        }

    def _request(
        self,
        url: str,
        *,
        method: str = "GET",
    ) -> tuple[Any, dict[str, str]]:
        request = urllib.request.Request(url, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                payload = json.loads(raw.decode("utf-8")) if raw else None
                return payload, dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API {method} {url} failed with {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"GitHub API request failed: {exc}") from exc

    def _paginate(self, url: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url: str | None = url
        while next_url:
            payload, headers = self._request(next_url)
            if not isinstance(payload, list):
                raise RuntimeError(f"expected list response from {next_url}")
            items.extend(item for item in payload if isinstance(item, dict))
            next_url = _next_link(headers.get("Link", ""))
        return items

    def default_branch(self) -> str:
        payload, _ = self._request(self.base_url)
        if not isinstance(payload, dict) or not isinstance(
            payload.get("default_branch"), str
        ):
            raise RuntimeError("repository response did not contain default_branch")
        return payload["default_branch"]

    def protected_branches(self) -> set[str]:
        items = self._paginate(f"{self.base_url}/branches?protected=true&per_page=100")
        return {
            str(item["name"])
            for item in items
            if isinstance(item.get("name"), str)
        }

    def open_pull_request_heads(self) -> set[str]:
        items = self._paginate(f"{self.base_url}/pulls?state=open&per_page=100")
        heads: set[str] = set()
        for item in items:
            head = item.get("head")
            if isinstance(head, dict) and isinstance(head.get("ref"), str):
                heads.add(head["ref"])
        return heads

    def merged_pull_request_heads(self) -> set[tuple[str, str]]:
        """Return same-repository branch refs and exact heads merged by PR."""
        items = self._paginate(
            f"{self.base_url}/pulls?state=closed&sort=updated&direction=desc&per_page=100"
        )
        merged_heads: set[tuple[str, str]] = set()
        for item in items:
            if not isinstance(item.get("merged_at"), str):
                continue
            head = item.get("head")
            if not isinstance(head, dict):
                continue
            repository = head.get("repo")
            branch = head.get("ref")
            sha = head.get("sha")
            if (
                isinstance(repository, dict)
                and repository.get("full_name") == self.repository
                and isinstance(branch, str)
                and isinstance(sha, str)
            ):
                merged_heads.add((branch, sha))
        return merged_heads

    def delete_branch(self, branch: str) -> None:
        encoded = urllib.parse.quote(branch, safe="/")
        self._request(f"{self.base_url}/git/refs/heads/{encoded}", method="DELETE")


def _next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) < 2:
            continue
        url = section[0].strip()
        rel = ";".join(section[1:])
        if 'rel="next"' in rel and url.startswith("<") and url.endswith(">"):
            return url[1:-1]
    return None


def _git(*args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if process.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout.strip()


def _remote_branches(remote: str) -> list[str]:
    prefix = f"refs/remotes/{remote}/"
    output = _git("for-each-ref", "--format=%(refname)", prefix)
    branches: list[str] = []
    for ref in output.splitlines():
        if not ref.startswith(prefix):
            continue
        name = ref[len(prefix) :]
        if name == "HEAD":
            continue
        branches.append(name)
    return sorted(branches)


def _branch_head_sha(remote: str, branch: str) -> str:
    return _git("rev-parse", f"{remote}/{branch}")


def _branch_age_days(remote: str, branch: str, now: dt.datetime) -> int:
    timestamp = int(_git("log", "-1", "--format=%ct", f"{remote}/{branch}"))
    committed = dt.datetime.fromtimestamp(timestamp, tz=dt.UTC)
    return max(0, (now - committed).days)


def _unique_commit_count(remote: str, default_branch: str, branch: str) -> int:
    output = _git(
        "rev-list",
        "--count",
        f"{remote}/{default_branch}..{remote}/{branch}",
    )
    return int(output)


def collect_branch_facts(
    *,
    remote: str,
    default_branch: str,
    protected_branches: set[str],
    open_pull_request_heads: set[str],
    merged_pull_request_heads: set[tuple[str, str]],
    now: dt.datetime,
) -> list[BranchFacts]:
    """Collect local Git and GitHub facts for every remote branch."""
    facts: list[BranchFacts] = []
    for branch in _remote_branches(remote):
        head_sha = _branch_head_sha(remote, branch)
        facts.append(
            BranchFacts(
                name=branch,
                head_sha=head_sha,
                age_days=_branch_age_days(remote, branch, now),
                protected=branch in protected_branches,
                has_open_pull_request=branch in open_pull_request_heads,
                has_merged_pull_request_at_head=(
                    branch,
                    head_sha,
                )
                in merged_pull_request_heads,
                unique_commits=_unique_commit_count(remote, default_branch, branch),
            )
        )
    return facts


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory remote branches and optionally delete only old, reviewed, "
            "merged and otherwise unprotected branches without open pull requests."
        )
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="Repository in owner/name form.",
    )
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--default-branch")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument(
        "--keep-pattern",
        action="append",
        default=[],
        help="Additional fnmatch pattern that must never be deleted.",
    )
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--confirm-repository",
        help="Required with --apply and must exactly equal --repository.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.repository:
        print("branch hygiene failed: --repository is required", file=sys.stderr)
        return 2
    if args.stale_days < 1:
        print("branch hygiene failed: --stale-days must be positive", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("branch hygiene failed: GITHUB_TOKEN is required", file=sys.stderr)
        return 2
    if args.apply and args.confirm_repository != args.repository:
        print(
            "branch hygiene failed: --apply requires an exact "
            "--confirm-repository value",
            file=sys.stderr,
        )
        return 2

    api = GitHubApi(args.repository, token)
    default_branch = args.default_branch or api.default_branch()

    _git(
        "fetch",
        args.remote,
        f"+refs/heads/*:refs/remotes/{args.remote}/*",
        "--prune",
        "--no-tags",
    )
    facts = collect_branch_facts(
        remote=args.remote,
        default_branch=default_branch,
        protected_branches=api.protected_branches(),
        open_pull_request_heads=api.open_pull_request_heads(),
        merged_pull_request_heads=api.merged_pull_request_heads(),
        now=dt.datetime.now(tz=dt.UTC),
    )

    keep_patterns = (*DEFAULT_KEEP_PATTERNS, *args.keep_pattern)
    records: list[dict[str, Any]] = []
    deleted: list[str] = []
    for branch in facts:
        decision = evaluate_branch(
            branch,
            default_branch=default_branch,
            stale_days=args.stale_days,
            keep_patterns=keep_patterns,
        )
        status = "candidate" if decision.eligible else "retained"
        if args.apply and decision.eligible:
            api.delete_branch(branch.name)
            deleted.append(branch.name)
            status = "deleted"
        records.append(
            {
                **dataclasses.asdict(branch),
                "eligible": decision.eligible,
                "reasons": list(decision.reasons),
                "status": status,
            }
        )

    report = {
        "repository": args.repository,
        "default_branch": default_branch,
        "stale_days": args.stale_days,
        "mode": "apply" if args.apply else "dry-run",
        "branch_count": len(records),
        "candidate_count": sum(1 for record in records if record["eligible"]),
        "deleted_count": len(deleted),
        "deleted": deleted,
        "branches": records,
    }
    if args.report_json:
        _write_report(args.report_json, report)
    print(json.dumps({key: value for key, value in report.items() if key != "branches"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
