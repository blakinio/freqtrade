from __future__ import annotations

from typing import Any

from ai_platform.scripts.liquidation_alert_watchdog import reconcile_schedule


NOW_MS = 1_800_000_000_000


class FakeClient:
    def __init__(self) -> None:
        self.issue = {
            "number": 1201,
            "title": "[liquidations-live] operational health alert",
            "state": "open",
            "body": """## Liquidations Live operational health failure

- Code: `LIQUIDATIONS_HEALTH_RUNNER_UNAVAILABLE`
- Runner label: `freqtrade-staging`
- Observed health job status: `queued`
""",
        }
        self.updated: list[tuple[int, str | None]] = []

    def list_issues(self, repository: str, *, state: str = "all") -> list[dict[str, Any]]:
        return [self.issue]

    def list_workflow_runs(self, repository: str, workflow: str) -> list[dict[str, Any]]:
        return [
            {
                "status": "completed",
                "conclusion": "success",
                "created_at": "2027-01-15T06:00:00Z",
                "head_sha": "a" * 40,
                "html_url": "https://github.com/blakinio/freqtrade/actions/runs/1",
            }
        ]

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        *,
        body: str | None = None,
        state: str | None = None,
    ) -> dict[str, Any]:
        self.updated.append((issue_number, state))
        return {"number": issue_number, "body": body, "state": state}


def test_non_json_runner_incident_remains_authoritative_when_schedule_is_stale() -> None:
    client = FakeClient()
    dispatched: list[bool] = []

    decision = reconcile_schedule(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        dispatch=lambda: dispatched.append(True),
    )

    assert decision.action == "continue"
    assert decision.issue_number == 1201
    assert dispatched == []
    assert client.updated == []
