from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from ai_platform.scripts.liquidation_alert_notifications import (
    GitHubApiClient,
    HEALTH_WORKFLOW,
    main as notification_main,
    OPERATIONAL_TITLE,
    STALE_MONITOR_MS,
)


MONITOR_STALE_CODE = "LIQUIDATIONS_HEALTH_MONITOR_STALE"
ACTIVE_RUN_STATUSES = {"queued", "in_progress", "pending", "requested", "waiting"}


class WatchdogClient(Protocol):
    def list_issues(self, repository: str, *, state: str = "all") -> list[dict[str, Any]]: ...

    def list_workflow_runs(self, repository: str, workflow: str) -> list[dict[str, Any]]: ...

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ScheduleDecision:
    action: Literal["continue", "dispatched", "waiting", "recovered"]
    issue_number: int | None = None


def _epoch_ms(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


def _extract_json_report(body: str) -> dict[str, Any]:
    for match in re.finditer(r"```json\s*(\{.*?\})\s*```", body, flags=re.DOTALL):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _open_operational_issue(client: WatchdogClient, repository: str) -> dict[str, Any] | None:
    return next(
        (
            issue
            for issue in client.list_issues(repository, state="all")
            if issue.get("title") == OPERATIONAL_TITLE and issue.get("state") == "open"
        ),
        None,
    )


def _issue_codes(issue: dict[str, Any] | None) -> tuple[str, ...]:
    body = str((issue or {}).get("body") or "")
    return tuple(sorted(set(re.findall(r"(?:Code|Kod):\s*`?([A-Z0-9_]+)`?", body))))


def _is_synthetic_stale_issue(issue: dict[str, Any] | None) -> bool:
    if issue is None:
        return False
    body = str(issue.get("body") or "")
    return MONITOR_STALE_CODE in _issue_codes(issue) and not _extract_json_report(body)


def reconcile_schedule(
    client: WatchdogClient,
    repository: str,
    *,
    now_ms: int,
    dispatch: Callable[[], None],
) -> ScheduleDecision:
    issue = _open_operational_issue(client, repository)
    runs = client.list_workflow_runs(repository, HEALTH_WORKFLOW)
    latest = runs[0] if runs else {}
    created_at_ms = _epoch_ms(str(latest.get("created_at") or ""))
    status = str(latest.get("status") or "")
    conclusion = str(latest.get("conclusion") or "")
    stale = not latest or created_at_ms is None
    if created_at_ms is not None and now_ms - created_at_ms > STALE_MONITOR_MS:
        stale = True

    synthetic_stale_issue = _is_synthetic_stale_issue(issue)
    issue_number = int(issue["number"]) if issue and issue.get("number") else None

    if issue is not None and not synthetic_stale_issue:
        return ScheduleDecision("continue", issue_number)

    if synthetic_stale_issue and not stale:
        if status in ACTIVE_RUN_STATUSES:
            return ScheduleDecision("waiting", issue_number)
        if status == "completed" and conclusion == "success" and issue_number is not None:
            client.update_issue(repository, issue_number, state="closed")
            return ScheduleDecision("recovered", issue_number)

    if not stale:
        return ScheduleDecision("continue", issue_number)

    if status in ACTIVE_RUN_STATUSES:
        return ScheduleDecision("continue", issue_number)

    dispatch()
    return ScheduleDecision("dispatched", issue_number)


def dispatch_health_workflow(repository: str, token: str, *, api_url: str) -> None:
    if not repository or not token:
        raise RuntimeError("GitHub repository and token are required for health dispatch")
    data = json.dumps({"ref": "develop"}, separators=(",", ":")).encode()
    request = urllib.request.Request(  # noqa: S310
        f"{api_url.rstrip('/')}/repos/{repository}/actions/workflows/{HEALTH_WORKFLOW}/dispatches",
        data=data,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "freqtrade-liquidations-health-self-heal",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Health workflow dispatch failed with HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError("Health workflow dispatch failed") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Self-heal stale Liquidations health schedules before Telegram escalation."
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "bootstrap", "test", "controlled_failure", "controlled_recovery"),
        default="auto",
    )
    parser.add_argument("--issue-number", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode != "auto" or os.environ.get("GITHUB_EVENT_NAME") != "schedule":
        return notification_main(argv)

    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GH_TOKEN", "")
    if not repository or not token:
        print("GitHub repository and token are required", file=sys.stderr)
        return 2

    client = GitHubApiClient(
        token, api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com")
    )
    try:
        decision = reconcile_schedule(
            client,
            repository,
            now_ms=time.time_ns() // 1_000_000,
            dispatch=lambda: dispatch_health_workflow(
                repository,
                token,
                api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
            ),
        )
    except RuntimeError as error:
        print(f"Stale-monitor self-heal failed: {error}", file=sys.stderr)
        return notification_main(argv)

    if decision.action in {"dispatched", "waiting"}:
        print(f"Liquidations health self-heal action: {decision.action}")
        return 0
    if decision.action == "recovered" and decision.issue_number is not None:
        return notification_main(["--mode", "auto", "--issue-number", str(decision.issue_number)])
    return notification_main(argv)


if __name__ == "__main__":
    sys.exit(main())
