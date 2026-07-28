from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Protocol


LIVE_CONTRACT = "liquidation-live-state-v1"
REQUIRED_SOURCES = ("bybit-linear", "binance-usdm")
ALERT_TITLE = "[liquidations-live] operational health alert"
ALERT_MARKER = "<!-- liquidations-live-operational-health -->"


class IssueClient(Protocol):
    def list_open_issues(self, repository: str) -> list[dict[str, Any]]:
        ...

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]:
        ...

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        ...

    def create_comment(self, repository: str, issue_number: int, *, body: str) -> None:
        ...


class GitHubIssueClient:
    def __init__(self, token: str, *, api_url: str = "https://api.github.com") -> None:
        if not token:
            raise ValueError("GitHub token is required")
        self._token = token
        self._api_url = api_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode()
        request = urllib.request.Request(
            f"{self._api_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "freqtrade-liquidations-live-health",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
                raw = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:1000]
            message = f"GitHub API {method} {path} failed: {error.code} {detail}"
            raise RuntimeError(message) from error
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))

    def list_open_issues(self, repository: str) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode({"state": "open", "per_page": 100})
        payload = self._request("GET", f"/repos/{repository}/issues?{query}")
        if not isinstance(payload, list):
            raise RuntimeError("GitHub issues response is not a list")
        return [item for item in payload if isinstance(item, dict)]

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/repos/{repository}/issues",
            {"title": title, "body": body},
        )
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub create issue response is not an object")
        return payload

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        update: dict[str, Any] = {}
        if body is not None:
            update["body"] = body
        if state is not None:
            update["state"] = state
        payload = self._request(
            "PATCH",
            f"/repos/{repository}/issues/{issue_number}",
            update,
        )
        if not isinstance(payload, dict):
            raise RuntimeError("GitHub update issue response is not an object")
        return payload

    def create_comment(self, repository: str, issue_number: int, *, body: str) -> None:
        self._request(
            "POST",
            f"/repos/{repository}/issues/{issue_number}/comments",
            {"body": body},
        )


def _alert(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message, "severity": "critical"}


def _heartbeat_age(now_ms: int, value: object) -> int | None:
    return now_ms - value if isinstance(value, int) else None


def _fresh(age_ms: int | None, limit_ms: int) -> bool:
    return isinstance(age_ms, int) and -limit_ms <= age_ms <= limit_ms


def _container_result(container: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    healthy = (
        container.get("running") is True
        and container.get("status") == "running"
        and container.get("restarting") is not True
        and container.get("oom_killed") is not True
        and not container.get("error")
    )
    alerts: list[dict[str, str]] = []
    if not healthy:
        alerts.append(
            _alert(
                "LIQUID20_CONTAINER_UNHEALTHY",
                f"Collector container is not healthy: status={container.get('status', 'unknown')}",
            )
        )
    return {**container, "healthy": healthy}, alerts


def _source_result(
    *,
    source_name: str,
    source: object,
    now_ms: int,
    stale_after_ms: int,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    configured = isinstance(source, dict) and source.get("configured") is True
    connected = isinstance(source, dict) and source.get("connected") is True
    subscriptions = source.get("subscription_symbol_count") if isinstance(source, dict) else None
    heartbeat = source.get("last_heartbeat_at_ms") if isinstance(source, dict) else None
    heartbeat_age_ms = _heartbeat_age(now_ms, heartbeat)
    healthy = (
        configured
        and connected
        and isinstance(subscriptions, int)
        and subscriptions >= 1
        and _fresh(heartbeat_age_ms, stale_after_ms)
    )
    result = {
        "configured": configured,
        "connected": connected,
        "subscription_symbol_count": subscriptions,
        "heartbeat_age_ms": heartbeat_age_ms,
        "healthy": healthy,
    }
    if healthy:
        return result, []
    message = (
        f"{source_name} unhealthy: configured={configured}, connected={connected}, "
        f"subscriptions={subscriptions!r}, heartbeat_age_ms={heartbeat_age_ms!r}"
    )
    return result, [_alert("LIQUID20_SOURCE_UNHEALTHY", message)]


def _state_result(
    *,
    pointer: dict[str, Any] | None,
    now_ms: int,
    stale_after_ms: int,
    source_stale_after_ms: int,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    if not isinstance(pointer, dict):
        return (
            {"healthy": False},
            {},
            [_alert("LIQUID20_STATE_UNAVAILABLE", "Live state pointer is missing or invalid.")],
        )

    state = pointer.get("state")
    state_dict = state if isinstance(state, dict) else {}
    contract_ok = (
        pointer.get("contract") == LIVE_CONTRACT
        and state_dict.get("contract") == LIVE_CONTRACT
    )
    active = state_dict.get("run_state") == "active"
    heartbeat_age_ms = _heartbeat_age(now_ms, state_dict.get("collector_heartbeat_at_ms"))
    heartbeat_fresh = _fresh(heartbeat_age_ms, stale_after_ms)
    safety_ok = (
        state_dict.get("execution_enabled") is False
        and state_dict.get("trading_authorized") is False
        and state_dict.get("trading_credentials_present") is False
    )

    alerts: list[dict[str, str]] = []
    if not contract_ok:
        alerts.append(
            _alert(
                "LIQUID20_STATE_CONTRACT_INVALID",
                "Live state contract does not match liquidation-live-state-v1.",
            )
        )
    if not active:
        alerts.append(_alert("LIQUID20_RUN_NOT_ACTIVE", "Collector run is not active."))
    if not heartbeat_fresh:
        alerts.append(
            _alert(
                "LIQUID20_COLLECTOR_HEARTBEAT_STALE",
                f"Collector heartbeat age is {heartbeat_age_ms!r} ms.",
            )
        )
    if not safety_ok:
        alerts.append(
            _alert(
                "LIQUID20_DATA_ONLY_SAFETY_VIOLATION",
                "Collector no longer proves execution-disabled, credential-free data-only mode.",
            )
        )

    source_results: dict[str, Any] = {}
    sources = state_dict.get("sources")
    for source_name in REQUIRED_SOURCES:
        source = sources.get(source_name) if isinstance(sources, dict) else None
        result, source_alerts = _source_result(
            source_name=source_name,
            source=source,
            now_ms=now_ms,
            stale_after_ms=source_stale_after_ms,
        )
        source_results[source_name] = result
        alerts.extend(source_alerts)

    state_result = {
        "active": active,
        "collector_heartbeat_age_ms": heartbeat_age_ms,
        "contract_ok": contract_ok,
        "healthy": contract_ok and active and heartbeat_fresh and safety_ok,
        "run_id": state_dict.get("run_id"),
        "safety_ok": safety_ok,
    }
    return state_result, source_results, alerts


def _disk_result(
    *,
    disk: dict[str, int],
    used_percent_max: float,
    free_bytes_min: int,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    total = int(disk.get("total", 0))
    used = int(disk.get("used", 0))
    free = int(disk.get("free", 0))
    used_percent = (used / total * 100.0) if total > 0 else 100.0
    healthy = total > 0 and used_percent < used_percent_max and free >= free_bytes_min
    result = {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "used_percent": round(used_percent, 3),
        "used_percent_max": used_percent_max,
        "free_bytes_min": free_bytes_min,
        "healthy": healthy,
    }
    alerts: list[dict[str, str]] = []
    if total <= 0:
        alerts.append(_alert("LIQUID20_DISK_UNAVAILABLE", "Disk usage is unavailable."))
    if total > 0 and used_percent >= used_percent_max:
        alerts.append(
            _alert(
                "LIQUID20_DISK_USAGE_HIGH",
                f"Data volume usage is {used_percent:.2f}% (limit {used_percent_max:.2f}%).",
            )
        )
    if total > 0 and free < free_bytes_min:
        alerts.append(
            _alert(
                "LIQUID20_DISK_FREE_LOW",
                f"Data volume free bytes are {free} (minimum {free_bytes_min}).",
            )
        )
    return result, alerts


def evaluate_health(
    *,
    now_ms: int,
    container: dict[str, Any],
    pointer: dict[str, Any] | None,
    disk: dict[str, int],
    stale_after_ms: int,
    source_stale_after_ms: int,
    disk_used_percent_max: float,
    disk_free_bytes_min: int,
) -> dict[str, Any]:
    container_result, container_alerts = _container_result(container)
    state_result, source_results, state_alerts = _state_result(
        pointer=pointer,
        now_ms=now_ms,
        stale_after_ms=stale_after_ms,
        source_stale_after_ms=source_stale_after_ms,
    )
    disk_result, disk_alerts = _disk_result(
        disk=disk,
        used_percent_max=disk_used_percent_max,
        free_bytes_min=disk_free_bytes_min,
    )
    alerts = container_alerts + state_alerts + disk_alerts
    return {
        "schema_version": 1,
        "checked_at_ms": now_ms,
        "healthy": not alerts,
        "alerts": alerts,
        "checks": {
            "container": container_result,
            "state": state_result,
            "sources": source_results,
            "disk": disk_result,
        },
    }


def inspect_container(container_name: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{json .State}}", container_name],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        state = json.loads(result.stdout)
        if not isinstance(state, dict):
            raise ValueError("container state is not an object")
        return {
            "running": state.get("Running") is True,
            "status": state.get("Status"),
            "restarting": state.get("Restarting") is True,
            "oom_killed": state.get("OOMKilled") is True,
            "exit_code": state.get("ExitCode"),
            "error": state.get("Error") or None,
        }
    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as error:
        return {
            "running": False,
            "status": "unavailable",
            "restarting": False,
            "oom_killed": False,
            "exit_code": None,
            "error": f"{type(error).__name__}: {error}"[:500],
        }


def read_live_pointer(data_root: Path) -> dict[str, Any] | None:
    pointer = data_root / "live" / "live-state-v1.json"
    try:
        if not data_root.is_dir() or data_root.is_symlink():
            return None
        if not pointer.is_file() or pointer.is_symlink():
            return None
        payload = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def disk_snapshot(data_root: Path) -> dict[str, int]:
    try:
        usage = shutil.disk_usage(data_root)
    except OSError:
        return {"total": 0, "used": 0, "free": 0}
    return {"total": usage.total, "used": usage.used, "free": usage.free}


def render_issue_body(report: dict[str, Any], *, run_url: str | None) -> str:
    alerts = report.get("alerts", [])
    lines = [
        ALERT_MARKER,
        "The Synology liquidation live collector failed its operational health check.",
        "",
        f"- Checked at (epoch ms): `{report.get('checked_at_ms')}`",
        f"- Workflow run: {run_url or 'unavailable'}",
        f"- Alert count: `{len(alerts) if isinstance(alerts, list) else 'unknown'}`",
        "",
        "```json",
        json.dumps(report, indent=2, sort_keys=True),
        "```",
        "",
        "This issue is updated while unhealthy and closed automatically after recovery.",
    ]
    return "\n".join(lines)


def reconcile_alert_issue(
    client: IssueClient,
    repository: str,
    report: dict[str, Any],
    *,
    run_url: str | None = None,
) -> str:
    open_issues = client.list_open_issues(repository)
    existing = next(
        (
            item
            for item in open_issues
            if item.get("title") == ALERT_TITLE and "pull_request" not in item
        ),
        None,
    )
    if report.get("healthy") is not True:
        body = render_issue_body(report, run_url=run_url)
        if existing is None:
            client.create_issue(repository, title=ALERT_TITLE, body=body)
            return "created"
        client.update_issue(repository, int(existing["number"]), body=body)
        return "updated"
    if existing is None:
        return "none"
    issue_number = int(existing["number"])
    client.create_comment(
        repository,
        issue_number,
        body=(
            "Collector health recovered. The monitor now reports a fresh heartbeat, "
            "connected sources and acceptable disk capacity."
        ),
    )
    client.update_issue(repository, issue_number, state="closed")
    return "closed"


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def _percentage(value: str) -> float:
    parsed = float(value)
    if parsed <= 0 or parsed > 100:
        raise argparse.ArgumentTypeError("value must be > 0 and <= 100")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor the Synology liquidation collector.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(
            os.environ.get(
                "LIQUID20_DATA_ROOT",
                "/volume1/docker/freqtrade-liquidations/data",
            )
        ),
    )
    parser.add_argument(
        "--container-name",
        default=os.environ.get("LIQUID20_CONTAINER_NAME", "liquid20-live"),
    )
    parser.add_argument(
        "--stale-after-seconds",
        type=_positive_int,
        default=int(os.environ.get("LIQUID20_HEARTBEAT_STALE_SECONDS", "60")),
    )
    parser.add_argument(
        "--source-stale-after-seconds",
        type=_positive_int,
        default=int(os.environ.get("LIQUID20_SOURCE_STALE_SECONDS", "60")),
    )
    parser.add_argument(
        "--disk-used-percent-max",
        type=_percentage,
        default=float(os.environ.get("LIQUID20_DISK_USED_PERCENT_MAX", "90")),
    )
    parser.add_argument(
        "--disk-free-bytes-min",
        type=_positive_int,
        default=int(os.environ.get("LIQUID20_DISK_FREE_BYTES_MIN", str(20 * 1024**3))),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(os.environ.get("LIQUID20_HEALTH_REPORT", "/tmp/liquid20-health.json")),
    )
    parser.add_argument("--github-repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--github-token-env", default="GH_TOKEN")
    parser.add_argument(
        "--github-api-url",
        default=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    parser.add_argument("--run-url", default=None)
    return parser


def _workflow_run_url() -> str | None:
    run_id = os.environ.get("GITHUB_RUN_ID")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not run_id or not repository:
        return None
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    return f"{server}/{repository}/actions/runs/{run_id}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate_health(
        now_ms=time.time_ns() // 1_000_000,
        container=inspect_container(args.container_name),
        pointer=read_live_pointer(args.data_root),
        disk=disk_snapshot(args.data_root),
        stale_after_ms=args.stale_after_seconds * 1000,
        source_stale_after_ms=args.source_stale_after_seconds * 1000,
        disk_used_percent_max=args.disk_used_percent_max,
        disk_free_bytes_min=args.disk_free_bytes_min,
    )
    token = os.environ.get(args.github_token_env, "")
    if args.github_repository and token:
        try:
            client = GitHubIssueClient(token, api_url=args.github_api_url)
            report["github_alert_action"] = reconcile_alert_issue(
                client,
                args.github_repository,
                report,
                run_url=args.run_url or _workflow_run_url(),
            )
        except (OSError, RuntimeError, ValueError) as error:
            report["alerts"].append(
                _alert(
                    "LIQUID20_ALERT_DELIVERY_FAILED",
                    f"GitHub alert reconciliation failed: {type(error).__name__}: {error}"[:500],
                )
            )
            report["healthy"] = False
            report["github_alert_action"] = "failed"
    else:
        report["github_alert_action"] = "disabled"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    return 0 if report["healthy"] is True else 1


if __name__ == "__main__":
    sys.exit(main())
