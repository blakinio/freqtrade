from __future__ import annotations

from typing import Any

from ai_platform.scripts.liquidation_alert_watchdog import reconcile_schedule


NOW_MS = 1_800_000_000_000
STALE_CREATED_AT = "2027-01-15T06:00:00Z"
FRESH_CREATED_AT = "2027-01-15T08:00:00Z"


class FakeClient:
    def __init__(
        self,
        *,
        issue: dict[str, Any] | None = None,
        run: dict[str, Any] | None = None,
    ) -> None:
        self.issue = issue
        self.run = run or {
            "status": "completed",
            "conclusion": "success",
            "created_at": STALE_CREATED_AT,
            "head_sha": "a" * 40,
            "html_url": "https://github.com/blakinio/freqtrade/actions/runs/1",
        }
        self.updated: list[tuple[int, str | None]] = []

    def list_issues(self, repository: str, *, state: str = "all") -> list[dict[str, Any]]:
        return [self.issue] if self.issue is not None else []

    def list_workflow_runs(self, repository: str, workflow: str) -> list[dict[str, Any]]:
        return [self.run]

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        self.updated.append((issue_number, state))
        if self.issue is not None and state is not None:
            self.issue["state"] = state
        return {"number": issue_number, "body": body, "state": state}


def stale_issue() -> dict[str, Any]:
    return {
        "number": 1198,
        "title": "[liquidations-live] operational health alert",
        "state": "open",
        "body": """<!-- liquidations-live-operational-health -->
## Liquidations Live monitoring failure

- Code: `LIQUIDATIONS_HEALTH_MONITOR_STALE`
- Workflow run: https://github.com/blakinio/freqtrade/actions/runs/1

Brak prawidłowego uruchomienia monitoringu przez ponad 60 minut.
""",
    }


def real_issue() -> dict[str, Any]:
    return {
        "number": 1200,
        "title": "[liquidations-live] operational health alert",
        "state": "open",
        "body": """<!-- liquidations-live-operational-health -->
```json
{
  "alerts": [{"code": "LIQUID20_CONTAINER_UNHEALTHY"}],
  "checks": {"container": {"healthy": false}}
}
```
""",
    }


def test_stale_successful_schedule_dispatches_fresh_health_probe() -> None:
    client = FakeClient()
    dispatched: list[bool] = []

    decision = reconcile_schedule(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        dispatch=lambda: dispatched.append(True),
    )

    assert decision.action == "dispatched"
    assert dispatched == [True]
    assert client.updated == []


def test_existing_stale_issue_is_not_reminded_before_self_heal_probe() -> None:
    client = FakeClient(issue=stale_issue())
    dispatched: list[bool] = []

    decision = reconcile_schedule(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        dispatch=lambda: dispatched.append(True),
    )

    assert decision.action == "dispatched"
    assert decision.issue_number == 1198
    assert dispatched == [True]
    assert client.updated == []


def test_fresh_in_progress_probe_suppresses_stale_issue_reminder() -> None:
    client = FakeClient(
        issue=stale_issue(),
        run={
            "status": "in_progress",
            "conclusion": None,
            "created_at": FRESH_CREATED_AT,
            "head_sha": "b" * 40,
            "html_url": "https://github.com/blakinio/freqtrade/actions/runs/2",
        },
    )
    dispatched: list[bool] = []

    decision = reconcile_schedule(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        dispatch=lambda: dispatched.append(True),
    )

    assert decision.action == "waiting"
    assert dispatched == []
    assert client.updated == []


def test_fresh_success_closes_synthetic_stale_issue_for_recovery_delivery() -> None:
    client = FakeClient(
        issue=stale_issue(),
        run={
            "status": "completed",
            "conclusion": "success",
            "created_at": FRESH_CREATED_AT,
            "head_sha": "c" * 40,
            "html_url": "https://github.com/blakinio/freqtrade/actions/runs/3",
        },
    )

    decision = reconcile_schedule(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        dispatch=lambda: None,
    )

    assert decision.action == "recovered"
    assert decision.issue_number == 1198
    assert client.updated == [(1198, "closed")]


def test_real_operational_incident_remains_authoritative_when_schedule_is_stale() -> None:
    client = FakeClient(issue=real_issue())
    dispatched: list[bool] = []

    decision = reconcile_schedule(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        dispatch=lambda: dispatched.append(True),
    )

    assert decision.action == "continue"
    assert dispatched == []
    assert client.updated == []
