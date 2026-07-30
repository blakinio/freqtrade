from __future__ import annotations

from typing import Any

from ai_platform.scripts.liquidation_alert_notifications import (
    Incident,
    REMINDER_MS,
    decide_notification,
    render_failure_message,
    render_recovery_message,
    run,
)

NOW_MS = 1_800_000_000_000


def incident(*, healthy: bool = False, codes: tuple[str, ...] = ("PORTAL_LIQUIDATIONS_API_UNHEALTHY",)) -> Incident:
    return Incident(
        healthy=healthy,
        codes=codes,
        description="Portal API/page check failed.",
        components={
            "Portal": "niedostępny",
            "Kolektor": "zdrowy",
            "Binance": "połączony",
            "Bybit": "połączony",
            "Dysk": "w normie",
            "Runner Synology": "online",
        },
        commit_sha="a" * 40,
        run_url="https://github.com/blakinio/freqtrade/actions/runs/1",
        issue_number=751,
        issue_closed=healthy,
    )


def test_first_failure_update_reminder_and_deduplication() -> None:
    first = decide_notification(None, incident(), now_ms=NOW_MS)
    assert first.action == "alert"

    unchanged = decide_notification(first.state, incident(), now_ms=NOW_MS + 5 * 60_000)
    assert unchanged.action == "none"

    reminder = decide_notification(first.state, incident(), now_ms=NOW_MS + REMINDER_MS)
    assert reminder.action == "reminder"

    changed = decide_notification(
        first.state,
        incident(codes=("LIQUIDATIONS_HEALTH_RUNNER_UNAVAILABLE",)),
        now_ms=NOW_MS + 10_000,
    )
    assert changed.action == "update"


def test_recovery_is_immediate_and_mentions_automatic_issue_close() -> None:
    failed = decide_notification(None, incident(), now_ms=NOW_MS)
    recovered_incident = incident(healthy=True, codes=())
    recovered = decide_notification(failed.state, recovered_incident, now_ms=NOW_MS + 30_000)

    assert recovered.action == "recovery"
    message = render_recovery_message(recovered_incident, recovered, now_ms=NOW_MS + 30_000)
    assert "✅ Liquidations Live — PRZYWRÓCONO" in message
    assert "automatycznie zamknięte" in message
    assert "30 s" in message


def test_failure_payload_contains_required_polish_fields() -> None:
    decision = decide_notification(None, incident(), now_ms=NOW_MS)
    message = render_failure_message(incident(), decision, now_ms=NOW_MS)

    assert "🚨 Liquidations Live — AWARIA" in message
    assert "Środowisko: produkcyjne" in message
    assert "Europe/Warsaw" in message
    assert "Kod: PORTAL_LIQUIDATIONS_API_UNHEALTHY" in message
    assert "Portal: niedostępny" in message
    assert "Kolektor: zdrowy" in message
    assert "Binance: połączony" in message
    assert "Bybit: połączony" in message
    assert "Runner Synology: online" in message
    assert "Commit:" in message
    assert "GitHub run:" in message
    assert "Issue: #751" in message
    assert "Pierwsza czynność:" in message


class FakeClient:
    def __init__(self) -> None:
        self.issues = [
            {
                "number": 751,
                "title": "[liquidations-live] operational health alert",
                "state": "open",
                "body": """<!-- liquidations-live-operational-health -->
```json
{"alerts":[{"code":"LIQUID20_CONTAINER_UNHEALTHY","message":"collector stopped"}],"checks":{"container":{"healthy":false},"state":{"healthy":false},"sources":{},"disk":{"healthy":true},"portal":{"healthy":true,"commit_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}}
```""",
            }
        ]
        self.comments: list[dict[str, Any]] = []
        self.created_issues: list[dict[str, Any]] = []
        self.updated_issues: list[tuple[int, dict[str, Any]]] = []
        self.statuses: list[dict[str, Any]] = []

    def list_issues(self, repository: str, *, state: str = "all") -> list[dict[str, Any]]:
        return [*self.issues, *self.created_issues]

    def get_issue(self, repository: str, issue_number: int) -> dict[str, Any]:
        return next(item for item in self.issues if item["number"] == issue_number)

    def create_issue(self, repository: str, *, title: str, body: str) -> dict[str, Any]:
        issue = {"number": 900 + len(self.created_issues), "title": title, "body": body, "state": "open"}
        self.created_issues.append(issue)
        return issue

    def update_issue(self, repository: str, issue_number: int, *, body: str | None = None, state: str | None = None) -> dict[str, Any]:
        self.updated_issues.append((issue_number, {"body": body, "state": state}))
        return {"number": issue_number, "body": body, "state": state}

    def list_comments(self, repository: str, issue_number: int) -> list[dict[str, Any]]:
        return self.comments

    def create_comment(self, repository: str, issue_number: int, *, body: str) -> dict[str, Any]:
        comment = {"id": len(self.comments) + 1, "body": body}
        self.comments.append(comment)
        return comment

    def update_comment(self, repository: str, comment_id: int, *, body: str) -> dict[str, Any]:
        for comment in self.comments:
            if comment["id"] == comment_id:
                comment["body"] = body
                return comment
        raise AssertionError("comment not found")

    def list_workflow_runs(self, repository: str, workflow: str) -> list[dict[str, Any]]:
        return [{
            "status": "completed",
            "conclusion": "failure",
            "created_at": "2027-01-15T08:00:00Z",
            "head_sha": "a" * 40,
            "html_url": "https://github.com/blakinio/freqtrade/actions/runs/1",
        }]

    def combined_status(self, repository: str, sha: str) -> dict[str, Any]:
        return {"statuses": [{"context": "liquidations-live-health", "state": "failure"}]}

    def create_status(self, repository: str, sha: str, *, state: str, context: str, description: str, target_url: str | None) -> None:
        self.statuses.append({"sha": sha, "state": state, "context": context})


def test_runner_unavailable_and_collector_unhealthy_are_supported() -> None:
    for code in ("LIQUIDATIONS_HEALTH_RUNNER_UNAVAILABLE", "LIQUID20_CONTAINER_UNHEALTHY"):
        result = decide_notification(None, incident(codes=(code,)), now_ms=NOW_MS)
        assert result.action == "alert"
        assert code in render_failure_message(incident(codes=(code,)), result, now_ms=NOW_MS)


def test_delivery_failure_creates_separate_issue_and_red_status(monkeypatch: Any) -> None:
    client = FakeClient()
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_RUN_ID", "1")

    def failing_sender(token: str, chat_id: str, text: str) -> None:
        raise RuntimeError("Telegram API request failed with HTTP 500")

    result = run(
        client=client,
        repository="blakinio/freqtrade",
        token="secret-token",
        chat_id="secret-chat",
        mode="auto",
        issue_number=751,
        now_ms=NOW_MS,
        sender=failing_sender,
    )

    assert result == 1
    assert any(item["title"] == "[liquidations-live] Telegram delivery failure" for item in client.created_issues)
    assert client.statuses[-1]["state"] == "failure"
    assert client.statuses[-1]["context"] == "liquidations-live-notification"
    assert "secret-token" not in client.created_issues[-1]["body"]
    assert "secret-chat" not in client.created_issues[-1]["body"]


def test_bootstrap_sends_test_failure_and_recovery_without_production_issue(monkeypatch: Any) -> None:
    client = FakeClient()
    delivered: list[str] = []
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_RUN_ID", "1")

    result = run(
        client=client,
        repository="blakinio/freqtrade",
        token="token",
        chat_id="chat",
        mode="bootstrap",
        issue_number=None,
        now_ms=NOW_MS,
        sender=lambda token, chat, text: delivered.append(text),
    )

    assert result == 0
    assert len(delivered) == 3
    assert delivered[0].startswith("🧪 TEST")
    assert "AWARIA KONTROLOWANA" in delivered[1]
    assert "PRZYWRÓCONO" in delivered[2]
    assert not any(item["title"] == "[liquidations-live] operational health alert" for item in client.created_issues)


def test_notification_workflow_is_github_hosted_secret_backed_and_watchdog_enabled() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github" / "workflows" / "liquidations-live-telegram-notifications.yml").read_text(encoding="utf-8")

    assert 'cron: "*/5 * * * *"' in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "issues:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "actions: read" in workflow
    assert "issues: write" in workflow
    assert "statuses: write" in workflow
    assert "LIQUIDATIONS_ALERT_TELEGRAM_BOT_TOKEN" in workflow
    assert "LIQUIDATIONS_ALERT_TELEGRAM_CHAT_ID" in workflow
    assert "--mode bootstrap" in workflow
    assert "controlled_failure" in workflow
    assert "controlled_recovery" in workflow
    assert "persist-credentials: false" in workflow


def test_portal_restart_contract_is_persistent_without_weakened_security() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    proof = (root / "deploy" / "synology" / "portal" / "prove-liquidations-live.sh").read_text(encoding="utf-8")
    deployment = (root / "deploy" / "synology" / "portal" / "deploy-preview.sh").read_text(encoding="utf-8")
    repair = (root / ".github" / "workflows" / "repair-synology-autostart.yml").read_text(encoding="utf-8")

    assert 'test "$portal_restart" = "always"' in proof
    assert 'test "$portal_restart" = "unless-stopped"' not in proof
    assert '"$container_name" "$image" "$bind_address" "$portal_port" always' in deployment
    assert "unless-stopped" not in deployment
    assert "workflow_run:" not in repair
    assert "--read-only" in proof
    assert "--cap-drop ALL" in proof
    assert "--security-opt no-new-privileges:true" in proof
    assert "dst=${liquidations_container_root},readonly" in proof
    assert 'test -z "$candidate_docker_socket_mount"' in proof
