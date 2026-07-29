from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "liquidations-live-operational-health.yml"
)


def test_health_runner_provisions_python_before_monitoring() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    setup_position = workflow.index("- name: Set up Python")
    health_position = workflow.index("- name: Check combined health and reconcile alert")

    assert setup_position < health_position
    assert (
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0"
        in workflow
    )
    assert 'python-version: "3.13"' in workflow


def test_runner_watchdog_keeps_commit_status_authoritative_without_issues() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert '--write-out "%{http_code}"' in workflow
    assert "issues_http_code=000" in workflow
    assert (
        "GitHub Issues API returned HTTP $issues_http_code; commit status remains authoritative."
        in workflow
    )
    assert (
        "Unable to create Liquidations health alert issue; commit status remains authoritative."
        in workflow
    )
    assert (
        "Unable to update Liquidations health alert issue; commit status remains authoritative."
        in workflow
    )
