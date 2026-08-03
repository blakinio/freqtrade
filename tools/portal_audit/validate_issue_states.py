#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from audit_ledger import AuditLedgerError, issue_numbers, load_ledger

JsonFetcher = Callable[[str], dict[str, Any]]


def github_fetcher(repository: str, token: str, api_url: str) -> JsonFetcher:
    base = api_url.rstrip("/")

    def fetch(path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{base}/repos/{repository}/{path.lstrip('/')}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "portal-completeness-audit",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except (OSError, urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise AuditLedgerError(f"cannot verify GitHub Issue state for {path}: {exc}") from exc

    return fetch


def validate_open_issue_mappings(ledger: dict[str, Any], fetch: JsonFetcher) -> None:
    closed: list[int] = []
    for number in sorted(issue_numbers(ledger)):
        payload = fetch(f"issues/{number}")
        if payload.get("pull_request") is not None:
            raise AuditLedgerError(f"ledger mapping #{number} resolves to a pull request, not an Issue")
        state = payload.get("state")
        if state not in {"open", "closed"}:
            raise AuditLedgerError(f"GitHub Issue #{number} returned unknown state {state!r}")
        if state == "closed":
            closed.append(number)
    if closed:
        raise AuditLedgerError(
            "ledger still claims active gaps through closed GitHub Issues: "
            + ", ".join(f"#{number}" for number in closed)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise AuditLedgerError("GITHUB_TOKEN is required for fail-closed Issue-state validation")
    ledger = load_ledger()
    validate_open_issue_mappings(ledger, github_fetcher(args.repository, token, args.api_url))
    print(json.dumps({"verified_open_issue_mappings": len(issue_numbers(ledger))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
