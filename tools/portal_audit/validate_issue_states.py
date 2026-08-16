#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import os
import urllib.parse
from collections.abc import Callable
from pathlib import Path
from typing import Any

from audit_ledger import AuditLedgerError, issue_numbers, load_ledger


JsonFetcher = Callable[[str], dict[str, Any]]


def github_fetcher(repository: str, token: str, api_url: str) -> JsonFetcher:
    parsed = urllib.parse.urlsplit(api_url)
    hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise AuditLedgerError("GitHub API URL must be an absolute credential-free HTTPS URL")
    base_path = parsed.path.rstrip("/")

    def fetch(path: str) -> dict[str, Any]:
        connection = http.client.HTTPSConnection(hostname, parsed.port, timeout=20)
        endpoint = f"{base_path}/repos/{repository}/{path.lstrip('/')}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "portal-completeness-audit",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            connection.request("GET", endpoint, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            if response.status != 200:
                raise AuditLedgerError(
                    f"GitHub Issue state request for {path} returned HTTP {response.status}"
                )
            decoded = json.loads(payload)
        except (OSError, http.client.HTTPException, json.JSONDecodeError) as exc:
            raise AuditLedgerError(f"cannot verify GitHub Issue state for {path}: {exc}") from exc
        finally:
            connection.close()
        if not isinstance(decoded, dict):
            raise AuditLedgerError(f"GitHub Issue state response for {path} is not an object")
        return decoded

    return fetch


def validate_open_issue_mappings(ledger: dict[str, Any], fetch: JsonFetcher) -> None:
    closed: list[int] = []
    for number in sorted(issue_numbers(ledger)):
        payload = fetch(f"issues/{number}")
        if payload.get("pull_request") is not None:
            raise AuditLedgerError(
                f"ledger mapping #{number} resolves to a pull request, not an Issue"
            )
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


def legacy_issue_state_gate_is_applicable(repository_root: Path | None = None) -> bool:
    root = repository_root or Path(__file__).resolve().parents[2]
    registry_path = root / "ARCHITECTURE_REGISTRY.yaml"
    try:
        registry = registry_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuditLedgerError(f"cannot read architecture registry: {exc}") from exc

    adr023_markers = (
        "decision: ADR-023",
        "ADR-023 is the current product overlay for the entire Portal",
        "SHADOW/PAPER/LIVE are historical or compatibility vocabulary only",
    )
    return not all(marker in registry for marker in adr023_markers)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument(
        "--api-url",
        default=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    args = parser.parse_args()
    ledger = load_ledger()

    if not legacy_issue_state_gate_is_applicable():
        print(
            json.dumps(
                {
                    "legacy_issue_state_gate": "NOT_APPLICABLE_ADR_023",
                    "ledger_issue_mappings": len(issue_numbers(ledger)),
                    "reason": (
                        "ADR-023 supersedes legacy completeness-Issue state as current "
                        "Portal delivery authority"
                    ),
                },
                sort_keys=True,
            )
        )
        return 0

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise AuditLedgerError("GITHUB_TOKEN is required for fail-closed Issue-state validation")
    validate_open_issue_mappings(
        ledger,
        github_fetcher(args.repository, token, args.api_url),
    )
    print(
        json.dumps(
            {"verified_open_issue_mappings": len(issue_numbers(ledger))},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
