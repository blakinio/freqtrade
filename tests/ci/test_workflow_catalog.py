from datetime import UTC, datetime
from pathlib import Path

from tools.ci.validate_workflows import validate_workflow_registry
from tools.ci.workflow_catalog import (
    _classification_for_current,
    _current_workflow_metadata,
    _safe_to_disable,
)


def test_current_workflow_classification() -> None:
    assert (
        _classification_for_current(".github/workflows/ci.yml", {"on": {"pull_request": {}}})
        == "canonical"
    )
    assert (
        _classification_for_current(
            ".github/workflows/component.yml", {"on": {"workflow_call": {}}}
        )
        == "reusable_component"
    )
    assert (
        _classification_for_current(
            ".github/workflows/nightly.yml", {"on": {"schedule": [{"cron": "0 0 * * *"}]}}
        )
        == "operational_schedule"
    )
    assert (
        _classification_for_current(".github/workflows/agent-bootstrap.yml", {"on": {"push": {}}})
        == "temporary_helper"
    )


def test_retirement_requires_absent_file_and_no_live_owner() -> None:
    assert _safe_to_disable(
        {
            "classification": "historical_deleted",
            "state_before": "active",
            "latest_run": {"status": "completed"},
            "open_pr": None,
        }
    )
    assert not _safe_to_disable(
        {
            "classification": "historical_deleted",
            "state_before": "active",
            "latest_run": {"status": "in_progress"},
            "open_pr": None,
        }
    )
    assert not _safe_to_disable(
        {
            "classification": "historical_deleted",
            "state_before": "active",
            "latest_run": {"lookup_error": "GitHub unavailable"},
            "open_pr": None,
        }
    )
    assert not _safe_to_disable(
        {
            "classification": "historical_deleted",
            "state_before": "active",
            "latest_run": {},
            "open_pr": None,
        }
    )
    assert not _safe_to_disable(
        {
            "classification": "bounded_diagnostic",
            "state_before": "active",
            "latest_run": {"status": "completed"},
            "open_pr": {"number": 1},
        }
    )


def test_temporary_registry_contract(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "agent-temporary.yml").write_text(
        "name: Temporary\non: workflow_dispatch\njobs:\n"
        "  test:\n    runs-on: ubuntu-latest\n    steps: []\n",
        encoding="utf-8",
    )
    _, registry_entries = _current_workflow_metadata(
        tmp_path,
        excluded_path=None,
        now=datetime(2026, 8, 5, tzinfo=UTC),
    )
    assert registry_entries[0]["lifecycle"] == "temporary"
    assert registry_entries[0]["expiry"] == "2026-08-12"
    assert registry_entries[0]["tracking_issue"] == 1252
    assert registry_entries[0]["retirement"]


def test_registry_rejects_unregistered_current_workflow(tmp_path: Path) -> None:
    registry = tmp_path / ".github" / "workflow-registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        '{"canonical_entry_points": [".github/workflows/ci.yml"], "workflows": []}\n',
        encoding="utf-8",
    )
    catalog = tmp_path / "docs" / "agents" / "evidence" / "FTAI-CI-001"
    catalog.mkdir(parents=True)
    (catalog / "workflow-catalog.json").write_text(
        '{"summary": {"unknown_active": 0, "retirement_failures": 1}}\n',
        encoding="utf-8",
    )
    failures = validate_workflow_registry(tmp_path, {".github/workflows/ci.yml"})
    assert any("missing from" in failure for failure in failures)
    assert any("retirement failures remain" in failure for failure in failures)
