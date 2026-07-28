from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Protocol

from ai_platform.scripts.liquidation_live_health import (
    ALERT_MARKER,
    ALERT_TITLE,
    GitHubIssueClient,
    _alert,
    _workflow_run_url,
    build_parser as build_collector_parser,
    disk_snapshot,
    evaluate_health,
    inspect_container,
    read_live_pointer,
)

MAX_PORTAL_REPORT_BYTES = 2 * 1024 * 1024
REQUIRED_PORTAL_SOURCES = ("bybit-linear", "binance-usdm")


class IssueClient(Protocol):
    def list_open_issues(self, repository: str) -> list[dict[str, Any]]: ...

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]: ...

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]: ...

    def create_comment(self, repository: str, issue_number: int, *, body: str) -> None: ...


def read_portal_report(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_PORTAL_REPORT_BYTES:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _record(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def evaluate_portal_report(
    report: dict[str, Any] | None,
    *,
    required: bool,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    if not required:
        return {"enabled": False, "healthy": True, "mode": None}, []
    if not isinstance(report, dict):
        return (
            {"enabled": True, "healthy": False, "mode": None},
            [
                _alert(
                    "PORTAL_LIQUIDATIONS_HEALTH_UNAVAILABLE",
                    "Portal health report is missing or invalid.",
                )
            ],
        )

    production = _record(report.get("production_portal"))
    boundary = _record(production.get("unauthenticated_boundary"))
    candidate = _record(report.get("isolated_candidate"))
    observation = _record(report.get("observation"))
    health = _record(observation.get("health"))
    api_status = _record(observation.get("api_status"))
    cache_control = _record(observation.get("cache_control"))
    candidate_boundary = _record(observation.get("unauthenticated_boundary"))
    sources = _record(health.get("sources"))

    mode = health.get("mode") if isinstance(health.get("mode"), str) else None
    boundary_ok = (
        boundary.get("page_status") == 200
        and boundary.get("health_status") == 401
        and boundary.get("health_code") == "SESSION_MISSING"
        and "no-store" in str(boundary.get("health_cache_control") or "")
    )
    candidate_boundary_ok = (
        candidate_boundary.get("health_status") == 401
        and candidate_boundary.get("health_code") == "SESSION_MISSING"
        and "no-store" in str(candidate_boundary.get("health_cache_control") or "")
    )
    exact_image = (
        bool(production.get("image"))
        and production.get("image") == candidate.get("image")
        and production.get("image_id") == candidate.get("image_id")
    )
    runtime_ok = (
        isinstance(candidate.get("uid"), int)
        and candidate["uid"] != 0
        and candidate.get("restart_policy") == "no"
        and candidate.get("fixture_identity") is True
        and candidate.get("fixture_session_validated") is True
        and candidate.get("read_only_root_filesystem") is True
        and candidate.get("cap_drop") == ["ALL"]
        and candidate.get("no_new_privileges") is True
        and candidate.get("memory_limit_bytes") == 805306368
        and candidate.get("real_data_mount_read_only") is True
        and candidate.get("docker_socket_mounted") is False
        and set(_record(candidate.get("tmpfs"))) == {"/tmp", "/app/.next/cache"}
    )
    api_ok = (
        observation.get("page_status") == 200
        and api_status.get("health") == 200
        and api_status.get("list") == 200
        and api_status.get("summary") == 200
        and all(
            "no-store" in str(cache_control.get(name) or "")
            for name in ("health", "list", "summary")
        )
    )
    health_contract_ok = (
        health.get("contract") == "portal-liquidations-health-v2"
        and health.get("run_state") in {"active", "completed"}
        and isinstance(health.get("collector_heartbeat_at_ms"), int)
        and isinstance(health.get("portal_checked_at_ms"), int)
        and health.get("research_preview") is True
        and health.get("trading_authorized") is False
    )

    source_results: dict[str, Any] = {}
    sources_ok = True
    for source in REQUIRED_PORTAL_SOURCES:
        item = _record(sources.get(source))
        source_ok = (
            item.get("configured") is True
            and item.get("connected") is True
            and isinstance(item.get("subscription_symbol_count"), int)
            and item["subscription_symbol_count"] >= 1
            and isinstance(item.get("events"), int)
            and item["events"] >= 0
        )
        source_results[source] = {
            "configured": item.get("configured"),
            "connected": item.get("connected"),
            "subscription_symbol_count": item.get("subscription_symbol_count"),
            "events": item.get("events"),
            "healthy": source_ok,
        }
        sources_ok = sources_ok and source_ok

    alerts: list[dict[str, str]] = []
    if not boundary_ok:
        alerts.append(
            _alert(
                "PORTAL_PRODUCTION_BOUNDARY_UNHEALTHY",
                "Production portal page/authentication/no-store boundary is not healthy.",
            )
        )
    if not candidate_boundary_ok:
        alerts.append(
            _alert(
                "PORTAL_CANDIDATE_AUTH_BOUNDARY_UNHEALTHY",
                "Isolated candidate no longer rejects unauthenticated access with SESSION_MISSING.",
            )
        )
    if not exact_image:
        alerts.append(
            _alert(
                "PORTAL_CANDIDATE_IMAGE_MISMATCH",
                "Isolated candidate does not use the exact production image and image ID.",
            )
        )
    if not runtime_ok:
        alerts.append(
            _alert(
                "PORTAL_CANDIDATE_SECURITY_UNHEALTHY",
                "Isolated candidate runtime security contract is incomplete.",
            )
        )
    if not api_ok:
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_API_UNHEALTHY",
                "Portal health/list/summary/page checks are unavailable or violate no-store.",
            )
        )
    if not health_contract_ok:
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_CONTRACT_INVALID",
                "Portal Liquid20 health payload violates the expected read-only contract.",
            )
        )
    if not sources_ok:
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_SOURCE_UNHEALTHY",
                "Portal does not report fresh connected Bybit and Binance subscriptions.",
            )
        )

    if mode == "stale":
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_STALE",
                "Portal reports the Liquid20 dataset as STALE.",
            )
        )
    elif mode == "offline":
        alerts.append(
            _alert("PORTAL_LIQUIDATIONS_OFFLINE", "Portal reports the Liquid20 dataset as OFFLINE.")
        )
    elif mode == "historical":
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_HISTORICAL",
                "Portal fell back to HISTORICAL instead of the continuous live dataset.",
            )
        )
    elif mode != "live":
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_MODE_INVALID",
                f"Portal mode is missing or invalid: {mode!r}.",
            )
        )

    if report.get("result") != "success" and not alerts:
        alerts.append(
            _alert(
                "PORTAL_LIQUIDATIONS_PROBE_FAILED",
                str(report.get("rejection_reason") or "Portal health probe failed.")[:500],
            )
        )

    healthy = not alerts
    return (
        {
            "enabled": True,
            "healthy": healthy,
            "mode": mode,
            "result": report.get("result"),
            "rejection_reason": report.get("rejection_reason"),
            "commit_sha": report.get("commit_sha"),
            "production": {
                "page_status": boundary.get("page_status"),
                "protected_health_status": boundary.get("health_status"),
                "protected_health_code": boundary.get("health_code"),
                "protected_health_cache_control": boundary.get("health_cache_control"),
            },
            "candidate": {
                "exact_production_image": exact_image,
                "uid": candidate.get("uid"),
                "read_only_root_filesystem": candidate.get("read_only_root_filesystem"),
                "cap_drop": candidate.get("cap_drop"),
                "no_new_privileges": candidate.get("no_new_privileges"),
                "real_data_mount_read_only": candidate.get("real_data_mount_read_only"),
                "docker_socket_mounted": candidate.get("docker_socket_mounted"),
            },
            "observation": {
                "run_state": health.get("run_state"),
                "run_id": health.get("run_id"),
                "collector_heartbeat_at_ms": health.get("collector_heartbeat_at_ms"),
                "portal_checked_at_ms": health.get("portal_checked_at_ms"),
                "last_event_at_ms": health.get("last_event_at_ms"),
                "last_event_received_at_ms": health.get("last_event_received_at_ms"),
                "sources": source_results,
            },
        },
        alerts,
    )


def render_issue_body(report: dict[str, Any], *, run_url: str | None) -> str:
    alerts = report.get("alerts", [])
    lines = [
        ALERT_MARKER,
        "The Synology Liquid20 collector or portal read path failed its operational health check.",
        "",
        f"- Checked at (epoch ms): `{report.get('checked_at_ms')}`",
        f"- Workflow run: {run_url or 'unavailable'}",
        f"- Portal mode: `{_record(_record(report.get('checks')).get('portal')).get('mode')}`",
        f"- Alert count: `{len(alerts) if isinstance(alerts, list) else 'unknown'}`",
        "",
        "```json",
        json.dumps(report, indent=2, sort_keys=True),
        "```",
        "",
        "This issue is updated while unhealthy and closed automatically after full recovery.",
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
            "Liquid20 operational health recovered. The collector heartbeat and sources are fresh, "
            "disk capacity is acceptable, and the portal reports the live read path as LIVE."
        ),
    )
    client.update_issue(repository, issue_number, state="closed")
    return "closed"


def build_parser() -> argparse.ArgumentParser:
    parser = build_collector_parser()
    parser.description = "Monitor the Synology Liquid20 collector and portal read path."
    parser.add_argument(
        "--portal-report",
        type=Path,
        default=(
            Path(os.environ["LIQUID20_PORTAL_HEALTH_REPORT"])
            if os.environ.get("LIQUID20_PORTAL_HEALTH_REPORT")
            else None
        ),
    )
    parser.add_argument(
        "--require-portal",
        action="store_true",
        default=os.environ.get("LIQUID20_REQUIRE_PORTAL_HEALTH", "").lower() == "true",
    )
    return parser


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
    portal_result, portal_alerts = evaluate_portal_report(
        read_portal_report(args.portal_report),
        required=args.require_portal,
    )
    report["schema_version"] = 2
    report["checks"]["portal"] = portal_result
    report["alerts"].extend(portal_alerts)
    report["healthy"] = not report["alerts"]

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
