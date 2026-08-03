from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import ai_platform.scripts.liquidation_live_health as live_health_module
import ai_platform.scripts.liquidation_portal_health as portal_health_module
from ai_platform.scripts.liquidation_live_health import (
    GitHubIssueClient,
    _alert,
    _workflow_run_url,
    evaluate_health,
    inspect_container,
    reconcile_alert_issue,
)
from ai_platform.scripts.liquidation_portal_health import (
    build_parser,
    evaluate_portal_report,
    normalize_portal_report,
    read_portal_report,
    run_portal_proof,
)


REQUIRED_SOURCES = ("bybit-linear", "binance-usdm", "okx-swap")
DATA_MOUNT_DESTINATION = "/data"
PORTAL_OPERATIONAL_REPORT_TYPE = "liquidations_live_portal_operational_probe"
HOUR_MS = 60 * 60 * 1000

_CONTAINER_OBSERVATION_SCRIPT = r"""
import json
import shutil
from pathlib import Path

root = Path("/data")
pointer_path = root / "live" / "live-state-v1.json"
if not root.is_dir() or root.is_symlink():
    raise SystemExit("collector data root is invalid")
if not pointer_path.is_file() or pointer_path.is_symlink():
    raise SystemExit("collector live-state pointer is invalid")
pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
if not isinstance(pointer, dict):
    raise SystemExit("collector live-state pointer is not an object")
usage = shutil.disk_usage(root)
print(json.dumps({
    "pointer": pointer,
    "disk": {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    },
}, separators=(",", ":"), sort_keys=True))
"""


def inspect_container_data(
    container_name: str,
    expected_data_root: Path,
) -> tuple[dict[str, Any] | None, dict[str, int], str | None]:
    empty_disk = {"total": 0, "used": 0, "free": 0}
    try:
        mounts_result = subprocess.run(
            ["docker", "inspect", "--format", "{{json .Mounts}}", container_name],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        mounts = json.loads(mounts_result.stdout)
        if not isinstance(mounts, list):
            raise ValueError("collector mounts are not a list")
        data_mount = next(
            (
                item
                for item in mounts
                if isinstance(item, dict) and item.get("Destination") == DATA_MOUNT_DESTINATION
            ),
            None,
        )
        if not isinstance(data_mount, dict):
            raise ValueError("collector /data mount is missing")
        if data_mount.get("Type") != "bind":
            raise ValueError("collector /data mount is not a bind mount")
        if data_mount.get("Source") != str(expected_data_root):
            raise ValueError("collector /data mount source does not match the trusted host root")
        if data_mount.get("RW") is not True:
            raise ValueError("collector /data mount is unexpectedly read-only")

        observation_result = subprocess.run(
            ["docker", "exec", "--interactive", container_name, "python", "-"],
            input=_CONTAINER_OBSERVATION_SCRIPT,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        observation = json.loads(observation_result.stdout)
        if not isinstance(observation, dict):
            raise ValueError("collector data observation is not an object")
        pointer = observation.get("pointer")
        disk = observation.get("disk")
        if not isinstance(pointer, dict):
            raise ValueError("collector data observation has no pointer")
        if not isinstance(disk, dict):
            raise ValueError("collector data observation has no disk snapshot")
        parsed_disk = {
            "total": int(disk.get("total", 0)),
            "used": int(disk.get("used", 0)),
            "free": int(disk.get("free", 0)),
        }
        if min(parsed_disk.values()) < 0:
            raise ValueError("collector disk snapshot contains negative values")
        return pointer, parsed_disk, None
    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
        TypeError,
    ) as error:
        return None, empty_disk, f"{type(error).__name__}: {error}"[:500]


def _record(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _integer(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _source_runtime_alerts(
    pointer: dict[str, Any] | None,
    *,
    now_ms: int,
    event_stale_ms: int,
    reconnects_per_hour_max: int,
) -> list[dict[str, str]]:
    state = _record(_record(pointer).get("state"))
    sources = _record(state.get("sources"))
    collector_started_at_ms = _integer(state.get("collector_started_at_ms"))
    uptime_hours = None
    if collector_started_at_ms is not None and now_ms >= collector_started_at_ms:
        uptime_hours = max(1.0, (now_ms - collector_started_at_ms) / HOUR_MS)

    alerts: list[dict[str, str]] = []
    for source in REQUIRED_SOURCES:
        item = _record(sources.get(source))
        events = _integer(item.get("events_written"))
        last_receive = _integer(item.get("last_event_received_at_ms"))
        parse_errors = _integer(item.get("parse_error_count"))
        reconnects = _integer(item.get("reconnect_count"))
        if events is None:
            alerts.append(
                _alert(
                    "LIQUID20_SOURCE_WRITE_STATE_INVALID",
                    f"{source} events_written is invalid.",
                )
            )
        elif (
            events == 0
            and collector_started_at_ms is not None
            and now_ms - collector_started_at_ms > event_stale_ms
        ):
            alerts.append(
                _alert(
                    "LIQUID20_SOURCE_NO_DATA_WRITTEN",
                    f"{source} has written no events.",
                )
            )
        if (
            events is not None
            and events > 0
            and (last_receive is None or now_ms - last_receive > event_stale_ms)
        ):
            alerts.append(
                _alert(
                    "LIQUID20_SOURCE_EVENT_STALE",
                    f"{source} last receive time is stale.",
                )
            )
        if parse_errors is None:
            alerts.append(
                _alert(
                    "LIQUID20_SOURCE_PARSE_STATE_INVALID",
                    f"{source} parse count is invalid.",
                )
            )
        elif parse_errors > 0:
            alerts.append(
                _alert(
                    "LIQUID20_SOURCE_PARSE_ERRORS",
                    f"{source} parse errors={parse_errors}.",
                )
            )
        if reconnects is None:
            alerts.append(
                _alert(
                    "LIQUID20_SOURCE_RECONNECT_STATE_INVALID",
                    f"{source} reconnect count is invalid.",
                )
            )
        elif uptime_hours is not None:
            reconnect_budget = reconnects_per_hour_max * uptime_hours
            if reconnects > reconnect_budget:
                reconnect_rate = reconnects / uptime_hours
                alerts.append(
                    _alert(
                        "LIQUID20_SOURCE_RECONNECTS_UNCONTROLLED",
                        (
                            f"{source} reconnect rate {reconnect_rate:.1f}/h exceeds "
                            f"{reconnects_per_hour_max}/h."
                        ),
                    )
                )
    return alerts


def _runtime_portal_alerts(
    pointer: dict[str, Any] | None,
    portal_report: dict[str, Any] | None,
) -> list[dict[str, str]]:
    runtime_sources = _record(_record(_record(pointer).get("state")).get("sources"))
    portal_health = _record(_record(_record(portal_report).get("observation")).get("health"))
    portal_sources = _record(portal_health.get("sources"))
    alerts: list[dict[str, str]] = []
    for source in REQUIRED_SOURCES:
        runtime = _record(runtime_sources.get(source))
        portal = _record(portal_sources.get(source))
        if not portal:
            alerts.append(
                _alert(
                    "LIQUID20_PORTAL_SOURCE_MISSING",
                    f"Portal omitted {source}.",
                )
            )
            continue
        if runtime.get("configured") != portal.get("configured"):
            alerts.append(
                _alert(
                    "LIQUID20_PORTAL_SOURCE_CONFIG_DRIFT",
                    f"{source} configured state differs.",
                )
            )
        runtime_events = _integer(runtime.get("events_written"))
        portal_events = _integer(portal.get("events"))
        if (
            runtime_events is not None
            and portal_events is not None
            and portal_events > runtime_events
        ):
            alerts.append(
                _alert(
                    "LIQUID20_PORTAL_SOURCE_COUNT_DRIFT",
                    f"{source} portal count exceeds runtime count.",
                )
            )
    return alerts


def _operational_portal_source_results(
    pointer: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    state = _record(_record(pointer).get("state"))
    raw_sources = _record(state.get("sources"))
    results: dict[str, Any] = {}
    healthy = True
    for source in REQUIRED_SOURCES:
        item = _record(raw_sources.get(source))
        source_ok = (
            item.get("configured") is True
            and item.get("connected") is True
            and isinstance(item.get("subscription_symbol_count"), int)
            and item["subscription_symbol_count"] >= 1
            and isinstance(item.get("events_written"), int)
            and item["events_written"] >= 0
        )
        results[source] = {
            "configured": item.get("configured"),
            "connected": item.get("connected"),
            "subscription_symbol_count": item.get("subscription_symbol_count"),
            "events": item.get("events_written"),
            "healthy": source_ok,
        }
        healthy = healthy and source_ok
    return results, healthy


def _evaluate_operational_portal_report(
    report: dict[str, Any] | None,
    *,
    pointer: dict[str, Any] | None,
    now_ms: int,
    proof_exit_code: int | None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    mode = portal_health_module.portal_mode_from_pointer(pointer, now_ms=now_ms)
    source_results, sources_ok = _operational_portal_source_results(pointer)
    if not isinstance(report, dict):
        return (
            {
                "enabled": True,
                "healthy": False,
                "mode": mode,
                "result": None,
                "proof_exit_code": proof_exit_code,
                "production": {},
                "observation": {"sources": source_results},
            },
            [_alert("PORTAL_LIQUIDATIONS_HEALTH_UNAVAILABLE", "Portal report is unavailable.")],
        )

    if report.get("result") != "success" or proof_exit_code != 0:
        reason = str(report.get("rejection_reason") or "Operational portal probe failed.")[:500]
        return (
            {
                "enabled": True,
                "healthy": False,
                "mode": mode,
                "result": report.get("result"),
                "rejection_reason": reason,
                "proof_exit_code": proof_exit_code,
                "commit_sha": report.get("commit_sha"),
                "production": {},
                "observation": {"sources": source_results},
            },
            [_alert("PORTAL_LIQUIDATIONS_PROBE_FAILED", reason)],
        )

    production = _record(report.get("production_portal"))
    boundary = _record(production.get("unauthenticated_boundary"))
    container_ok = production.get("running") is True
    security_ok = (
        isinstance(production.get("uid"), int)
        and production["uid"] != 0
        and production.get("restart_policy") == "always"
        and production.get("real_data_mount_read_only") is True
        and production.get("docker_socket_mounted") is False
    )
    boundary_ok = (
        boundary.get("page_status") == 200
        and boundary.get("health_status") == 401
        and boundary.get("health_code") == "SESSION_MISSING"
        and "no-store" in str(boundary.get("health_cache_control") or "")
    )

    alerts: list[dict[str, str]] = []
    checks = (
        (container_ok, "PORTAL_PRODUCTION_CONTAINER_UNHEALTHY", "Portal container is not running."),
        (security_ok, "PORTAL_PRODUCTION_SECURITY_UNHEALTHY", "Portal runtime security failed."),
        (boundary_ok, "PORTAL_PRODUCTION_BOUNDARY_UNHEALTHY", "Portal boundary failed."),
        (sources_ok, "PORTAL_LIQUIDATIONS_SOURCE_UNHEALTHY", "Collector sources failed."),
    )
    for passed, code, message in checks:
        if not passed:
            alerts.append(_alert(code, message))

    mode_alerts = {
        "stale": ("PORTAL_LIQUIDATIONS_STALE", "Portal input state is STALE."),
        "offline": ("PORTAL_LIQUIDATIONS_OFFLINE", "Portal input state is OFFLINE."),
    }
    if mode in mode_alerts:
        code, message = mode_alerts[mode]
        alerts.append(_alert(code, message))
    elif mode != "live":
        alerts.append(_alert("PORTAL_LIQUIDATIONS_MODE_INVALID", f"Invalid portal mode: {mode!r}."))

    return (
        {
            "enabled": True,
            "healthy": not alerts,
            "mode": mode,
            "result": report.get("result"),
            "rejection_reason": report.get("rejection_reason"),
            "proof_exit_code": proof_exit_code,
            "commit_sha": report.get("commit_sha"),
            "production": {
                "page_status": boundary.get("page_status"),
                "protected_health_status": boundary.get("health_status"),
                "protected_health_code": boundary.get("health_code"),
                "protected_health_cache_control": boundary.get("health_cache_control"),
                "restart_policy": production.get("restart_policy"),
                "uid": production.get("uid"),
                "real_data_mount_read_only": production.get("real_data_mount_read_only"),
                "docker_socket_mounted": production.get("docker_socket_mounted"),
            },
            "observation": {"sources": source_results},
        },
        alerts,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    proof_exit_code = None
    if args.require_portal:
        proof_exit_code = run_portal_proof(
            args.portal_proof_script,
            args.portal_report,
            delay_seconds=args.portal_proof_delay_seconds,
        )

    now_ms = time.time_ns() // 1_000_000
    pointer, disk, observation_error = inspect_container_data(
        args.container_name,
        args.data_root,
    )

    live_health_module.REQUIRED_SOURCES = REQUIRED_SOURCES
    portal_health_module.REQUIRED_SOURCES = REQUIRED_SOURCES

    report = evaluate_health(
        now_ms=now_ms,
        container=inspect_container(args.container_name),
        pointer=pointer,
        disk=disk,
        stale_after_ms=args.stale_after_seconds * 1000,
        source_stale_after_ms=args.source_stale_after_seconds * 1000,
        disk_used_percent_max=args.disk_used_percent_max,
        disk_free_bytes_min=args.disk_free_bytes_min,
    )
    report["checks"]["data_observation"] = {
        "mode": "collector-container-exec",
        "error": observation_error,
        "healthy": observation_error is None,
    }

    raw_portal_report = read_portal_report(args.portal_report)
    operational_probe = (
        isinstance(raw_portal_report, dict)
        and raw_portal_report.get("report_type") == PORTAL_OPERATIONAL_REPORT_TYPE
    )
    if operational_probe:
        portal_report = raw_portal_report
        portal_result, portal_alerts = _evaluate_operational_portal_report(
            portal_report,
            pointer=pointer,
            now_ms=now_ms,
            proof_exit_code=proof_exit_code,
        )
        consistency_alerts: list[dict[str, str]] = []
    else:
        portal_report = normalize_portal_report(
            raw_portal_report,
            pointer=pointer,
            now_ms=now_ms,
            proof_exit_code=proof_exit_code,
        )
        portal_result, portal_alerts = evaluate_portal_report(
            portal_report,
            required=args.require_portal,
        )
        consistency_alerts = (
            _runtime_portal_alerts(pointer, portal_report) if args.require_portal else []
        )

    operational_alerts = _source_runtime_alerts(
        pointer,
        now_ms=now_ms,
        event_stale_ms=(int(os.environ.get("LIQUID20_EVENT_STALE_SECONDS", "300")) * 1000),
        reconnects_per_hour_max=int(os.environ.get("LIQUID20_RECONNECTS_PER_HOUR_MAX", "100")),
    )
    report["schema_version"] = 2
    report["checks"]["portal"] = portal_result
    report["alerts"].extend(portal_alerts + operational_alerts + consistency_alerts)
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
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    return 0 if report["healthy"] is True else 1


if __name__ == "__main__":
    sys.exit(main())
