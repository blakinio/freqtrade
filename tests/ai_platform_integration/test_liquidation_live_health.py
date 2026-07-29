from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_platform.scripts.liquidation_live_health import (
    ALERT_TITLE,
    evaluate_health,
    reconcile_alert_issue,
)


NOW_MS = 1_800_000_000_000


def healthy_pointer() -> dict[str, Any]:
    source = {
        "configured": True,
        "connected": True,
        "subscription_symbol_count": 100,
        "last_heartbeat_at_ms": NOW_MS - 5_000,
    }
    state = {
        "contract": "liquidation-live-state-v1",
        "run_id": "liquid20-20260728T000000Z-0",
        "run_state": "active",
        "collector_heartbeat_at_ms": NOW_MS - 5_000,
        "execution_enabled": False,
        "trading_authorized": False,
        "trading_credentials_present": False,
        "sources": {
            "bybit-linear": dict(source),
            "binance-usdm": dict(source),
        },
    }
    return {"contract": "liquidation-live-state-v1", "state": state}


def evaluate(pointer: dict[str, Any], *, free: int = 200 * 1024**3) -> dict[str, Any]:
    total = 1_000 * 1024**3
    return evaluate_health(
        now_ms=NOW_MS,
        container={
            "running": True,
            "status": "running",
            "restarting": False,
            "oom_killed": False,
            "exit_code": 0,
            "error": None,
        },
        pointer=pointer,
        disk={"total": total, "used": total - free, "free": free},
        stale_after_ms=60_000,
        source_stale_after_ms=60_000,
        disk_used_percent_max=90.0,
        disk_free_bytes_min=20 * 1024**3,
    )


def alert_codes(report: dict[str, Any]) -> set[str]:
    return {str(item["code"]) for item in report["alerts"]}


def test_healthy_collector_passes_all_checks() -> None:
    report = evaluate(healthy_pointer())

    assert report["healthy"] is True
    assert report["alerts"] == []
    assert report["checks"]["container"]["healthy"] is True
    assert report["checks"]["state"]["healthy"] is True
    assert report["checks"]["sources"]["bybit-linear"]["healthy"] is True
    assert report["checks"]["sources"]["binance-usdm"]["healthy"] is True
    assert report["checks"]["disk"]["healthy"] is True


def test_stale_heartbeat_and_disconnected_source_raise_alerts() -> None:
    pointer = healthy_pointer()
    pointer["state"]["collector_heartbeat_at_ms"] = NOW_MS - 61_000
    pointer["state"]["sources"]["binance-usdm"]["connected"] = False
    pointer["state"]["sources"]["binance-usdm"]["last_heartbeat_at_ms"] = NOW_MS - 61_000

    report = evaluate(pointer)

    assert report["healthy"] is False
    assert "LIQUID20_COLLECTOR_HEARTBEAT_STALE" in alert_codes(report)
    assert "LIQUID20_SOURCE_UNHEALTHY" in alert_codes(report)


def test_disk_capacity_thresholds_raise_both_alerts() -> None:
    report = evaluate(healthy_pointer(), free=10 * 1024**3)

    assert report["healthy"] is False
    assert "LIQUID20_DISK_USAGE_HIGH" in alert_codes(report)
    assert "LIQUID20_DISK_FREE_LOW" in alert_codes(report)


def test_data_only_safety_violation_is_critical() -> None:
    pointer = healthy_pointer()
    pointer["state"]["trading_authorized"] = True

    report = evaluate(pointer)

    assert report["healthy"] is False
    assert "LIQUID20_DATA_ONLY_SAFETY_VIOLATION" in alert_codes(report)


class FakeIssueClient:
    def __init__(self, issues: list[dict[str, Any]] | None = None) -> None:
        self.issues = issues or []
        self.created: list[dict[str, Any]] = []
        self.updated: list[tuple[int, dict[str, Any]]] = []
        self.comments: list[tuple[int, str]] = []

    def list_open_issues(self, repository: str) -> list[dict[str, Any]]:
        assert repository == "blakinio/freqtrade"
        return self.issues

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]:
        payload = {"number": 42, "title": title, "body": body}
        self.created.append(payload)
        return payload

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        update = {"body": body, "state": state}
        self.updated.append((issue_number, update))
        return {"number": issue_number, **update}

    def create_comment(self, repository: str, issue_number: int, *, body: str) -> None:
        self.comments.append((issue_number, body))


def test_github_alert_is_deduplicated_and_closed_after_recovery() -> None:
    unhealthy = evaluate(healthy_pointer(), free=10 * 1024**3)
    client = FakeIssueClient()

    assert (
        reconcile_alert_issue(
            client,
            "blakinio/freqtrade",
            unhealthy,
            run_url="https://example.invalid/run/1",
        )
        == "created"
    )
    assert client.created[0]["title"] == ALERT_TITLE

    existing = FakeIssueClient([{"number": 42, "title": ALERT_TITLE}])
    assert reconcile_alert_issue(existing, "blakinio/freqtrade", unhealthy) == "updated"
    assert existing.updated[0][0] == 42
    assert existing.updated[0][1]["body"] is not None

    recovered = evaluate(healthy_pointer())
    assert reconcile_alert_issue(existing, "blakinio/freqtrade", recovered) == "closed"
    assert existing.comments
    assert existing.updated[-1] == (42, {"body": None, "state": "closed"})


def test_health_workflow_is_scheduled_deduplicated_and_alert_capable() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    workflows_root = repository_root / ".github" / "workflows"
    workflow = (workflows_root / "liquidations-live-operational-health.yml").read_text(
        encoding="utf-8"
    )

    assert not (workflows_root / "liquidations-live-health.yml").exists()
    assert 'cron: "*/5 * * * *"' in workflow
    assert "runs-on: freqtrade-staging" in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "actions: read" in workflow
    assert "issues: write" in workflow
    assert "statuses: write" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "persist-credentials: false" in workflow
    assert "LIQUID20_HEARTBEAT_STALE_SECONDS" in workflow
    assert "LIQUID20_SOURCE_STALE_SECONDS" in workflow
    assert "LIQUID20_DISK_USED_PERCENT_MAX" in workflow
    assert "LIQUID20_DISK_FREE_BYTES_MIN" in workflow
    assert "steps.health.outcome != 'success'" in workflow
    assert "retention-days: 14" in workflow
    assert "Publish pending health status" in workflow
    assert "Publish final health status" in workflow
    assert '"context": "liquidations-live-health"' in workflow
    assert "runner_watchdog:" in workflow
    assert "actions/runs/$GITHUB_RUN_ID/jobs" in workflow
    assert "LIQUIDATIONS_HEALTH_RUNNER_UNAVAILABLE" in workflow
    assert "did not start within 120 seconds" in workflow
