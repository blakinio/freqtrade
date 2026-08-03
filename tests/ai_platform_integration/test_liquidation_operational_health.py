from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ai_platform.scripts.liquidation_operational_health import (
    HOUR_MS,
    _evaluate_operational_portal_report,
    _source_runtime_alerts,
    inspect_container_data,
)


DATA_ROOT = Path("/volume1/docker/freqtrade-liquidations/data")
NOW_MS = 1_800_000_000_000


def healthy_pointer(*, reconnects: int = 0, uptime_hours: int = 20) -> dict[str, Any]:
    source = {
        "configured": True,
        "connected": True,
        "subscription_symbol_count": 100,
        "events_written": 12,
        "last_event_received_at_ms": NOW_MS - 4_000,
        "last_heartbeat_at_ms": NOW_MS - 5_000,
        "parse_error_count": 0,
        "reconnect_count": 0,
    }
    okx = dict(source)
    okx["reconnect_count"] = reconnects
    state = {
        "contract": "liquidation-live-state-v1",
        "run_id": "liquid20-20260803T000000Z-0",
        "run_state": "active",
        "collector_started_at_ms": NOW_MS - uptime_hours * HOUR_MS,
        "collector_heartbeat_at_ms": NOW_MS - 5_000,
        "last_event_at_ms": NOW_MS - 5_000,
        "last_event_received_at_ms": NOW_MS - 4_000,
        "sources": {
            "bybit-linear": dict(source),
            "binance-usdm": dict(source),
            "okx-swap": okx,
        },
    }
    return {"contract": "liquidation-live-state-v1", "state": state}


def operational_portal_report(*, result: str = "success") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "report_type": "liquidations_live_portal_operational_probe",
        "commit_sha": "a" * 40,
        "result": result,
        "rejection_reason": (
            None if result == "success" else "operational probe failed during boundary"
        ),
        "production_portal": {
            "running": True,
            "uid": 1000,
            "restart_policy": "always",
            "real_data_mount_read_only": True,
            "docker_socket_mounted": False,
            "unauthenticated_boundary": {
                "page_status": 200,
                "health_status": 401,
                "health_code": "SESSION_MISSING",
                "health_cache_control": "private, no-store",
            },
        },
    }


def alert_codes(alerts: list[dict[str, str]]) -> set[str]:
    return {item["code"] for item in alerts}


def test_container_observation_uses_validated_production_data_mount(monkeypatch) -> None:
    pointer = {
        "contract": "liquidation-live-state-v1",
        "state": {"contract": "liquidation-live-state-v1", "run_state": "active"},
    }
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:2] == ["docker", "inspect"]:
            mounts = [
                {
                    "Type": "bind",
                    "Source": str(DATA_ROOT),
                    "Destination": "/data",
                    "RW": True,
                }
            ]
            return subprocess.CompletedProcess(command, 0, json.dumps(mounts), "")
        payload = {
            "pointer": pointer,
            "disk": {"total": 1_000, "used": 400, "free": 600},
        }
        assert command == ["docker", "exec", "--interactive", "liquid20-live", "python", "-"]
        assert 'Path("/data")' in kwargs["input"]
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    observed_pointer, disk, error = inspect_container_data("liquid20-live", DATA_ROOT)

    assert error is None
    assert observed_pointer == pointer
    assert disk == {"total": 1_000, "used": 400, "free": 600}
    assert len(calls) == 2


def test_container_observation_fails_closed_on_untrusted_mount(monkeypatch) -> None:
    mounts = [
        {
            "Type": "bind",
            "Source": "/volume1/docker/other-data",
            "Destination": "/data",
            "RW": True,
        }
    ]

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, json.dumps(mounts), "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    pointer, disk, error = inspect_container_data("liquid20-live", DATA_ROOT)

    assert pointer is None
    assert disk == {"total": 0, "used": 0, "free": 0}
    assert error is not None
    assert "trusted host root" in error


def test_reconnect_budget_is_normalized_by_collector_uptime() -> None:
    alerts = _source_runtime_alerts(
        healthy_pointer(reconnects=445, uptime_hours=20),
        now_ms=NOW_MS,
        event_stale_ms=300_000,
        reconnect_max=100,
    )

    assert "LIQUID20_SOURCE_RECONNECTS_UNCONTROLLED" not in alert_codes(alerts)


def test_reconnect_burst_still_fails_closed() -> None:
    alerts = _source_runtime_alerts(
        healthy_pointer(reconnects=150, uptime_hours=1),
        now_ms=NOW_MS,
        event_stale_ms=300_000,
        reconnect_max=100,
    )

    assert "LIQUID20_SOURCE_RECONNECTS_UNCONTROLLED" in alert_codes(alerts)


def test_operational_portal_probe_proves_live_boundary_and_all_sources() -> None:
    result, alerts = _evaluate_operational_portal_report(
        operational_portal_report(),
        pointer=healthy_pointer(),
        now_ms=NOW_MS,
        proof_exit_code=0,
    )

    assert alerts == []
    assert result["healthy"] is True
    assert result["mode"] == "live"
    assert result["production"]["restart_policy"] == "always"
    assert result["production"]["protected_health_status"] == 401
    assert result["production"]["protected_health_code"] == "SESSION_MISSING"
    assert set(result["observation"]["sources"]) == {
        "bybit-linear",
        "binance-usdm",
        "okx-swap",
    }
    assert all(source["healthy"] for source in result["observation"]["sources"].values())


def test_operational_portal_probe_failure_preserves_specific_diagnosis() -> None:
    result, alerts = _evaluate_operational_portal_report(
        operational_portal_report(result="failure"),
        pointer=healthy_pointer(),
        now_ms=NOW_MS,
        proof_exit_code=124,
    )

    assert result["healthy"] is False
    assert alert_codes(alerts) == {"PORTAL_LIQUIDATIONS_PROBE_FAILED"}
    assert result["rejection_reason"] == "operational probe failed during boundary"


def test_operational_probe_is_bounded_and_does_not_launch_candidate() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    script = (
        repository_root
        / "deploy"
        / "synology"
        / "portal"
        / "probe-liquidations-live-operational.sh"
    ).read_text(encoding="utf-8")

    assert "set -Eeuo pipefail" in script
    assert "AbortSignal.timeout" in script
    assert "command -v timeout" in script
    assert "docker_bounded" in script
    assert 'test "$portal_restart" = "always"' in script
    assert 'test "$portal_uid" != "0"' in script
    assert 'test -z "$docker_socket_mount"' in script
    assert "liquidations_live_portal_operational_probe" in script
    assert "docker run" not in script


def test_repair_workflow_restarts_unresponsive_portal_once() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    workflow = (
        repository_root / ".github" / "workflows" / "repair-synology-autostart.yml"
    ).read_text(encoding="utf-8")

    assert "probe-liquidations-live-operational.sh" in workflow
    assert "docker restart --time 20 freqtrade-portal-staging" in workflow
    assert "Portal remained unhealthy after one bounded restart" in workflow
    assert "persist-credentials: false" in workflow
