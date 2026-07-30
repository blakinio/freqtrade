from __future__ import annotations

from copy import deepcopy

from ai_platform.scripts.liquidation_operational_health import (
    REQUIRED_SOURCES,
    _runtime_portal_alerts,
    _source_runtime_alerts,
)


NOW_MS = 1_784_956_800_000


def _source(*, events: int = 1) -> dict[str, object]:
    return {
        "configured": True,
        "connected": True,
        "last_event_received_at_ms": NOW_MS - 1_000 if events else None,
        "last_heartbeat_at_ms": NOW_MS - 500,
        "events_written": events,
        "parse_error_count": 0,
        "reconnect_count": 0,
    }


def _pointer() -> dict[str, object]:
    return {
        "state": {
            "collector_started_at_ms": NOW_MS - 60_000,
            "sources": {source: _source() for source in REQUIRED_SOURCES},
        }
    }


def _portal_report() -> dict[str, object]:
    return {
        "observation": {
            "health": {
                "sources": {
                    source: {"configured": True, "connected": True, "events": 1}
                    for source in REQUIRED_SOURCES
                }
            }
        }
    }


def _codes(alerts: list[dict[str, str]]) -> set[str]:
    return {alert["code"] for alert in alerts}


def test_three_source_runtime_and_portal_state_is_healthy() -> None:
    assert _source_runtime_alerts(
        _pointer(),
        now_ms=NOW_MS,
        event_stale_ms=300_000,
        reconnect_max=100,
    ) == []
    assert _runtime_portal_alerts(_pointer(), _portal_report()) == []


def test_okx_parse_reconnect_stale_and_write_alerts_are_source_isolated() -> None:
    pointer = _pointer()
    sources = pointer["state"]["sources"]
    sources["okx-swap"] = {
        **_source(events=1),
        "last_event_received_at_ms": NOW_MS - 301_000,
        "parse_error_count": 1,
        "reconnect_count": 101,
    }

    alerts = _source_runtime_alerts(
        pointer,
        now_ms=NOW_MS,
        event_stale_ms=300_000,
        reconnect_max=100,
    )

    assert _codes(alerts) == {
        "LIQUID20_SOURCE_EVENT_STALE",
        "LIQUID20_SOURCE_PARSE_ERRORS",
        "LIQUID20_SOURCE_RECONNECTS_UNCONTROLLED",
    }
    assert all("okx-swap" in alert["message"] for alert in alerts)

    no_write = deepcopy(pointer)
    no_write["state"]["collector_started_at_ms"] = NOW_MS - 301_000
    no_write["state"]["sources"]["okx-swap"] = _source(events=0)
    alerts = _source_runtime_alerts(
        no_write,
        now_ms=NOW_MS,
        event_stale_ms=300_000,
        reconnect_max=100,
    )
    assert "LIQUID20_SOURCE_NO_DATA_WRITTEN" in _codes(alerts)


def test_portal_runtime_drift_detects_missing_okx_and_impossible_counts() -> None:
    missing = _portal_report()
    del missing["observation"]["health"]["sources"]["okx-swap"]
    assert _codes(_runtime_portal_alerts(_pointer(), missing)) == {
        "LIQUID20_PORTAL_SOURCE_MISSING"
    }

    drift = _portal_report()
    drift["observation"]["health"]["sources"]["okx-swap"]["configured"] = False
    drift["observation"]["health"]["sources"]["okx-swap"]["events"] = 2
    assert _codes(_runtime_portal_alerts(_pointer(), drift)) == {
        "LIQUID20_PORTAL_SOURCE_CONFIG_DRIFT",
        "LIQUID20_PORTAL_SOURCE_COUNT_DRIFT",
    }


def test_invalid_runtime_counters_fail_closed_without_crashing() -> None:
    pointer = _pointer()
    pointer["state"]["collector_started_at_ms"] = "invalid"
    pointer["state"]["sources"]["okx-swap"] = {
        **_source(),
        "events_written": "invalid",
        "parse_error_count": -1,
        "reconnect_count": None,
    }

    alerts = _source_runtime_alerts(
        pointer,
        now_ms=NOW_MS,
        event_stale_ms=300_000,
        reconnect_max=100,
    )
    assert _codes(alerts) == {
        "LIQUID20_SOURCE_WRITE_STATE_INVALID",
        "LIQUID20_SOURCE_PARSE_STATE_INVALID",
        "LIQUID20_SOURCE_RECONNECT_STATE_INVALID",
    }
