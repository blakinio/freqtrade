from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_platform.scripts.liquidation_portal_health import (
    evaluate_portal_report,
    normalize_portal_report,
    portal_mode_from_pointer,
)


NOW_MS = 1_800_000_000_000


def healthy_pointer() -> dict[str, Any]:
    source = {
        "configured": True,
        "connected": True,
        "subscription_symbol_count": 100,
        "events_written": 12,
        "last_heartbeat_at_ms": NOW_MS - 5_000,
    }
    state = {
        "contract": "liquidation-live-state-v1",
        "run_id": "liquid20-20260728T000000Z-0",
        "run_state": "active",
        "collector_started_at_ms": NOW_MS - 60_000,
        "collector_heartbeat_at_ms": NOW_MS - 5_000,
        "last_event_at_ms": NOW_MS - 5_000,
        "last_event_received_at_ms": NOW_MS - 4_000,
        "sources": {
            "bybit-linear": dict(source),
            "binance-usdm": dict(source),
        },
    }
    return {"contract": "liquidation-live-state-v1", "state": state}


def successful_proof() -> dict[str, Any]:
    source = {
        "configured": True,
        "connected": True,
        "subscription_symbol_count": 100,
        "events": 12,
    }
    observation = {
        "page_status": 200,
        "cache_control": {
            "health": "private, no-store",
            "list": "private, no-store",
            "summary": "private, no-store",
        },
        "health": {
            "contract": "portal-liquidations-health-v2",
            "mode": "live",
            "run_state": "active",
            "run_id": "liquid20-20260728T000000Z-0",
            "collector_heartbeat_at_ms": NOW_MS - 5_000,
            "portal_checked_at_ms": NOW_MS,
            "last_event_at_ms": NOW_MS - 5_000,
            "last_event_received_at_ms": NOW_MS - 4_000,
            "research_preview": True,
            "trading_authorized": False,
            "sources": {
                "bybit-linear": dict(source),
                "binance-usdm": dict(source),
            },
        },
    }
    return {
        "schema_version": 1,
        "report_type": "liquidations_live_portal_synology_proof",
        "commit_sha": "a" * 40,
        "result": "success",
        "rejection_reason": None,
        "production_portal": {
            "image": "local/freqtrade-portal-web:sha-a",
            "image_id": "sha256:abc",
            "unauthenticated_boundary": {
                "page_status": 200,
                "health_status": 401,
                "health_code": "SESSION_MISSING",
                "health_cache_control": "private, no-store",
            },
        },
        "isolated_candidate": {
            "image": "local/freqtrade-portal-web:sha-a",
            "image_id": "sha256:abc",
            "uid": 1000,
            "restart_policy": "no",
            "fixture_identity": True,
            "fixture_session_validated": True,
            "unauthenticated_api_rejected": True,
            "read_only_root_filesystem": True,
            "tmpfs": {
                "/tmp": "size=64m,mode=1777",  # noqa: S108
                "/app/.next/cache": "size=64m,mode=0755",
            },
            "cap_drop": ["ALL"],
            "no_new_privileges": True,
            "memory_limit_bytes": 805306368,
            "real_data_mount_read_only": True,
            "docker_socket_mounted": False,
            "first": observation,
            "second": observation,
        },
    }


def alert_codes(alerts: list[dict[str, str]]) -> set[str]:
    return {item["code"] for item in alerts}


def test_successful_terminal_proof_normalizes_to_live_monitor_evidence() -> None:
    normalized = normalize_portal_report(
        successful_proof(),
        pointer=healthy_pointer(),
        now_ms=NOW_MS,
        proof_exit_code=0,
    )
    result, alerts = evaluate_portal_report(normalized, required=True)

    assert alerts == []
    assert result["healthy"] is True
    assert result["mode"] == "live"
    assert result["proof_exit_code"] == 0
    assert result["production"]["page_status"] == 200
    assert result["production"]["protected_health_status"] == 401
    assert result["production"]["protected_health_code"] == "SESSION_MISSING"
    assert result["candidate"]["exact_production_image"] is True
    assert result["candidate"]["read_only_root_filesystem"] is True
    assert result["observation"]["sources"]["bybit-linear"]["healthy"] is True
    assert result["observation"]["sources"]["binance-usdm"]["healthy"] is True


def test_pointer_classifies_live_stale_and_offline_transitions() -> None:
    pointer = healthy_pointer()
    assert portal_mode_from_pointer(pointer, now_ms=NOW_MS) == "live"

    pointer["state"]["collector_heartbeat_at_ms"] = NOW_MS - 31_000
    assert portal_mode_from_pointer(pointer, now_ms=NOW_MS) == "stale"

    pointer["state"]["collector_heartbeat_at_ms"] = NOW_MS - 121_000
    assert portal_mode_from_pointer(pointer, now_ms=NOW_MS) == "offline"


def test_failed_proof_preserves_stale_mode_and_fails_closed() -> None:
    pointer = healthy_pointer()
    pointer["state"]["collector_heartbeat_at_ms"] = NOW_MS - 31_000
    failed = {
        "report_type": "liquidations_live_portal_synology_proof",
        "commit_sha": "a" * 40,
        "result": "failure",
        "rejection_reason": "proof failed during candidate_first_authenticated_observation",
    }

    normalized = normalize_portal_report(
        failed,
        pointer=pointer,
        now_ms=NOW_MS,
        proof_exit_code=1,
    )
    result, alerts = evaluate_portal_report(normalized, required=True)
    codes = alert_codes(alerts)

    assert result["healthy"] is False
    assert result["mode"] == "stale"
    assert "PORTAL_LIQUIDATIONS_STALE" in codes
    assert "PORTAL_LIQUIDATIONS_PROBE_FAILED" in codes


def test_missing_portal_report_fails_closed_when_required() -> None:
    result, alerts = evaluate_portal_report(None, required=True)

    assert result["healthy"] is False
    assert alert_codes(alerts) == {"PORTAL_LIQUIDATIONS_HEALTH_UNAVAILABLE"}


def test_existing_proof_script_preserves_security_and_session_boundaries() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    script = (
        repository_root / "deploy" / "synology" / "portal" / "prove-liquidations-live.sh"
    ).read_text(encoding="utf-8")

    assert "set -Eeuo pipefail" in script
    assert 'test "$portal_uid" != "0"' in script
    assert 'test "$candidate_image" = "$portal_image"' in script
    assert 'test "$candidate_image_id" = "$portal_image_id"' in script
    assert "--read-only" in script
    assert "--cap-drop ALL" in script
    assert "--security-opt no-new-privileges:true" in script
    assert "dst=${liquidations_container_root},readonly" in script
    assert 'test -z "$candidate_docker_socket_mount"' in script
    assert "--env PORTAL_IDENTITY_FIXTURE_MODE=enabled" in script
    assert '"SESSION_MISSING"' in script
    assert "/api/market/liquidations/health" in script
    assert "/api/market/liquidations?limit=20" in script
    assert "/api/market/liquidations/summary" in script
    assert 'docker exec --env "PORTAL_FIXTURE_COOKIE=$fixture_cookie"' in script


def test_health_workflow_requires_combined_collector_and_portal_monitoring() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    workflow = (
        repository_root / ".github" / "workflows" / "liquidations-live-health.yml"
    ).read_text(encoding="utf-8")

    assert 'cron: "*/5 * * * *"' in workflow
    assert "Check Synology collector and portal" in workflow
    assert "python -m ai_platform.scripts.liquidation_portal_health" in workflow
    assert "LIQUID20_PORTAL_PROOF_SCRIPT" in workflow
    assert "prove-liquidations-live.sh" in workflow
    assert 'PORTAL_LIVE_PROOF_DELAY_SECONDS: "5"' in workflow
    assert 'LIQUID20_REQUIRE_PORTAL_HEALTH: "true"' in workflow
    assert "liquidations-live-portal-health.json" in workflow
    assert "statuses: write" in workflow
    assert "persist-credentials: false" in workflow
    assert '"context": "liquidations-live-health"' in workflow
