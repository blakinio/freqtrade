from __future__ import annotations

from pathlib import Path


SCRIPT = Path("ai_platform/scripts/liquidation_alert_notifications.py")
TESTS = Path("tests/ai_platform_integration/test_liquidation_alert_notifications.py")


def patch_script() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    start = text.index("def _status_present(")
    end = text.index("\n\ndef _ensure_watchdog_issue(", start)
    replacement = '''def _final_status_present(
    client: GitHubClient, repository: str, sha: str
) -> bool:
    payload = client.combined_status(repository, sha)
    statuses = payload.get("statuses") if isinstance(payload, dict) else None
    return any(
        isinstance(item, dict)
        and item.get("context") == HEALTH_STATUS_CONTEXT
        and item.get("state") in {"success", "failure", "error"}
        for item in statuses or []
    )'''
    text = text[:start] + replacement + text[end:]

    old = '''    elif sha and status == "completed" and not _status_present(client, repository, sha):
'''
    new = '''    elif (
        status == "completed"
        and conclusion not in {"success", "cancelled"}
        and not (issue and issue.get("state") == "open")
    ):
        synthetic_code = "LIQUIDATIONS_HEALTH_RUN_FAILED_WITHOUT_ALERT"
        synthetic_description = (
            "Run health zakończył się błędem, ale nie pozostawił otwartego alertu."
        )
    elif sha and status == "completed" and not _final_status_present(
        client, repository, sha
    ):
'''
    if text.count(old) != 1:
        raise RuntimeError("unexpected final-status call shape")
    text = text.replace(old, new)

    old = '''    else:
        report = {}
        codes = ()
        healthy = bool(
            issue is not None and issue.get("state") == "closed" and issue_number is not None
        ) or (status == "completed" and conclusion == "success")
        description = "Wszystkie kontrole Liquidations Live zakończyły się sukcesem."
'''
    new = '''    else:
        report = {}
        codes = ()
        event_confirms_recovery = bool(
            issue is not None and issue.get("state") == "closed" and issue_number is not None
        )
        run_is_fresh_and_active = status in {
            "queued",
            "in_progress",
            "pending",
            "requested",
            "waiting",
        }
        healthy = (
            event_confirms_recovery
            or (status == "completed" and conclusion == "success")
            or run_is_fresh_and_active
        )
        description = (
            "Monitoring jest w toku; brak nowej potwierdzonej awarii."
            if run_is_fresh_and_active and not event_confirms_recovery
            else "Wszystkie kontrole Liquidations Live zakończyły się sukcesem."
        )
'''
    if text.count(old) != 1:
        raise RuntimeError("unexpected healthy-result block shape")
    SCRIPT.write_text(text.replace(old, new), encoding="utf-8")


def patch_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    old = "    decide_notification,\n"
    if text.count(old) != 1:
        raise RuntimeError("unexpected notifier import shape")
    text = text.replace(old, old + "    discover_incident,\n", 1)
    addition = '''


def test_fresh_in_progress_run_does_not_create_false_incident() -> None:
    client = FakeClient()
    client.issues[0]["state"] = "closed"
    client.list_workflow_runs = lambda repository, workflow: [
        {
            "status": "in_progress",
            "conclusion": None,
            "created_at": "2027-01-15T08:00:00Z",
            "head_sha": "b" * 40,
            "html_url": "https://github.com/blakinio/freqtrade/actions/runs/2",
        }
    ]

    current, _ = discover_incident(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        issue_number=None,
    )

    assert current.healthy is True
    assert current.codes == ()
    assert client.created_issues == []


def test_pending_commit_status_is_not_final() -> None:
    client = FakeClient()
    client.issues[0]["state"] = "closed"
    client.list_workflow_runs = lambda repository, workflow: [
        {
            "status": "completed",
            "conclusion": "success",
            "created_at": "2027-01-15T08:00:00Z",
            "head_sha": "c" * 40,
            "html_url": "https://github.com/blakinio/freqtrade/actions/runs/3",
        }
    ]
    client.combined_status = lambda repository, sha: {
        "statuses": [{"context": "liquidations-live-health", "state": "pending"}]
    }

    current, _ = discover_incident(
        client,
        "blakinio/freqtrade",
        now_ms=NOW_MS,
        issue_number=None,
    )

    assert current.healthy is False
    assert current.codes == ("LIQUIDATIONS_HEALTH_STATUS_MISSING",)
    assert client.created_issues[-1]["title"] == (
        "[liquidations-live] operational health alert"
    )
'''
    if "test_fresh_in_progress_run_does_not_create_false_incident" in text:
        raise RuntimeError("race regressions already present")
    TESTS.write_text(text + addition, encoding="utf-8")


if __name__ == "__main__":
    patch_script()
    patch_tests()
