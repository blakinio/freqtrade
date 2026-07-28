from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.scripts.liquidation_live_health import (
    GitHubIssueClient,
    _alert,
    _workflow_run_url,
    build_parser as build_collector_parser,
    disk_snapshot,
    evaluate_health,
    inspect_container,
    read_live_pointer,
    reconcile_alert_issue,
)

MAX_PORTAL_REPORT_BYTES = 2 * 1024 * 1024
REQUIRED_SOURCES = ("bybit-linear", "binance-usdm")
COLLECTOR_STALE_MS = 30_000
COLLECTOR_OFFLINE_MS = 120_000
EVENT_STALE_MS = 300_000
SOURCE_STALE_MS = 45_000


def _record(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def read_portal_report(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        if not path.is_file() or path.is_symlink():
            return None
        if path.stat().st_size > MAX_PORTAL_REPORT_BYTES:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def run_portal_proof(
    script: Path | None,
    report_path: Path | None,
    *,
    delay_seconds: int,
) -> int | None:
    if script is None or report_path is None:
        return None
    if not script.is_file() or script.is_symlink() or not 5 <= delay_seconds <= 120:
        return None
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.unlink(missing_ok=True)
    environment = os.environ.copy()
    environment["PORTAL_LIVE_PROOF_REPORT_PATH"] = str(report_path)
    environment["PORTAL_LIVE_PROOF_DELAY_SECONDS"] = str(delay_seconds)
    try:
        result = subprocess.run(
            ["bash", str(script)],
            check=False,
            env=environment,
            timeout=240,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.returncode


def portal_mode_from_pointer(pointer: dict[str, Any] | None, *, now_ms: int) -> str | None:
    root = _record(pointer)
    state = _record(root.get("state"))
    if (
        root.get("contract") != "liquidation-live-state-v1"
        or state.get("contract") != "liquidation-live-state-v1"
    ):
        return None
    if state.get("run_state") == "completed":
        return "offline"
    if state.get("run_state") != "active":
        return None
    heartbeat = _integer(state.get("collector_heartbeat_at_ms"))
    if heartbeat is None:
        return None
    age = max(0, now_ms - heartbeat)
    if age > COLLECTOR_OFFLINE_MS:
        return "offline"
    if age > COLLECTOR_STALE_MS:
        return "stale"
    event_reference = _integer(state.get("last_event_received_at_ms"))
    if event_reference is None:
        event_reference = _integer(state.get("collector_started_at_ms"))
    if event_reference is None:
        return None
    if max(0, now_ms - event_reference) > EVENT_STALE_MS:
        return "stale"
    sources = _record(state.get("sources"))
    for source in REQUIRED_SOURCES:
        item = _record(sources.get(source))
        source_heartbeat = _integer(item.get("last_heartbeat_at_ms"))
        if (
            item.get("configured") is not True
            or item.get("connected") is not True
            or source_heartbeat is None
            or now_ms - source_heartbeat > SOURCE_STALE_MS
        ):
            return "stale"
    return "live"


def _fallback_health(
    pointer: dict[str, Any] | None,
    *,
    mode: str | None,
    now_ms: int,
) -> dict[str, Any]:
    state = _record(_record(pointer).get("state"))
    raw_sources = _record(state.get("sources"))
    sources: dict[str, Any] = {}
    for source in REQUIRED_SOURCES:
        item = _record(raw_sources.get(source))
        heartbeat = _integer(item.get("last_heartbeat_at_ms"))
        sources[source] = {
            "configured": item.get("configured"),
            "connected": (
                item.get("configured") is True
                and item.get("connected") is True
                and heartbeat is not None
                and now_ms - heartbeat <= SOURCE_STALE_MS
            ),
            "subscription_symbol_count": item.get("subscription_symbol_count"),
            "events": item.get("events_written"),
        }
    return {
        "contract": "portal-liquidations-health-v2",
        "mode": mode,
        "run_state": state.get("run_state"),
        "run_id": state.get("run_id"),
        "collector_heartbeat_at_ms": state.get("collector_heartbeat_at_ms"),
        "portal_checked_at_ms": now_ms,
        "last_event_at_ms": state.get("last_event_at_ms"),
        "last_event_received_at_ms": state.get("last_event_received_at_ms"),
        "research_preview": True,
        "trading_authorized": False,
        "sources": sources,
    }


def normalize_portal_report(
    report: dict[str, Any] | None,
    *,
    pointer: dict[str, Any] | None,
    now_ms: int,
    proof_exit_code: int | None,
) -> dict[str, Any] | None:
    if not isinstance(report, dict):
        return None
    if report.get("report_type") != "liquidations_live_portal_synology_proof":
        return report
    production = _record(report.get("production_portal"))
    candidate = _record(report.get("isolated_candidate"))
    second = _record(candidate.get("second"))
    rejected = candidate.get("unauthenticated_api_rejected") is True
    if report.get("result") == "success" and second:
        observation = {
            "page_status": second.get("page_status"),
            "unauthenticated_boundary": {
                "health_status": 401 if rejected else None,
                "health_code": "SESSION_MISSING" if rejected else None,
            },
            "api_status": {"health": 200, "list": 200, "summary": 200},
            "cache_control": second.get("cache_control"),
            "health": second.get("health"),
        }
    else:
        mode = portal_mode_from_pointer(pointer, now_ms=now_ms)
        observation = {
            "page_status": _record(production.get("unauthenticated_boundary")).get(
                "page_status"
            ),
            "unauthenticated_boundary": {},
            "api_status": {},
            "cache_control": {},
            "health": _fallback_health(pointer, mode=mode, now_ms=now_ms),
        }
    return {
        "schema_version": 1,
        "report_type": "liquidations_live_portal_health",
        "commit_sha": report.get("commit_sha"),
        "result": report.get("result"),
        "rejection_reason": report.get("rejection_reason"),
        "proof_exit_code": proof_exit_code,
        "production_portal": production,
        "isolated_candidate": candidate,
        "observation": observation,
    }


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
            [_alert("PORTAL_LIQUIDATIONS_HEALTH_UNAVAILABLE", "Portal report is unavailable.")],
        )

    production = _record(report.get("production_portal"))
    boundary = _record(production.get("unauthenticated_boundary"))
    candidate = _record(report.get("isolated_candidate"))
    observation = _record(report.get("observation"))
    candidate_boundary = _record(observation.get("unauthenticated_boundary"))
    api_status = _record(observation.get("api_status"))
    cache_control = _record(observation.get("cache_control"))
    health = _record(observation.get("health"))
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
    contract_ok = (
        health.get("contract") == "portal-liquidations-health-v2"
        and health.get("run_state") in {"active", "completed"}
        and isinstance(health.get("collector_heartbeat_at_ms"), int)
        and isinstance(health.get("portal_checked_at_ms"), int)
        and health.get("research_preview") is True
        and health.get("trading_authorized") is False
    )

    source_results: dict[str, Any] = {}
    sources_ok = True
    for source in REQUIRED_SOURCES:
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
    checks = (
        (boundary_ok, "PORTAL_PRODUCTION_BOUNDARY_UNHEALTHY", "Production boundary failed."),
        (
            candidate_boundary_ok,
            "PORTAL_CANDIDATE_AUTH_BOUNDARY_UNHEALTHY",
            "Candidate authentication boundary failed.",
        ),
        (exact_image, "PORTAL_CANDIDATE_IMAGE_MISMATCH", "Candidate image mismatch."),
        (runtime_ok, "PORTAL_CANDIDATE_SECURITY_UNHEALTHY", "Candidate security failed."),
        (api_ok, "PORTAL_LIQUIDATIONS_API_UNHEALTHY", "Portal API/page check failed."),
        (contract_ok, "PORTAL_LIQUIDATIONS_CONTRACT_INVALID", "Portal contract failed."),
        (sources_ok, "PORTAL_LIQUIDATIONS_SOURCE_UNHEALTHY", "Portal sources failed."),
    )
    for passed, code, message in checks:
        if not passed:
            alerts.append(_alert(code, message))

    mode_alerts = {
        "stale": ("PORTAL_LIQUIDATIONS_STALE", "Portal reports STALE."),
        "offline": ("PORTAL_LIQUIDATIONS_OFFLINE", "Portal reports OFFLINE."),
        "historical": (
            "PORTAL_LIQUIDATIONS_HISTORICAL",
            "Portal fell back to HISTORICAL.",
        ),
    }
    if mode in mode_alerts:
        code, message = mode_alerts[mode]
        alerts.append(_alert(code, message))
    elif mode != "live":
        alerts.append(
            _alert("PORTAL_LIQUIDATIONS_MODE_INVALID", f"Invalid portal mode: {mode!r}.")
        )
    if report.get("result") != "success":
        reason = str(report.get("rejection_reason") or "Portal proof failed.")[:500]
        alerts.append(_alert("PORTAL_LIQUIDATIONS_PROBE_FAILED", reason))

    return (
        {
            "enabled": True,
            "healthy": not alerts,
            "mode": mode,
            "result": report.get("result"),
            "rejection_reason": report.get("rejection_reason"),
            "proof_exit_code": report.get("proof_exit_code"),
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
        "--portal-proof-script",
        type=Path,
        default=(
            Path(os.environ["LIQUID20_PORTAL_PROOF_SCRIPT"])
            if os.environ.get("LIQUID20_PORTAL_PROOF_SCRIPT")
            else None
        ),
    )
    parser.add_argument(
        "--portal-proof-delay-seconds",
        type=int,
        default=int(os.environ.get("PORTAL_LIVE_PROOF_DELAY_SECONDS", "5")),
    )
    parser.add_argument(
        "--require-portal",
        action="store_true",
        default=os.environ.get("LIQUID20_REQUIRE_PORTAL_HEALTH", "").lower() == "true",
    )
    return parser


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
    pointer = read_live_pointer(args.data_root)
    report = evaluate_health(
        now_ms=now_ms,
        container=inspect_container(args.container_name),
        pointer=pointer,
        disk=disk_snapshot(args.data_root),
        stale_after_ms=args.stale_after_seconds * 1000,
        source_stale_after_ms=args.source_stale_after_seconds * 1000,
        disk_used_percent_max=args.disk_used_percent_max,
        disk_free_bytes_min=args.disk_free_bytes_min,
    )
    portal_report = normalize_portal_report(
        read_portal_report(args.portal_report),
        pointer=pointer,
        now_ms=now_ms,
        proof_exit_code=proof_exit_code,
    )
    portal_result, portal_alerts = evaluate_portal_report(
        portal_report,
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
